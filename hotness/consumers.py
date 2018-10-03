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
import socket
import subprocess

from requests.packages.urllib3.util import retry
import fedmsg
import fedmsg.consumers
import fedmsg.meta
import requests
import yaml

from hotness import exceptions
import hotness.anitya
import hotness.buildsys
import hotness.bz
import hotness.cache
import hotness.helpers


_log = logging.getLogger(__name__)


class BugzillaTicketFiler(fedmsg.consumers.FedmsgConsumer):
    """
    A fedmsg consumer that is the heart of the-new-hotness.

    This consumer subscribes to the following topics:

    * 'org.fedoraproject.prod.buildsys.task.state.change'
      handled by :method:`BugzillaTicketFiler.handle_buildsys_scratch`

    * 'org.release-monitoring.prod.anitya.project.version.update'
      handled by :method:`BugzillaTicketFiler.handle_anitya_version_update`

    * 'org.release-monitoring.prod.anitya.project.map.new'
      handled by :method:`BugzillaTicketFiler.handle_anitya_map_new`
    """

    # We can do multiple topics like this as of moksha.hub-1.4.4
    # https://github.com/mokshaproject/moksha/pull/25
    topic = [
        # This is the real production topic
        "org.release-monitoring.prod.anitya.project.version.update",
        # Also listen for when projects are newly mapped to Fedora
        "org.release-monitoring.prod.anitya.project.map.new",
        # Anyways, we also listen for koji scratch builds to circle back:
        "org.fedoraproject.prod.buildsys.task.state.change",
    ]

    config_key = "hotness.bugzilla.enabled"

    def __init__(self, hub):

        # If we're in development mode, rewrite some of our topics so that
        # local playback with fedmsg-dg-replay works as expected.
        if hub.config["environment"] == "dev":
            # Keep the original set, but append a duplicate set for local work
            prefix, env = hub.config["topic_prefix"], hub.config["environment"]
            self.topic = self.topic + [
                ".".join([prefix, env] + topic.split(".")[3:]) for topic in self.topic
            ]

        super(BugzillaTicketFiler, self).__init__(hub)

        if not self._initialized:
            return

        # This is just convenient.
        self.config = self.hub.config

        # First, initialize fedmsg and bugzilla in this thread's context.
        hostname = socket.gethostname().split(".", 1)[0]
        if not getattr(getattr(fedmsg, "__local", None), "__context", None):
            fedmsg.init(name="hotness.%s" % hostname)
        fedmsg.meta.make_processors(**self.hub.config)

        self.bugzilla = hotness.bz.Bugzilla(
            consumer=self, config=self.config["hotness.bugzilla"]
        )
        self.buildsys = hotness.buildsys.Koji(
            consumer=self, config=self.config["hotness.koji"]
        )

        default = "https://pagure.io/releng/fedora-scm-requests"
        self.repo_url = self.config.get("hotness.repo_url", default)
        default = "https://pdc.fedoraproject.org"
        self.pdc_url = self.config.get("hotness.pdc_url", default)
        default = "https://src.fedoraproject.org"
        self.dist_git_url = self.config.get("hotness.dist_git_url", default)

        anitya_config = self.config.get("hotness.anitya", {})
        default = "https://release-monitoring.org"
        self.anitya_url = anitya_config.get("url", default)
        self.anitya_username = anitya_config.get("username", default)
        self.anitya_password = anitya_config.get("password", default)

        # Also, set up our global cache object.
        _log.info("Configuring cache.")
        with hotness.cache.cache_lock:
            if not hasattr(hotness.cache.cache, "backend"):
                hotness.cache.cache.configure(**self.config["hotness.cache"])

        self.mdapi_url = self.config.get("hotness.mdapi_url")
        _log.info("Using hotness.mdapi_url=%r" % self.mdapi_url)
        self.repoid = self.config.get("hotness.repoid", "rawhide")
        _log.info("Using hotness.repoid=%r" % self.repoid)
        self.distro = self.config.get("hotness.distro", "Fedora")
        _log.info("Using hotness.distro=%r" % self.distro)

        # Retrieve the requests configuration; by default requests time out
        # after 15 seconds and are retried up to 3 times.
        self.requests_session = requests.Session()
        self.timeout = (
            self.config.get("hotness.connect_timeout", 15),
            self.config.get("hotness.read_timeout", 15),
        )
        retries = self.config.get("hotness.requests_retries", 3)
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
        Publish a fedmsg message to the specified topic.
        """
        _log.info("publishing topic %r" % topic)
        fedmsg.publish(modname="hotness", topic=topic, msg=msg)

    def consume(self, msg):
        """
        Called when a message arrives on the fedmsg bus.
        """
        topic, msg = msg["topic"], msg["body"]
        _log.debug("Received %r" % msg.get("msg_id", None))

        if topic.endswith("anitya.project.version.update"):
            self.handle_anitya_version_update(msg)
        elif topic.endswith("anitya.project.map.new"):
            self.handle_anitya_map_new(msg)
        elif topic.endswith("buildsys.task.state.change"):
            self.handle_buildsys_scratch(msg)
        else:
            _log.debug("Dropping %r %r" % (topic, msg["msg_id"]))
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
        _log.info("Handling anitya msg %r" % msg.get("msg_id", None))
        # First, What is this thing called in our distro?
        # (we do this little inner.get(..) trick to handle legacy messages)
        inner = msg["msg"].get("message", msg["msg"])
        if self.distro not in [p["distro"] for p in inner["packages"]]:
            _log.info(
                "No %r mapping for %r.  Dropping."
                % (self.distro, msg["msg"]["project"]["name"])
            )
            self.publish("update.drop", msg=dict(trigger=msg, reason="anitya"))
            return

        # Sometimes, an upstream is mapped to multiple fedora packages
        # File a bug on each one...
        # https://github.com/fedora-infra/the-new-hotness/issues/33
        for package in inner["packages"]:
            if package["distro"] == self.distro:
                inner = msg["msg"].get("message", msg["msg"])
                pname = package["package_name"]

                upstream = inner["upstream_version"]
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
        message = msg["msg"]["message"]
        if message["distro"] != self.distro:
            _log.info(
                "New mapping on %s, not for %s.  Dropping."
                % (message["distro"], self.distro)
            )
            return

        project = message["project"]
        package = message["new"]
        upstream = msg["msg"]["project"]["version"]

        _log.info(
            "Newly mapped %r to %r bears version %r" % (project, package, upstream)
        )

        if upstream:
            self._handle_anitya_update(upstream, package, msg)
        else:
            _log.info("Forcing an anitya upstream check.")
            anitya = hotness.anitya.Anitya(self.anitya_url)
            anitya.force_check(msg["msg"]["project"])

    def _handle_anitya_update(self, upstream, package, msg):
        url = msg["msg"]["project"]["homepage"]
        projectid = msg["msg"]["project"]["id"]

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
                self.publish("update.drop", msg=dict(trigger=msg, reason="rawhide"))
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
                _log.info("repo says not to monitor %r.  Dropping." % package)
                self.publish("update.drop", msg=dict(trigger=msg, reason="pkgdb"))
                return

            bz = self.bugzilla.handle(
                projectid, package, upstream, version, release, url
            )
            if not bz:
                _log.info("No RHBZ change detected (odd).  Aborting.")
                self.publish("update.drop", msg=dict(trigger=msg, reason="bugzilla"))
                return

            self.publish(
                "update.bug.file", msg=dict(trigger=msg, bug=dict(bug_id=bz.bug_id))
            )
            _log.info("Filed Bugzilla #%i" % bz.bug_id)

            if is_monitored == "nobuild":
                _log.info("Monitor flag set to 'nobuild'.  " "Skipping scratch build.")
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
        instance = msg["msg"]["instance"]

        if instance != "primary":
            _log.debug("Ignoring secondary arch task...")
            return

        method = msg["msg"]["method"]

        if method != "build":
            _log.debug("Ignoring non-build task...")
            return

        task_id = msg["msg"]["info"]["id"]
        if task_id not in self.scratch_builds:
            _log.debug(
                "Ignoring [%s] as it's not one of our %d outstanding "
                "builds" % (str(task_id), len(self.scratch_builds))
            )
            return

        _log.info("Handling koji scratch msg %r" % msg.get("msg_id"))

        # see koji.TASK_STATES for all values
        done_states = {
            "CLOSED": "completed",
            "FAILED": "failed",
            "CANCELED": "canceled",
        }
        state = msg["msg"]["new"]
        if state not in done_states:
            return

        bugs = []

        url = fedmsg.meta.msg2link(msg, **self.hub.config)
        subtitle = fedmsg.meta.msg2subtitle(msg, **self.hub.config)
        text = "%s %s" % (subtitle, url)

        # Followup on bugs we filed
        self.bugzilla.follow_up(text, self.scratch_builds[task_id]["bz"])

        # Also follow up on Package Review requests, but only if the package is
        # not already in Fedora (it would be a waste of time to query bugzilla
        # if the review is already approved and scm has been processed).
        package_name = "-".join(msg["msg"]["srpm"].split("-")[:-2])
        if package_name and not self.in_dist_git(package_name):
            for bug in self.bugzilla.review_request_bugs(package_name):
                bugs.append((bug, text))

        if not bugs:
            _log.debug("No bugs to update for %r" % msg.get("msg_id"))
            return

    def is_monitored(self, package):
        """ Returns True if a package is marked as 'monitored' in git.

        This is a thin wrapper around a requests.get call and could raise any
        exceptions raised by that function.
        """
        # First, check to see if the package is retired.
        # Even if the package says it is monitored.. if it is retired, then
        # let's not file any bugs or anything for it.
        if self.is_retired(package):
            _log.info("Package %s is retired.  Ignoring monitoring." % package)
            return False

        url = "{0}/raw/master/f/rpms/{1}".format(self.repo_url, package)
        _log.debug("Checking %r to see if %s is monitored." % (url, package))
        r = self.requests_session.get(url, timeout=self.timeout)

        if not r.status_code == 200:
            _log.warning("URL %s returned code %s", r.url, r.status_code)
            return False

        try:
            data = yaml.safe_load(r.text)
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
        """ Returns True if a package is marked as 'retired' in PDC.

        This is a thin wrapper around a requests.get call and could raise any
        exceptions raised by that function.
        """
        url = "{0}/rest_api/v1/component-branches/".format(self.pdc_url)
        params = dict(name="master", global_component=package, type="rpm", active=True)
        _log.debug("Checking %r to see if %s is retired, %r" % (url, package, params))
        r = self.requests_session.get(url, params=params, timeout=self.timeout)

        if not r.status_code == 200:
            _log.warning("URL %s returned code %s", r.url, r.status_code)
            return True

        # If there are zero active master branches for this package, then it is
        # retired.
        return r.json()["count"] == 0

    @hotness.cache.cache.cache_on_arguments()
    def in_dist_git(self, package):
        """ Returns True if a package is in the Fedora dist-git.

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
