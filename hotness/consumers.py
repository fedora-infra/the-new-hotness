# -*- coding: utf-8 -*-
# This file is part of the-new-hotness.
#
# the-new-hotness is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# the-new-hotness is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with the-new-hotness.  If not, see <http://www.gnu.org/licenses/>.
""" Fedmsg consumers that listen to `anitya <http://release-monitoring.org>`_.

Authors:    Ralph Bean <rbean@redhat.com>

"""

import logging
import subprocess

from requests.packages.urllib3.util import retry
from fedora_messaging.api import publish as fm_publish
from fedora_messaging.exceptions import PublishReturned, ConnectionException, Nack
from fedora_messaging.message import Message
from anitya_schema.project_messages import ProjectMapCreated, ProjectVersionUpdated

import requests
import fedmsg
import xmlrpc

from hotness import exceptions
from hotness.config import config as hotness_config
import hotness.anitya
import hotness.buildsys
import hotness.bz
import hotness.cache
import hotness.helpers


_log = logging.getLogger(__name__)


class BugzillaTicketFiler(object):
    """
    A fedora-messaging consumer that is the heart of the-new-hotness.

    This consumer subscribes to the following topics:

    * 'org.fedoraproject.prod.buildsys.task.state.change'
      handled by :method:`BugzillaTicketFiler.handle_buildsys_scratch`

    * 'org.release-monitoring.prod.anitya.project.version.update'
      handled by :method:`BugzillaTicketFiler.handle_anitya_version_update`

    * 'org.release-monitoring.prod.anitya.project.map.new'
      handled by :method:`BugzillaTicketFiler.handle_anitya_map_new`
    """

    def __init__(self):
        self.bugzilla = hotness.bz.Bugzilla(
            consumer=self, config=hotness_config["bugzilla"]
        )
        self.buildsys = hotness.buildsys.Koji(
            consumer=self, config=hotness_config["koji"]
        )

        self.pdc_url = hotness_config["pdc_url"]
        self.dist_git_url = hotness_config["dist_git_url"]

        self.anitya_url = hotness_config["anitya"]["url"]

        # Also, set up our global cache object.
        _log.info("Configuring cache.")
        with hotness.cache.cache_lock:
            if not hotness.cache.cache.is_configured:
                hotness.cache.cache.configure(**hotness_config["cache"])

        self.mdapi_url = hotness_config["mdapi_url"]
        _log.info("Using hotness.mdapi_url=%r" % self.mdapi_url)
        self.repoid = hotness_config["repoid"]
        _log.info("Using hotness.repoid=%r" % self.repoid)
        self.distro = hotness_config["distro"]
        _log.info("Using hotness.distro=%r" % self.distro)

        # Retrieve the requests configuration; by default requests time out
        # after 15 seconds and are retried up to 3 times.
        self.requests_session = requests.Session()
        self.timeout = (
            hotness_config["connect_timeout"],
            hotness_config["read_timeout"],
        )
        retries = hotness_config["requests_retries"]
        retry_conf = retry.Retry(
            total=retries, connect=retries, read=retries, backoff_factor=1
        )
        retry_conf.BACKOFF_MAX = 5
        self.requests_session.mount(
            "http://", requests.adapters.HTTPAdapter(max_retries=retry_conf)
        )
        self.requests_session.mount(
            "https://", requests.adapters.HTTPAdapter(max_retries=retry_conf)
        )
        _log.info(
            "Requests timeouts are {}s (connect) and {}s (read)"
            " with {} retries".format(self.timeout[0], self.timeout[1], retries)
        )

        # Build a little store where we'll keep track of what koji scratch
        # builds we have kicked off.  We'll look later for messages indicating
        # that they have completed.
        self.scratch_builds = {}

        _log.info("That new hotness ticket filer is all initialized")

    def publish(self, topic, msg):
        """
        Publish a fedora-messaging message to the specified topic.

        Args:
            topic (str): Topic to publish to
            msg (dict): Message to be send
        """
        _log.info("publishing topic %r" % topic)
        if hotness_config["legacy_messaging"]:
            fedmsg.publish(modname="hotness", topic=topic, msg=msg)
        else:
            try:
                fm_publish(Message(topic="hotness.{}".format(topic), body=msg))
            except PublishReturned as e:
                _log.warning(
                    "Fedora messaging broker rejected message %s:%s", msg.id, e
                )
            except ConnectionException as e:
                _log.warning("Error sending the message %s:%s", msg.id, e)

    def __call__(self, msg):
        """
        Called when a message is received from queue.

        Params:
            msg (fedora_messaging.message.Message) The message we received
                from the queue.
        """
        topic, body, msg_id = msg.topic, msg.body, msg.id
        _log.debug("Received %r" % msg_id)

        if topic.endswith("anitya.project.version.update"):
            message = ProjectVersionUpdated(topic=msg.topic, body=msg.body)
            self.handle_anitya_version_update(message)
        elif topic.endswith("anitya.project.map.new"):
            message = ProjectMapCreated(topic=msg.topic, body=msg.body)
            self.handle_anitya_map_new(message)
        elif topic.endswith("buildsys.task.state.change"):
            self.handle_buildsys_scratch(msg)
        else:
            _log.debug("Dropping %r %r" % (topic, body))
            pass

    def handle_anitya_version_update(self, msg):
        """
        Message handler for new versions found by Anitya.

        This handler deals with new versions found by Anitya. A new upstream
        release can map to several downstream packages, so each package in
        Rawhide (if any) are checked against the newly released version. If
        they are older than the new version, a bug is filed.

        Topic: ``org.release-monitoring.prod.anitya.project.version.update``

        Publishes to ``update.drop`` if there is no mapping to a package in
        Fedora.
        """
        _log.info("Handling anitya msg %r" % msg.id)
        if self.distro not in msg.distros:
            _log.info(
                "No %r mapping for %r. Dropping." % (self.distro, msg.project_name)
            )
            trigger = {"msg": msg.body, "topic": msg.topic}
            self.publish("update.drop", msg=dict(trigger=trigger, reason="anitya"))
            return

        # Sometimes, an upstream is mapped to multiple fedora packages
        # File a bug on each one...
        # https://github.com/fedora-infra/the-new-hotness/issues/33
        for package in msg.mappings:
            if package["distro"] == self.distro:
                pname = package["package_name"]

                upstream = msg.project_version
                self._handle_anitya_update(upstream, pname, msg)

    def handle_anitya_map_new(self, msg):
        """
        Message handler for projects newly mapped to Fedora in Anitya.

        This handler is used when a project is mapped to a Fedora package in
        Anitya. It triggers Anitya to perform a check for the latest upstream
        version, then compares that to the version in Rawhide. If Rawhide does
        not have the latest version, a bug is filed.

        Topic: 'org.release-monitoring.prod.anitya.project.map.new'
        """
        if msg.distro != self.distro:
            _log.info(
                "New mapping on %s, not for %s. Dropping." % (msg.distro, self.distro)
            )
            return

        project = msg.project_name
        package = msg.package_name
        upstream = msg.project_version

        _log.info(
            "Newly mapped %r to %r bears version %r" % (project, package, upstream)
        )

        if upstream:
            self._handle_anitya_update(upstream, package, msg)
        else:
            _log.info("Forcing an anitya upstream check.")
            anitya = hotness.anitya.Anitya(self.anitya_url)
            anitya.force_check(msg.project_id, msg.project_name)

    def _handle_anitya_update(self, upstream, package, msg):
        trigger = {"msg": msg.body, "topic": msg.topic}
        url = msg.project_homepage
        projectid = msg.project_id

        # Is it something that we're being asked not to act on?
        is_monitored = self.is_monitored(package)

        # Is it new to us?
        mdapi_url = "{0}/koji/srcpkg/{1}".format(self.mdapi_url, package)
        _log.debug("Getting pkg info from %r" % mdapi_url)
        r = self.requests_session.get(mdapi_url, timeout=self.timeout)
        if r.status_code != 200:
            # Unfortunately it's not in mdapi, we can't do much about it
            _log.warning("No koji version found for %r" % package)
            if is_monitored:
                self.publish("update.drop", msg=dict(trigger=trigger, reason="rawhide"))
            return
        js = r.json()
        version = js["version"]
        release = js["release"]

        _log.info(
            "Comparing upstream %s against repo %s-%s" % (upstream, version, release)
        )
        diff = hotness.helpers.cmp_upstream_repo(upstream, (version, release))

        # If so, then poke bugzilla and start a scratch build
        if diff == 1:
            _log.info("OK, %s is newer than %s-%s" % (upstream, version, release))

            if not is_monitored:
                _log.info("repo says not to monitor %r. Dropping." % package)
                self.publish("update.drop", msg=dict(trigger=trigger, reason="pkgdb"))
                return

            bz = None

            try:
                bz = self.bugzilla.handle(
                    projectid, package, upstream, version, release, url
                )
            # Raise Fedora messaging NACK exception when there is issue in bugzilla client
            except xmlrpc.client.Fault as e:
                _log.warn(
                    "Encountered an error during searching Bugzilla issue for '{0}': {1}".format(
                        package, e.faultString
                    )
                )
                raise Nack

            if not bz:
                _log.info("No RHBZ change detected (odd). Aborting.")
                self.publish(
                    "update.drop", msg=dict(trigger=trigger, reason="bugzilla")
                )
                return

            self.publish(
                "update.bug.file",
                msg=dict(trigger=trigger, bug=dict(bug_id=bz.bug_id), package=package),
            )
            _log.info("Filed Bugzilla #%i" % bz.bug_id)

            if is_monitored == "nobuild":
                _log.info("Monitor flag set to 'nobuild'. Skipping scratch build.")
                return

            try:
                _log.info("Starting scratch build for " + str(package))
                # Kick off a scratch build..
                task_id, patch_filename, description = self.buildsys.handle(
                    package, upstream, version, bz
                )

                # Map that koji task_id to the bz ticket we want to pursue.
                self.scratch_builds[task_id] = dict(
                    bz=bz, state=None, version=str(upstream)
                )
                # Attach the patch to the ticket
                self.bugzilla.attach_patch(patch_filename, description, bz)
            except exceptions.HotnessException as e:
                self.bugzilla.follow_up(str(e), bz)
            except subprocess.CalledProcessError as e:
                note = (
                    "Skipping the scratch build because an SRPM could not be built: "
                    "{cmd} returned {code}: {output}".format(
                        cmd=e.cmd, code=e.returncode, output=e.output
                    )
                )
                self.bugzilla.follow_up(note, bz)
            except Exception as e:
                _log.exception(e)
                note = (
                    "An unexpected error occurred while creating the scratch build "
                    "and has been automatically reported. Sorry!"
                )
                self.bugzilla.follow_up(note, bz)

    def handle_buildsys_scratch(self, msg):
        """
        Message handler for scratch builds in the build system.

        This handler is used to check up on scratch builds this consumer
        dispatched. When a message arrives it is checked to see if it is
        in a completed state and if it belongs to this consumer. A follow-up
        comment is left on bugs filed when builds are completed.

        Topic: 'org.fedoraproject.prod.buildsys.task.state.change'
        """
        msg_id, body = msg.id, msg.body
        instance = body["instance"]

        if instance != "primary":
            _log.debug("Ignoring secondary arch task...")
            return

        method = body["method"]

        if method != "build":
            _log.debug("Ignoring non-build task...")
            return

        task_id = body["info"]["id"]
        if task_id not in self.scratch_builds:
            _log.debug(
                "Ignoring [%s] as it's not one of our %d outstanding "
                "builds" % (str(task_id), len(self.scratch_builds))
            )
            return

        _log.info("Handling koji scratch msg %r" % msg_id)

        # see koji.TASK_STATES for all values
        done_states = {
            "CLOSED": "completed",
            "FAILED": "failed",
            "CANCELED": "canceled",
        }
        state = body["new"]
        if state not in done_states:
            return

        bugs = []

        url = hotness.buildsys.link(msg)
        subtitle = hotness.buildsys.subtitle(msg)
        text = "%s %s" % (subtitle, url)

        # Followup on bugs we filed
        self.bugzilla.follow_up(text, self.scratch_builds[task_id]["bz"])

        # Also follow up on Package Review requests, but only if the package is
        # not already in Fedora (it would be a waste of time to query bugzilla
        # if the review is already approved and scm has been processed).
        package_name = "-".join(body["srpm"].split("-")[:-2])
        if package_name and not self.in_dist_git(package_name):
            for bug in self.bugzilla.review_request_bugs(package_name):
                bugs.append((bug, text))

        if not bugs:
            _log.debug("No bugs to update for %r" % msg_id)
            return

    def is_monitored(self, package):
        """Returns True if a package is marked as 'monitored' in git.

        This is a thin wrapper around a requests.get call and could raise any
        exceptions raised by that function.
        """
        # First, check to see if the package is retired.
        # Even if the package says it is monitored.. if it is retired, then
        # let's not file any bugs or anything for it.
        if self.is_retired(package):
            _log.info("Package %s is retired.  Ignoring monitoring." % package)
            return False

        url = "{0}/_dg/anitya/rpms/{1}".format(self.dist_git_url, package)
        _log.debug("Checking %r to see if %s is monitored." % (url, package))
        r = self.requests_session.get(url, timeout=self.timeout)

        if not r.status_code == 200:
            _log.warning("URL %s returned code %s", r.url, r.status_code)
            return False

        try:
            data = r.json()
            string_value = data.get("monitoring", "no-monitoring")
            return_values = {
                "monitoring": "nobuild",
                "monitoring-with-scratch": True,
                "no-monitoring": False,
            }
            return return_values[string_value]
        except NameError:
            _log.exception("Problem interacting with the pagure repo.")
            return False

    def is_retired(self, package):
        """Returns True if a package is marked as 'retired' in PDC.

        This is a thin wrapper around a requests.get call and could raise any
        exceptions raised by that function.
        """
        url = "{0}/rest_api/v1/component-branches/".format(self.pdc_url)
        params = dict(name="rawhide", global_component=package, type="rpm", active=True)
        _log.debug("Checking %r to see if %s is retired, %r" % (url, package, params))
        r = self.requests_session.get(url, params=params, timeout=self.timeout)

        if not r.status_code == 200:
            _log.warning("URL %s returned code %s", r.url, r.status_code)
            return True

        # If there are zero active rawhide branches for this package, then it is
        # retired.
        return r.json()["count"] == 0

    @hotness.cache.cache.cache_on_arguments()
    def in_dist_git(self, package):
        """Returns True if a package is in the Fedora dist-git.

        This is a thin wrapper around a requests.head call and could raise any
        exceptions raised by that function.
        """

        url = "{0}/rpms/{1}".format(self.dist_git_url, package)
        _log.debug("Checking %r to see if %s is in dist-git" % (url, package))
        r = self.requests_session.head(url, timeout=self.timeout)

        if r.status_code == 404:
            return False
        if r.status_code != 200:
            _log.warning("URL %s returned code %s", r.url, r.status_code)
            return False
        return True
