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
import traceback

from requests.packages.urllib3.util import retry
import fedmsg
import fedmsg.consumers
import requests

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

    * 'org.fedoraproject.prod.buildsys.build.state.change'
      handled by :method:`BugzillaTicketFiler.handle_buildsys_real`

    * 'org.fedoraproject.prod.pkgdb.package.new'
      handled by :method:`BugzillaTicketFiler.handle_new_package`

    * 'org.fedoraproject.prod.pkgdb.package.update'
      handled by :method:`BugzillaTicketFiler.handle_updated_package`

    * 'org.fedoraproject.prod.pkgdb.package.monitor.update'
      handled by :method:`BugzillaTicketFiler.handle_monitor_toggle`

    * 'org.release-monitoring.prod.anitya.project.version.update'
      handled by :method:`BugzillaTicketFiler.handle_anitya_version_update`

    * 'org.release-monitoring.prod.anitya.project.map.new'
      handled by :method:`BugzillaTicketFiler.handle_anitya_map_new`
    """

    # We can do multiple topics like this as of moksha.hub-1.4.4
    # https://github.com/mokshaproject/moksha/pull/25
    topic = [
        # This is the real production topic
        'org.release-monitoring.prod.anitya.project.version.update',

        # Also listen for when projects are newly mapped to Fedora
        'org.release-monitoring.prod.anitya.project.map.new',

        # Anyways, we also listen for koji scratch builds to circle back:
        'org.fedoraproject.prod.buildsys.task.state.change',

        # Furthermore, we look for official builds and also circle back
        # and comment about those (when they succeed).
        'org.fedoraproject.prod.buildsys.build.state.change',

        # We look for new packages being added to Fedora for the very
        # first time so that we can double-check that they have an entry in
        # release-monitoring.org.  If they don't, then we try to add them when
        # we can.
        'org.fedoraproject.prod.pkgdb.package.new',

        # We also look for when packages get their upstream_url changed in
        # Fedora and try to perform anitya modifications in response.
        'org.fedoraproject.prod.pkgdb.package.update',

        # Lastly, look for packages that get their monitoring flag switched on
        # and off.  We'll use that as another opportunity to map stuff in
        # anitya.
        'org.fedoraproject.prod.pkgdb.package.monitor.update',
    ]

    config_key = 'hotness.bugzilla.enabled'

    def __init__(self, hub):

        # If we're in development mode, rewrite some of our topics so that
        # local playback with fedmsg-dg-replay works as expected.
        if hub.config['environment'] == 'dev':
            # Keep the original set, but append a duplicate set for local work
            prefix, env = hub.config['topic_prefix'], hub.config['environment']
            self.topic = self.topic + [
                '.'.join([prefix, env] + topic.split('.')[3:])
                for topic in self.topic
            ]

        super(BugzillaTicketFiler, self).__init__(hub)

        if not self._initialized:
            return

        # This is just convenient.
        self.config = self.hub.config

        # First, initialize fedmsg and bugzilla in this thread's context.
        hostname = socket.gethostname().split('.', 1)[0]
        fedmsg.init(name='hotness.%s' % hostname)
        fedmsg.meta.make_processors(**self.hub.config)

        self.bugzilla = hotness.bz.Bugzilla(
            consumer=self, config=self.config['hotness.bugzilla'])
        self.buildsys = hotness.buildsys.Koji(
            consumer=self, config=self.config['hotness.koji'])

        default = 'https://admin.fedoraproject.org/pkgdb/api'
        self.pkgdb_url = self.config.get('hotness.pkgdb_url', default)

        anitya_config = self.config.get('hotness.anitya', {})
        default = 'https://release-monitoring.org'
        self.anitya_url = anitya_config.get('url', default)
        self.anitya_username = anitya_config.get('username', default)
        self.anitya_password = anitya_config.get('password', default)

        # Also, set up our global cache object.
        _log.info("Configuring cache.")
        with hotness.cache.cache_lock:
            if not hasattr(hotness.cache.cache, 'backend'):
                hotness.cache.cache.configure(**self.config['hotness.cache'])

        self.mdapi_url = self.config.get("hotness.mdapi_url")
        _log.info("Using hotness.mdapi_url=%r" % self.mdapi_url)
        self.repoid = self.config.get('hotness.repoid', 'rawhide')
        _log.info("Using hotness.repoid=%r" % self.repoid)
        self.distro = self.config.get('hotness.distro', 'Fedora')
        _log.info("Using hotness.distro=%r" % self.distro)

        # Retrieve the requests configuration; by default requests time out
        # after 15 seconds and are retried up to 3 times.
        self.requests_session = requests.Session()
        self.timeout = (
            self.config.get('hotness.connect_timeout', 15),
            self.config.get('hotness.read_timeout', 15),
        )
        retries = self.config.get('hotness.requests_retries', 3)
        retry_conf = retry.Retry(total=retries, connect=retries, read=retries, backoff_factor=1)
        retry_conf.BACKOFF_MAX = 5
        self.requests_session.mount(
            'http://', requests.adapters.HTTPAdapter(max_retries=retry_conf))
        self.requests_session.mount(
            'https://', requests.adapters.HTTPAdapter(max_retries=retry_conf))
        _log.info('Requests timeouts are {}s (connect) and {}s (read)'
                  ' with {} retries'.format(self.timeout[0], self.timeout[1], retries))

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
        fedmsg.publish(modname='hotness', topic=topic, msg=msg)

    def consume(self, msg):
        """
        Called when a message arrives on the fedmsg bus.
        """
        topic, msg = msg['topic'], msg['body']
        _log.debug("Received %r" % msg.get('msg_id', None))

        if topic.endswith('anitya.project.version.update'):
            self.handle_anitya_version_update(msg)
        elif topic.endswith('anitya.project.map.new'):
            self.handle_anitya_map_new(msg)
        elif topic.endswith('buildsys.task.state.change'):
            self.handle_buildsys_scratch(msg)
        elif topic.endswith('buildsys.build.state.change'):
            self.handle_buildsys_real(msg)
        elif topic.endswith('pkgdb.package.new'):
            listing = msg['msg']['package_listing']
            if listing['collection']['branchname'] != 'master':
                _log.debug("Ignoring non-rawhide new package...")
                return
            self.handle_new_package(msg, listing['package'])
        elif topic.endswith('pkgdb.package.update'):
            self.handle_updated_package(msg)
        elif topic.endswith('pkgdb.package.monitor.update'):
            self.handle_monitor_toggle(msg)
        else:
            _log.debug("Dropping %r %r" % (topic, msg['msg_id']))
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
        _log.info("Handling anitya msg %r" % msg.get('msg_id', None))
        # First, What is this thing called in our distro?
        # (we do this little inner.get(..) trick to handle legacy messages)
        inner = msg['msg'].get('message', msg['msg'])
        if self.distro not in [p['distro'] for p in inner['packages']]:
            _log.info("No %r mapping for %r.  Dropping." % (
                self.distro, msg['msg']['project']['name']))
            self.publish("update.drop", msg=dict(trigger=msg, reason="anitya"))
            return

        # Sometimes, an upstream is mapped to multiple fedora packages
        # File a bug on each one...
        # https://github.com/fedora-infra/the-new-hotness/issues/33
        for package in inner['packages']:
            if package['distro'] == self.distro:
                inner = msg['msg'].get('message', msg['msg'])
                pname = package['package_name']

                upstream = inner['upstream_version']
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
        message = msg['msg']['message']
        if message['distro'] != self.distro:
            _log.info("New mapping on %s, not for %s.  Dropping." % (
                message['distro'], self.distro))
            return

        project = message['project']
        package = message['new']
        upstream = msg['msg']['project']['version']

        _log.info("Newly mapped %r to %r bears version %r" % (
            project, package, upstream))

        if upstream:
            self._handle_anitya_update(upstream, package, msg)
        else:
            _log.info("Forcing an anitya upstream check.")
            anitya = hotness.anitya.Anitya(self.anitya_url)
            anitya.force_check(msg['msg']['project'])

    def _handle_anitya_update(self, upstream, package, msg):
        url = msg['msg']['project']['homepage']
        projectid = msg['msg']['project']['id']

        # Is it something that we're being asked not to act on?
        is_monitored = self.is_monitored(package)

        # Is it new to us?
        mdapi_url = '{0}/koji/srcpkg/{1}'.format(self.mdapi_url, package)
        _log.debug("Getting pkg info from %r" % mdapi_url)
        r = self.requests_session.get(mdapi_url, timeout=self.timeout)
        if r.status_code != 200:
            # Unfortunately it's not in mdapi, we can't do much about it
            _log.warning("No koji version found for %r" % package)
            if is_monitored:
                self.publish("update.drop", msg=dict(
                    trigger=msg, reason="rawhide"))
            return
        js = r.json()
        version = js["version"]
        release = js["release"]

        _log.info("Comparing upstream %s against repo %s-%s" % (
            upstream, version, release))
        diff = hotness.helpers.cmp_upstream_repo(upstream, (version, release))

        # If so, then poke bugzilla and start a scratch build
        if diff == 1:
            _log.info("OK, %s is newer than %s-%s" % (
                upstream, version, release))

            if not is_monitored:
                _log.info("Pkgdb says not to monitor %r.  Dropping." % package)
                self.publish("update.drop", msg=dict(trigger=msg, reason="pkgdb"))
                return

            bz = self.bugzilla.handle(
                projectid, package, upstream, version, release, url)
            if not bz:
                _log.info("No RHBZ change detected (odd).  Aborting.")
                self.publish("update.drop", msg=dict(
                    trigger=msg, reason="bugzilla"))
                return

            self.publish("update.bug.file", msg=dict(
                trigger=msg, bug=dict(bug_id=bz.bug_id)))
            _log.info("Filed Bugzilla #%i" % bz.bug_id)

            if is_monitored == 'nobuild':
                _log.info("Monitor flag set to 'nobuild'.  "
                          "Skipping scratch build.")
                return

            try:
                _log.info('Starting scratch build for ' + str(package))
                # Kick off a scratch build..
                task_id, patch_filename, description = self.buildsys.handle(
                    package, upstream, version, bz)

                # Map that koji task_id to the bz ticket we want to pursue.
                self.scratch_builds[task_id] = dict(
                    bz=bz, state=None, version=str(upstream))
                # Attach the patch to the ticket
                self.bugzilla.attach_patch(patch_filename, description, bz)
            except Exception as e:
                _log.exception(e)
                note = ("An unexpected error occured creating the scratch build: "
                        "please report this issue to the-new-hotness issue tracker "
                        "at https://github.com/fedora-infra/the-new-hotness/issues")
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
        instance = msg['msg']['instance']

        if instance != 'primary':
            _log.debug("Ignoring secondary arch task...")
            return

        method = msg['msg']['method']

        if method != 'build':
            _log.debug("Ignoring non-build task...")
            return

        task_id = msg['msg']['info']['id']
        if task_id not in self.scratch_builds:
            _log.debug("Ignoring [%s] as it's not one of our %d outstanding "
                       "builds" % (str(task_id), len(self.scratch_builds)))
            return

        _log.info("Handling koji scratch msg %r" % msg.get('msg_id'))

        # see koji.TASK_STATES for all values
        done_states = {
            'CLOSED': 'completed',
            'FAILED': 'failed',
            'CANCELED': 'canceled',
        }
        state = msg['msg']['new']
        if state not in done_states:
            return

        bugs = []

        url = fedmsg.meta.msg2link(msg, **self.hub.config)
        subtitle = fedmsg.meta.msg2subtitle(msg, **self.hub.config)
        text = "%s %s" % (subtitle, url)

        # Followup on bugs we filed
        self.bugzilla.follow_up(text, self.scratch_builds[task_id]['bz'])

        # Also follow up on Package Review requests, but only if the package is
        # not already in Fedora (it would be a waste of time to query bugzilla
        # if the review is already approved and scm has been processed).
        package_name = '-'.join(msg['msg']['srpm'].split('-')[:-2])
        if package_name and not self.in_pkgdb(package_name):
            for bug in self.bugzilla.review_request_bugs(package_name):
                bugs.append((bug, text))

        if not bugs:
            _log.debug("No bugs to update for %r" % msg.get('msg_id'))
            return

    def handle_buildsys_real(self, msg):
        """
        Message handlers for real builds (not scratch) in the build system.

        This handles messages for the real builds. It only examines builds
        for Rawhide. It comments on bugs filed by this consumer previously.

        Topic: 'org.fedoraproject.prod.buildsys.build.state.change'
        """
        idx = msg['msg']['build_id']
        state = msg['msg']['new']
        release = msg['msg']['release'].split('.')[-1]
        instance = msg['msg']['instance']

        if instance != 'primary':
            _log.debug("Ignoring secondary arch build...")
            return

        rawhide = self.get_dist_tag()
        if not release.endswith(rawhide):
            _log.debug("Koji build=%r, %r is not rawhide(%r). Drop it." % (
                idx, release, rawhide))
            return

        if state != 1:
            _log.debug("Koji build_id=%r is not complete.  Drop it." % idx)
            return

        package = msg['msg']['name']
        version = msg['msg']['version']
        release = msg['msg']['release']

        is_monitored = self.is_monitored(package)
        if not is_monitored:
            _log.debug('%r not monitored, dropping koji build' % package)
            return

        if is_monitored == 'nobuild':
            _log.debug('%r set to "nobuild", dropping build' % package)
            return

        _log.info("Handling koji build msg %r" % msg.get('msg_id', None))

        # Search for all FTBFS bugs and any upstream bugs we filed earlier.
        bugs = list(self.bugzilla.ftbfs_bugs(name=package)) + [
            self.bugzilla.exact_bug(name=package, upstream=version),
        ]
        # Filter out None values
        bugs = [bug for bug in bugs if bug]

        if not bugs:
            _log.info("No bugs found for %s-%s.%s." % (
                package, version, release))
            return

        url = fedmsg.meta.msg2link(msg, **self.hub.config)
        subtitle = fedmsg.meta.msg2subtitle(msg, **self.hub.config)
        text = "%s %s" % (subtitle, url)

        for bug in bugs:
            # Don't followup on bugs that we have just recently followed up on.
            # https://github.com/fedora-infra/the-new-hotness/issues/17
            latest = bug.comments[-1]    # Check just the latest comment
            target = subtitle            # Our comments have this in it
            me = self.bugzilla.username  # Our comments are, obviously, by us.
            if latest['creator'] == me and target in latest['text']:
                _log.info("%s has a recent comment from me." % bug.weburl)
                continue

            # Don't followup on bugs that are already closed... otherwise we
            # would followup for ALL ETERNITY.
            if bug.status in self.bugzilla.bug_status_closed:
                _log.info("Bug %s is %s.  Dropping." % (
                    bug.weburl, bug.status))
                continue

            self.bugzilla.follow_up(text, bug)
            self.publish("update.bug.followup", msg=dict(
                trigger=msg, bug=dict(bug_id=bug.bug_id)))

    def handle_new_package(self, msg, package):
        """
        Message handler for newly added packages in pkgdb.

        When a new package is added to pkgdb, this ensures that there is a
        mapping in release-monitoring.org for that package. If it is not
        present, this adds it, if possible.

        Topic: 'org.fedoraproject.prod.pkgdb.package.new',

        Publish a message to ``project.map`` with the results of the attempt
        map the package to a project.
        """
        name = package['name']
        homepage = package['upstream_url']

        if not homepage:
            # If there is not homepage set at the outset in pkgdb, there's
            # nothing smart we can do with respect to anitya, so.. wait.
            # pkgdb has a cron script that runs weekly that updates the
            # upstream url there, so when that happens, we'll be triggered
            # and can try again.
            _log.warn("New package %r has no homepage.  Dropping." % name)
            return

        _log.info("Considering new package %r with %r" % (name, homepage))

        anitya = hotness.anitya.Anitya(self.anitya_url)
        results = anitya.search_by_homepage(name, homepage)

        projects = results['projects']
        total = results['total']
        if total > 1:
            _log.warning("Fail. %i matching projects on anitya." % total)
            self.publish("project.map", msg=dict(
                trigger=msg, total=total, success=False))
        elif total == 1:
            _log.info("Found one match on Anitya.")
            project = projects[0]
            anitya.login(self.anitya_username, self.anitya_password)

            reason = None
            try:
                anitya.map_new_package(name, project)
            except hotness.anitya.AnityaException as e:
                reason = str(e)
                _log.warn("Failed to map: %r" % reason)

            self.publish("project.map", msg=dict(
                trigger=msg,
                project=project,
                success=not bool(reason),
                reason=reason))
        else:
            _log.info("Saw 0 matching projects on anitya.  Adding.")
            anitya.login(self.anitya_username, self.anitya_password)

            reason = None
            try:
                anitya.add_new_project(name, homepage)
            except hotness.anitya.AnityaException as e:
                reason = str(e)
                _log.warn("Failed to create: %r" % reason)

            self.publish("project.map", msg=dict(
                trigger=msg,
                success=not bool(reason),
                reason=reason))

    def handle_updated_package(self, msg):
        """
        Message handler for updates to packages in pkgdb.

        When a package is updated in pkgdb, this ensures that if the
        upstream_url changes in pkgdb, the changes are pushed to Anitya.
        This can result in either an update to the Anitya project entry,
        or an entirely new entry if the package did not previously exist
        in Anitya.

        Topic: 'org.fedoraproject.prod.pkgdb.package.update',

        Publish a message to ``project.map`` with the results of the attempt
        map the package to a project if the project is not already on Anitya.
        """
        _log.info("Handling pkgdb update msg %r" % msg.get('msg_id'))

        fields = msg['msg']['fields']
        if 'upstream_url' not in fields:
            _log.info("Ignoring package edit with no url change.")
            return

        package = msg['msg']['package']
        name = package['name']
        homepage = package['upstream_url']

        _log.info("Trying url change on %s: %s" % (name, homepage))

        # There are two possible scenarios here.
        # 1) the package already *is mapped* in anitya, in which case we can
        #    update the old url there
        # 2) the package is not mapped there, in which case we handle this like
        #    a new package (and try to create it and map it)

        anitya = hotness.anitya.Anitya(self.anitya_url)
        project = anitya.get_project_by_package(name)

        if project:
            _log.info("Found project with name %s" % project['name'])
            anitya.login(self.anitya_username, self.anitya_password)
            if project['homepage'] == homepage:
                _log.info("No need to update anitya for %s.  Homepages"
                          " are already in sync." % project['name'])
                return

            _log.info("Updating anitya url on %s" % project['name'])
            anitya.update_url(project, homepage)
            anitya.force_check(project)
        else:
            # Just pretend like it's a new package, since its not in anitya.
            self.handle_new_package(msg, package)

    def handle_monitor_toggle(self, msg):
        """
        Message handler for packages whose monitoring is adjusted in pkgdb.

        If a package has its monitoring turned off, this does nothing. If it is
        turned on, this ensures the package exists in Anitya and forces Anitya
        to check for the latest version.

        Topic: 'org.fedoraproject.prod.pkgdb.package.monitor.update'
        """
        status = msg['msg']['status']
        name = msg['msg']['package']['name']
        homepage = msg['msg']['package']['upstream_url']

        _log.info("Considering monitored %r with %r" % (name, homepage))

        if not status:
            _log.info(".. but it was turned off.  Dropping.")
            return

        anitya = hotness.anitya.Anitya(self.anitya_url)
        results = anitya.search_by_homepage(name, homepage)
        total = results['total']

        if total > 1:
            _log.info("%i projects with %r %r already exist in anitya." % (
                total, name, homepage))
            return
        elif total == 1:
            # The project might exist in anitya, but it might not be mapped to
            # a Fedora package yet, so map it if necessary.
            project = results['projects'][0]

            anitya.login(self.anitya_username, self.anitya_password)

            reason = None
            try:
                anitya.map_new_package(name, project)
            except hotness.anitya.AnityaException as e:
                reason = str(e)
                _log.warn("Failed to map: %r" % reason)

            self.publish("project.map", msg=dict(
                trigger=msg,
                project=project,
                success=not bool(reason),
                reason=reason))

            # After mapping, force a check for new tarballs
            anitya.force_check(project)
        else:
            # OTHERWISE, there is *nothing* on anitya about it, so add one.
            _log.info("Saw 0 matching projects on anitya.  Adding.")
            anitya.login(self.anitya_username, self.anitya_password)

            reason = None
            try:
                anitya.add_new_project(name, homepage)
            except hotness.anitya.AnityaException as e:
                reason = str(e)
                _log.warn("Failed to create: %r" % reason)

            self.publish("project.map", msg=dict(
                trigger=msg,
                success=not bool(reason),
                reason=reason))

    def is_monitored(self, package):
        """ Returns True if a package is marked as 'monitored' in pkgdb2. """

        url = '{0}/package/{1}'.format(self.pkgdb_url, package)
        _log.debug("Checking %r" % url)
        r = self.requests_session.get(url, timeout=self.timeout)

        if not r.status_code == 200:
            _log.warning('URL %s returned code %s', r.url, r.status_code)
            return False

        try:
            data = r.json()
            package = data['packages'][0]

            # Even if the package says it is monitored.. if it is retired, then
            # let's not file any bugs or anything for it.
            if package['package']['status'] == "Retired":
                return False

            # Otherwise, if it is not retired, then return the monitor flag.
            return package['package'].get('monitor', True)
        except:
            _log.exception("Problem interacting with pkgdb.")
            return False

    @hotness.cache.cache.cache_on_arguments()
    def in_pkgdb(self, package):
        """ Returns True if a package is in the Fedora pkgdb. """

        url = '{0}/package/{1}'.format(self.pkgdb_url, package)
        _log.debug("Checking %r" % url)
        r = self.requests_session.get(url, timeout=self.timeout)

        if r.status_code == 404:
            return False
        if r.status_code != 200:
            _log.warning('URL %s returned code %s', r.url, r.status_code)
            return False
        return True

    @hotness.cache.cache.cache_on_arguments()
    def get_dist_tag(self):
        url = '{0}/collections/master/'.format(self.pkgdb_url)
        _log.debug("Getting dist tag from %r" % url)
        r = self.requests_session.get(url, timeout=self.timeout)

        if not r.status_code == 200:
            raise IOError('URL %s returned code %s', r.url, r.status_code)

        data = r.json()
        collection = data['collections'][0]
        tag = collection['dist_tag'][1:]
        _log.debug("Got rawhide suffix %r" % tag)
        return tag
