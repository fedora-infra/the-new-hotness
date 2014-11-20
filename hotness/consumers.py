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

import fedmsg
import fedmsg.consumers
import requests

import hotness.buildsys
import hotness.bz
import hotness.cache
import hotness.helpers
import hotness.repository


class BugzillaTicketFiler(fedmsg.consumers.FedmsgConsumer):


    # Moksha *should* be able to handle a list of topics, but it lost that
    # somewhere along the way.  We'll need to patch it to get that back.
    #topic = [
    #    # This is the real production topic
    #    # topic = 'org.release-monitoring.prod.anitya.project.version.update'

    #    # For development, I am using this so I can test with this command:
    #    # $ fedmsg-dg-replay --msg-id 2014-77ff95ff-3373-4926-bf23-bf0754b0925c
    #    'org.fedoraproject.dev.anitya.project.version.update',

    #    # Anyways, we also listen for koji scratch builds to circle back:
    #    'org.fedoraproject.prod.buildsys.task.state.change',
    #]

    # In the meantime, just subscribe to all messages and throw away the ones
    # we don't want.
    topic = '*'

    config_key = 'hotness.bugzilla.enabled'

    def __init__(self, hub):
        super(BugzillaTicketFiler, self).__init__(hub)

        if not self._initialized:
            return

        # This is just convenient.
        self.config = self.hub.config

        # First, initialize fedmsg and bugzilla in this thread's context.
        hostname = socket.gethostname().split('.', 1)[0]
        fedmsg.init(name='hotness.%s' % hostname)

        self.bugzilla = hotness.bz.Bugzilla(
            consumer=self, config=self.config['hotness.bugzilla'])
        self.buildsys = hotness.buildsys.Koji(
            consumer=self, config=self.config['hotness.koji'])

        default = 'https://admin.fedoraproject.org/pkgdb/api'
        self.pkgdb_url = self.config.get('hotness.pkgdb_url', default)

        # Also, set up our global cache object.
        self.log.info("Configuring cache.")
        with hotness.cache.cache_lock:
            if not hasattr(hotness.cache.cache, 'backend'):
                hotness.cache.cache.configure(**self.config['hotness.cache'])

        self.yumconfig = self.config.get('hotness.yumconfig')
        self.log.info("Using hotness.yumconfig=%r" % self.yumconfig)
        self.repoid = self.config.get('hotness.repoid', 'rawhide')
        self.log.info("Using hotness.repoid=%r" % self.repoid)
        self.distro = self.config.get('hotness.distro', 'Fedora')
        self.log.info("Using hotness.distro=%r" % self.distro)

        # Build a little store where we'll keep track of what koji scratch
        # builds we have kicked off.  We'll look later for messages indicating
        # that they have completed.
        self.triggered_task_ids = {}

        self.log.info("That new hotness ticket filer is all initialized")

    def publish(self, topic, msg):
        self.log.info("publishing topic %r" % topic)
        fedmsg.publish(modname='hotness', topic=topic, msg=msg)

    def consume(self, msg):
        topic, msg = msg['topic'], msg['body']
        self.log.debug("Received %r" % msg.get('msg_id', None))

        if topic.endswith('anitya.project.version.update'):
            self.handle_anitya(msg)
        elif topic.endswith('buildsys.task.state.change'):
            self.handle_buildsys(msg)
        else:
            self.log.debug("Dropping %r %r" % (topic, msg['msg_id']))
            pass

    def handle_anitya(self, msg):
        self.log.info("Handling anitya msg %r" % msg.get('msg_id', None))
        # First, What is this thing called in our distro?
        # (we do this little inner.get(..) trick to handle legacy messages)
        inner = msg['msg'].get('message', msg['msg'])
        mappings = dict([
            (p['distro'], p['package_name']) for p in inner['packages']
        ])
        if self.distro not in mappings:
            self.log.info("No %r mapping for %r.  Dropping." % (
                self.distro, msg['msg']['project']['name']))
            return

        package = mappings['Fedora']
        url = msg['msg']['project']['homepage']

        # Is it something that we're being asked not to act on:
        if not self.is_monitored(package):
            self.log.info("Pkgdb says not to monitor %r.  Dropping." % package)
            return

        # Is it new to us?
        fname = self.yumconfig
        version, release = hotness.repository.get_version(package, fname)
        upstream = inner['upstream_version']
        self.log.info("Comparing upstream %s against repo %s-%s" % (
            upstream, version, release))
        diff = hotness.helpers.cmp_upstream_repo(upstream, (version, release))

        # If so, then poke bugzilla and start a scratch build
        if diff == 1:
            self.log.info("OK, %s is newer than %s-%s" % (
                upstream, version, release))

            bz = self.bugzilla.handle(package, upstream, version, release, url)
            if not bz:
                self.log.info("No RHBZ change detected (odd).  Aborting.")
                return

            self.log.info("Now with RHBZ %r, time to do koji stuff" % bz)
            task_id = self.buildsys.handle(package, upstream, version, bz)

            # Map that koji task_id to the bz ticket we want to follow up on
            self.triggered_task_ids[task_id] = bz

    def handle_buildsys(self, msg):
        # Is this a scratch build that we triggered a couple minutes ago?
        task_id = msg['msg']['info']['id']
        if task_id not in self.triggered_task_ids:
            self.log.debug("Koji task_id=%r is not ours.  Drop it." % task_id)
            return

        self.log.info("Handling koji msg %r" % msg.get('msg_id', None))

        # see koji.TASK_STATES for all values
        done_states = ['FAILED', 'CANCELED', 'CLOSED']
        state = msg['msg']['new']
        self.log.info("Heard word that our task %r is %r." % (task_id, state))
        if state not in done_states:
            return

        bug = self.triggered_task_ids.pop(task_id)
        url = self.buildsys.url_for(task_id)
        self.bugzilla.follow_up(url, state, bug)

    def is_monitored(self, package):
        """ Returns True if a package is marked as 'monitored' in pkgdb2. """

        url = '{0}/package/{1}'.format(self.pkgdb_url, package)
        self.log.info("Checking %r" % url)
        r = requests.get(url)

        if not r.status_code == 200:
            self.log.warning('URL %s returned code %s', r.url, r.status_code)
            return False

        try:
            data = r.json()
            package = data['packages'][0]
            return package['package'].get('monitor', True)
        except:
            self.log.exception("Problem interacting with pkgdb.")
            return False
