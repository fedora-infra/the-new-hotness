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

import socket
import traceback

import fedmsg
import fedmsg.consumers
import requests

import hotness.anitya
import hotness.buildsys
import hotness.bz
import hotness.cache
import hotness.helpers
import hotness.repository
import os
import shutil
import tempfile
import time
import six

import koji


class BugzillaTicketFiler(fedmsg.consumers.FedmsgConsumer):


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
        self.log.info("Configuring cache.")
        with hotness.cache.cache_lock:
            if not hasattr(hotness.cache.cache, 'backend'):
                hotness.cache.cache.configure(**self.config['hotness.cache'])

        self.package_manager = self.config.get('hotness.pkg_manager', 'yum')
        self.log.info("Using hotness.pkg_manager=%r" % self.package_manager)
        self.yumconfig = self.config.get('hotness.yumconfig')
        self.log.info("Using hotness.yumconfig=%r" % self.yumconfig)
        self.repoid = self.config.get('hotness.repoid', 'rawhide')
        self.log.info("Using hotness.repoid=%r" % self.repoid)
        self.distro = self.config.get('hotness.distro', 'Fedora')
        self.log.info("Using hotness.distro=%r" % self.distro)

        # Build a little store where we'll keep track of what koji scratch
        # builds we have kicked off.  We'll look later for messages indicating
        # that they have completed.
        self.old_triggered_task_ids = {}
        self.new_triggered_task_ids = {}

        self.log.info("That new hotness ticket filer is all initialized")

    def publish(self, topic, msg):
        self.log.info("publishing topic %r" % topic)
        fedmsg.publish(modname='hotness', topic=topic, msg=msg)

    def consume(self, msg):
        topic, msg = msg['topic'], msg['body']
        self.log.debug("Received %r" % msg.get('msg_id', None))

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
                self.log.debug("Ignoring non-rawhide new package...")
                return
            self.handle_new_package(msg, listing['package'])
        elif topic.endswith('pkgdb.package.update'):
            self.handle_updated_package(msg)
        elif topic.endswith('pkgdb.package.monitor.update'):
            self.handle_monitor_toggle(msg)
        else:
            self.log.debug("Dropping %r %r" % (topic, msg['msg_id']))
            pass

    def handle_anitya_version_update(self, msg):
        self.log.info("Handling anitya msg %r" % msg.get('msg_id', None))
        # First, What is this thing called in our distro?
        # (we do this little inner.get(..) trick to handle legacy messages)
        inner = msg['msg'].get('message', msg['msg'])
        if not self.distro in [p['distro'] for p in inner['packages']]:
            self.log.info("No %r mapping for %r.  Dropping." % (
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
        message = msg['msg']['message']
        if message['distro'] != self.distro:
            self.log.info("New mapping on %s, not for %s.  Dropping." % (
                message['distro'], self.distro))
            return

        project = message['project']
        package = message['new']
        upstream = msg['msg']['project']['version']

        self.log.info("Newly mapped %r to %r bears version %r" % (
            project, package, upstream))

        if upstream:
            self._handle_anitya_update(upstream, package, msg)
        else:
            self.log.info("Forcing an anitya upstream check.")
            anitya = hotness.anitya.Anitya(self.anitya_url)
            anitya.force_check(msg['msg']['project'])

    def _handle_anitya_update(self, upstream, package, msg):
        url = msg['msg']['project']['homepage']
        projectid = msg['msg']['project']['id']

        # Is it something that we're being asked not to act on?
        is_monitored = self.is_monitored(package)

        # Is it new to us?
        fname = self.yumconfig
        try:
            version, release = hotness.repository.get_version(
                package, fname, self.package_manager)
        except KeyError:
            # At this point, we have tried very hard to find the rawhide
            # version of the package.  If we didn't find it, that means there
            # likely hasn't yet been a rawhide build of it.. and there's
            # nothing reasonable we can do.  Notify the world of our failure
            # and go back to the event loop.
            self.log.warn("No rawhide version found for %r" % package)
            if is_monitored:
                self.publish("update.drop", msg=dict(
                    trigger=msg, reason="rawhide"))
            return

        self.log.info("Comparing upstream %s against repo %s-%s" % (
            upstream, version, release))
        diff = hotness.helpers.cmp_upstream_repo(upstream, (version, release))

        # If so, then poke bugzilla and start a scratch build
        if diff == 1:
            self.log.info("OK, %s is newer than %s-%s" % (
                upstream, version, release))

            if not is_monitored:
                self.log.info("Pkgdb says not to monitor %r.  Dropping." % package)
                self.publish("update.drop", msg=dict(trigger=msg, reason="pkgdb"))
                return

            bz = self.bugzilla.handle(
                projectid, package, upstream, version, release, url)
            if not bz:
                self.log.info("No RHBZ change detected (odd).  Aborting.")
                self.publish("update.drop", msg=dict(
                    trigger=msg, reason="bugzilla"))
                return

            self.publish("update.bug.file", msg=dict(
                trigger=msg, bug=dict(bug_id=bz.bug_id)))

            if is_monitored == 'nobuild':
                self.log.info("Monitor flag set to 'nobuild'.  "
                              "Skipping scratch build.")
                return

            cwd = os.getcwd()
            result_rh = 0
            rh_stuff = {}
            tmp = tempfile.mkdtemp(prefix='thn-rh', dir='/var/tmp')
            try:
                result_rh, rh_stuff = self.buildsys.rebase_helper(package, upstream, tmp, bz)
                self.log.info(rh_stuff)
                if int(result_rh) == 0:
                    if 'build_logs' in rh_stuff and 'build_ref' in rh_stuff.get('build_logs'):
                        build_ref = rh_stuff['build_logs']['build_ref']
                        if build_ref:
                            for ver in ['old', 'new']:
                                dict_version = build_ref[ver]
                                task_id = dict_version['koji_task_id']
                                if 'old' == ver:
                                    self.old_triggered_task_ids[task_id] = [bz, None, str(version), str(package)]
                                else:
                                    self.new_triggered_task_ids[task_id] = [bz, None, str(upstream), str(package)]
                else:
                    note = 'Patching or scratch build for %s-%s failed.\n' % (package, version)
                    self.bugzilla.follow_up(note, bz)
                    if 'logs' in rh_stuff['build_logs']:
                        for log in rh_stuff['build_logs']['logs']:
                            note = 'Build log %s.' % log
                            self.bugzilla.attach_patch(log, note, bz)
                    # Attach rebase-helper logs for another analysis
                    if 'logs' in rh_stuff:
                        for log in rh_stuff['logs']:
                            rebase_helper_url = 'https://github.com/phracek/rebase-helper/issues'
                            note_logs = 'Rebase-helper %s log file.\n' \
                                        'See for details and report the eventual error to rebase-helper %s.' % \
                                        (os.path.basename(log), rebase_helper_url)
                            self.bugzilla.attach_patch(log, note_logs, bz)

                if 'patches' in rh_stuff:
                    for patch in rh_stuff['patches']:
                        self.bugzilla.follow_up(patch, bz)
                os.chdir(cwd)
                if os.path.exists(tmp):
                    shutil.rmtree(tmp)

            except Exception as ex:
                self.log.info('Customer.py: Rebase helper failed with an unknown reason. %s' % str(ex))
                self.log.info(rh_stuff)
                self.bugzilla.follow_up('Rebase helper failed.\n'
                                        'See logs and attachments in this bugzilla %s' % ex.message, bz)
                if 'patches' in rh_stuff:
                    for patch in rh_stuff['patches']:
                        self.bugzilla.follow_up(patch, bz)
                if 'logs' in rh_stuff:
                    for log in rh_stuff['logs']:
                        rh_logs = "Log %s provided by rebase-helper." % log
                        self.bugzilla.attach_patch(log, rh_logs, bz)

                os.chdir(cwd)

                if os.path.exists(tmp):
                    shutil.rmtree(tmp)

                self.log.info("Now with #%i, time to do koji stuff" % bz.bug_id)
                try:
                    # Kick off a scratch build..
                    task_id, patch_filename, description = self.buildsys.handle(
                        package, upstream, version, bz)

                    # Map that koji task_id to the bz ticket we want to pursue.
                    self.new_triggered_task_ids[task_id] = [bz, None, str(upstream), str(package)]
                    # Attach the patch to the ticket
                    self.bugzilla.attach_patch(patch_filename, description, bz)
                except Exception as e:
                    heading = "Failed to kick off scratch build."
                    note = heading + "\n\n" + str(e)
                    self.log.warning(heading)
                    self.log.warning(traceback.format_exc())
                    self.bugzilla.follow_up(note, bz)

    def handle_buildsys_scratch(self, msg):
        instance = msg['msg']['instance']

        if instance != 'primary':
            self.log.debug("Ignoring secondary arch task...")
            return

        method = msg['msg']['method']

        if method != 'build':
            self.log.debug("Ignoring non-build task...")
            return

        task_id = msg['msg']['info']['id']

        self.log.info("Handling koji scratch msg %r" % msg.get('msg_id'))

        # see koji.TASK_STATES for all values
        done_states = {
            'CLOSED': 'completed',
            'FAILED': 'failed',
            'CANCELLED': 'canceled',
        }
        state = msg['msg']['new']
        if state not in done_states:
            return

        bugs = []

        url = fedmsg.meta.msg2link(msg, **self.hub.config)
        subtitle = fedmsg.meta.msg2subtitle(msg, **self.hub.config)
        text1 = "Scratch build %s %s" % (done_states.get(state, state), url)
        text2 = "%s %s" % (subtitle, url)

        # Followup on bugs we filed
        self._update_tasks(task_id, state)
        # Also follow up on Package Review requests, but only if the package is
        # not already in Fedora (it would be a waste of time to query bugzilla
        # if the review is already approved and scm has been processed).
        package_name = '-'.join(msg['msg']['srpm'].split('-')[:-2])
        if package_name and not self.in_pkgdb(package_name):
            for bug in self.bugzilla.review_request_bugs(package_name):
                bugs.append((bug, text2))

        if not bugs:
            self.log.debug("No bugs to update for %r" % msg.get('msg_id'))
            return

        #for bug in bugs:
        #    # Don't followup on bugs that we have just recently followed up on.
        #    # https://github.com/fedora-infra/the-new-hotness/issues/17
        #    latest = bug.comments[-1]    # Check just the latest comment
        #    target = 'completed http'    # Our comments have this in it
        #    me = self.bugzilla.username  # Our comments are, obviously, by us.
        #    if latest['creator'] == me and target in latest['text']:
        #        self.log.info("%s has a recent comment from me." % bug.weburl)
        #        continue
        #
        #    self.bugzilla.follow_up(text1, bug)
        #    self.publish("update.bug.followup", msg=dict(
        #        trigger=msg, bug=dict(bug_id=bug.bug_id)))

    def handle_buildsys_real(self, msg):
        idx = msg['msg']['build_id']
        state = msg['msg']['new']
        release = msg['msg']['release'].split('.')[-1]
        instance = msg['msg']['instance']

        if instance != 'primary':
            self.log.debug("Ignoring secondary arch build...")
            return

        rawhide = self.get_dist_tag()
        if not release.endswith(rawhide):
            self.log.debug("Koji build=%r, %r is not rawhide(%r). Drop it." % (
                idx, release, rawhide))
            return

        if state != 1:
            self.log.debug("Koji build_id=%r is not complete.  Drop it." % idx)
            return

        package = msg['msg']['name']
        version = msg['msg']['version']
        release = msg['msg']['release']

        is_monitored = self.is_monitored(package)
        if not is_monitored:
            self.log.debug('%r not monitored, dropping koji build' % package)
            return

        if is_monitored == 'nobuild':
            self.log.debug('%r set to "nobuild", dropping build' % package)
            return

        self.log.info("Handling koji build msg %r" % msg.get('msg_id', None))

        # Search for all FTBFS bugs and any upstream bugs we filed earlier.
        bugs = list(self.bugzilla.ftbfs_bugs(name=package)) + [
            self.bugzilla.exact_bug(name=package, upstream=version),
        ]
        # Filter out None values
        bugs = [bug for bug in bugs if bug]

        if not bugs:
            self.log.info("No bugs found for %s-%s.%s." % (
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
                self.log.info("%s has a recent comment from me." % bug.weburl)
                continue

            # Don't followup on bugs that are already closed... otherwise we
            # would followup for ALL ETERNITY.
            if bug.status in self.bugzilla.bug_status_closed:
                self.log.info("Bug %s is %s.  Dropping." % (
                    bug.weburl, bug.status))
                continue

            self.bugzilla.follow_up(text, bug)
            self.publish("update.bug.followup", msg=dict(
                trigger=msg, bug=dict(bug_id=bug.bug_id)))

    def handle_new_package(self, msg, package):
        name = package['name']
        homepage = package['upstream_url']

        if not homepage:
            # If there is not homepage set at the outset in pkgdb, there's
            # nothing smart we can do with respect to anitya, so.. wait.
            # pkgdb has a cron script that runs weekly that updates the
            # upstream url there, so when that happens, we'll be triggered
            # and can try again.
            self.log.warn("New package %r has no homepage.  Dropping." % name)
            return

        self.log.info("Considering new package %r with %r" % (name, homepage))

        anitya = hotness.anitya.Anitya(self.anitya_url)
        results = anitya.search_by_homepage(name, homepage)

        projects = results['projects']
        total = results['total']
        if total > 1:
            self.log.warning("Fail. %i matching projects on anitya." % total)
            self.publish("project.map", msg=dict(
                trigger=msg, total=total, success=False))
        elif total == 1:
            self.log.info("Found one match on Anitya.")
            project = projects[0]
            anitya.login(self.anitya_username, self.anitya_password)

            reason = None
            try:
                anitya.map_new_package(name, project)
            except hotness.anitya.AnityaException as e:
                reason = str(e)
                self.log.warn("Failed to map: %r" % reason)

            self.publish("project.map", msg=dict(
                trigger=msg,
                project=project,
                success=not bool(reason),
                reason=reason))
        else:
            self.log.info("Saw 0 matching projects on anitya.  Adding.")
            anitya.login(self.anitya_username, self.anitya_password)

            reason = None
            try:
                anitya.add_new_project(name, homepage)
            except hotness.anitya.AnityaException as e:
                reason = str(e)
                self.log.warn("Failed to create: %r" % reason)

            self.publish("project.map", msg=dict(
                trigger=msg,
                success=not bool(reason),
                reason=reason))

    def handle_updated_package(self, msg):
        self.log.info("Handling pkgdb update msg %r" % msg.get('msg_id'))

        fields = msg['msg']['fields']
        if not 'upstream_url' in fields:
            self.log.info("Ignoring package edit with no url change.")
            return

        package = msg['msg']['package']
        name = package['name']
        homepage = package['upstream_url']

        self.log.info("Trying url change on %s: %s" % (name, homepage))

        # There are two possible scenarios here.
        # 1) the package already *is mapped* in anitya, in which case we can
        #    update the old url there
        # 2) the package is not mapped there, in which case we handle this like
        #    a new package (and try to create it and map it)

        anitya = hotness.anitya.Anitya(self.anitya_url)
        project = anitya.get_project_by_package(name)

        if project:
            self.log.info("Found project with name %s" % project['name'])
            anitya.login(self.anitya_username, self.anitya_password)
            if project['homepage'] == homepage:
                self.log.info("No need to update anitya for %s.  Homepages"
                                " are already in sync." % project['name'])
                return

            self.log.info("Updating anitya url on %s" % project['name'])
            anitya.update_url(project, homepage)
            anitya.force_check(project)
        else:
            # Just pretend like it's a new package, since its not in anitya.
            self.handle_new_package(msg, package)

    def handle_monitor_toggle(self, msg):
        status = msg['msg']['status']
        name = msg['msg']['package']['name']
        homepage = msg['msg']['package']['upstream_url']

        self.log.info("Considering monitored %r with %r" % (name, homepage))

        if not status:
            self.log.info(".. but it was turned off.  Dropping.")
            return

        anitya = hotness.anitya.Anitya(self.anitya_url)
        results = anitya.search_by_homepage(name, homepage)
        total = results['total']

        if total > 1:
            self.log.info("%i projects with %r %r already exist in anitya." % (
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
                self.log.warn("Failed to map: %r" % reason)

            self.publish("project.map", msg=dict(
                trigger=msg,
                project=project,
                success=not bool(reason),
                reason=reason))

            # After mapping, force a check for new tarballs
            anitya.force_check(project)
        else:
            # OTHERWISE, there is *nothing* on anitya about it, so add one.
            self.log.info("Saw 0 matching projects on anitya.  Adding.")
            anitya.login(self.anitya_username, self.anitya_password)

            reason = None
            try:
                anitya.add_new_project(name, homepage)
            except hotness.anitya.AnityaException as e:
                reason = str(e)
                self.log.warn("Failed to create: %r" % reason)

            self.publish("project.map", msg=dict(
                trigger=msg,
                success=not bool(reason),
                reason=reason))

    def is_monitored(self, package):
        """ Returns True if a package is marked as 'monitored' in pkgdb2. """

        url = '{0}/package/{1}'.format(self.pkgdb_url, package)
        self.log.debug("Checking %r" % url)
        r = requests.get(url)

        if not r.status_code == 200:
            self.log.warning('URL %s returned code %s', r.url, r.status_code)
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
            self.log.exception("Problem interacting with pkgdb.")
            return False

    @hotness.cache.cache.cache_on_arguments()
    def in_pkgdb(self, package):
        """ Returns True if a package is in the Fedora pkgdb. """

        url = '{0}/package/{1}'.format(self.pkgdb_url, package)
        self.log.debug("Checking %r" % url)
        r = requests.get(url)

        if r.status_code == 404:
            return False
        if r.status_code != 200:
            self.log.warning('URL %s returned code %s', r.url, r.status_code)
            return False
        return True

    @hotness.cache.cache.cache_on_arguments()
    def get_dist_tag(self):
        url = '{0}/collections/master/'.format(self.pkgdb_url)
        self.log.debug("Getting dist tag from %r" % url)
        r = requests.get(url)

        if not r.status_code == 200:
            raise IOError('URL %s returned code %s', r.url, r.status_code)

        data = r.json()
        collection = data['collections'][0]
        tag = collection['dist_tag'][1:]
        self.log.debug("Got rawhide suffix %r" % tag)
        return tag

    def _update_tasks(self, task_id, state):
        cwd = os.getcwd()
        tmp = tempfile.mkdtemp(prefix='thn-rh', dir='/var/tmp')
        os.chdir(tmp)

        bz = ""
        bug = None
        rh_stuff = None
        text = 'Scratch build %s http://koji.fedoraproject.org/koji/taskinfo?taskID=%s'
        # Remember BZ from old trigger which we are looking for.
        # First of all we will check whether old task was finished
        if task_id in self.old_triggered_task_ids:
            self.old_triggered_task_ids[task_id][1] = state
            bz, old_state, package, old_version = self.old_triggered_task_ids[task_id]
            # if state is CLOSED, then build was finished properly
            for new_task_id, values in six.iteritems(self.new_triggered_task_ids):
                (new_bz, new_state, new_version, new_package) = values
                if int(new_bz.bug_id) == int(bz.bug_id):
                    if old_state == 'CLOSED':
                        # if koji build is finished
                        if new_state is not None:
                            # Koji build was done properly as for old as for new builds rebase-helper is not called
                            if new_state == 'CANCELED':
                                bug = None
                                rh_stuff = None
                            else:
                                bug = bz
                                rh_stuff = self.buildsys.rebase_helper_checkers(new_version,
                                                                                str(task_id),
                                                                                str(new_task_id),
                                                                                tmp)
                                text = text % (new_state, new_task_id)
                                self.bugzilla.follow_up(text, bug)
                            # new build was cancelled. We do not have nothing to do.
                            self.new_triggered_task_ids.pop(new_task_id)
                            self.old_triggered_task_ids.pop(task_id)
                        # Koji task is not finished yet
                        else:
                            bug = None
                            rh_stuff = None
                    else:
                        # if it was CANCELED or FAILED, then we do not care.
                        # We remove koji builds from both triggers
                        # Check if we have proper BZ and then remove it.
                        self.old_triggered_task_ids.pop(task_id)
                        self.new_triggered_task_ids.pop(new_task_id)
                        bug = None
                        rh_stuff = None
                    break
        # if task_id is in new trigger let's check
        elif task_id in self.new_triggered_task_ids:
            self.new_triggered_task_ids[task_id][1] = state
            # Remember BZ from new trigger
            bz, new_state, new_version, package = self.new_triggered_task_ids[task_id]
            # We do not have nothing to do if koji was canceled
            # remove task_ids from old and new triggers
            for old_task_id, (old_bz, old_state, old_version, old_package) in six.iteritems(self.old_triggered_task_ids):
                if int(old_bz.bug_id) == int(bz.bug_id):
                    if new_state == 'CANCELED':
                        self.new_triggered_task_ids.pop(task_id)
                        self.old_triggered_task_ids.pop(old_task_id)
                        bug = None
                        rh_stuff = None
                    # Koji build was successful and we can compare both packages
                    elif new_state == 'CLOSED':
                        self.bugzilla.follow_up(text, bug)
                        if old_state is not None:
                            # We do not want to call rebase-helper if old koji was cancelled
                            # remove both task from triggers
                            if old_state == 'CLOSED':
                                rh_stuff = self.buildsys.rebase_helper_checkers(new_version,
                                                                                str(old_task_id),
                                                                                str(task_id),
                                                                                tmp)
                                bug = bz
                                text = text % (new_state, task_id)
                                self.bugzilla.follow_up(text, bug)
                            # Old sources failed or cancelled. We do not have nothing to do
                            elif old_state in ('FAILED', 'CANCELED'):
                                bug = None
                                rh_stuff = None
                            self.old_triggered_task_ids.pop(old_task_id)
                            self.new_triggered_task_ids.pop(task_id)
                        # Old sources has not been finished yet
                        else:
                            bug = None
                            rh_stuff = None
                    # Koji build failed and we have to attach build logs from rebase-helper
                    else:
                        if old_state is not None and old_state not in ('FAILED', 'CANCELED'):
                            rh_stuff = self.buildsys.rebase_helper_checkers(new_version,
                                                                            str(old_task_id),
                                                                            str(task_id),
                                                                            tmp)
                            bug = bz
                            self.old_triggered_task_ids.pop(old_task_id)
                            self.new_triggered_task_ids.pop(task_id)
                            text = text % (new_state, task_id)
                            self.bugzilla.follow_up(text, bug)
                    break

        if bug and rh_stuff:
            self._update_bz_rh(bug, rh_stuff)
        shutil.rmtree(tmp)
        os.chdir(cwd)

    def _update_bz_rh(self,  bugs, rh_stuff):
        # update BZ based on rebase-helper results
        if rh_stuff:
            # Attach build logs from new sources each time
            if 'build_logs' in rh_stuff and 'build_ref' in rh_stuff['build_logs']:
                build_ref = rh_stuff['build_logs']['build_ref']['new']
                if build_ref['logs']:
                    for log in build_ref['logs']:
                        if os.path.getsize(log) == 0:
                            continue
                        if log.endswith('root.log') or log.endswith('build.log'):
                            rh_log = 'Build log from new sources %s.' % (os.path.basename(log))
                            self.bugzilla.attach_patch(log, rh_log, bugs)
            # if check logs are available attach them
            if 'checkers' in rh_stuff:
                if rh_stuff['checkers']:
                    for check_name, log in six.iteritems(rh_stuff['checkers']):
                        self.log.info('%s %s' % (check_name, log))
                        if log is None:
                            continue
                        if os.path.getsize(log) == 0:
                            continue
                        rh_checkers = "Result from checker %s." % check_name
                        self.bugzilla.attach_patch(log, rh_checkers, bugs)
            # if logs are available from rebase-helper attach them
            if 'logs' in rh_stuff:
                for log in rh_stuff['logs']:
                    if os.path.getsize(log) == 0:
                        continue
                    rh_logs = "Log %s provided by rebase-helper." % (os.path.basename(log))
                    self.bugzilla.attach_patch(log, rh_logs, bugs)
