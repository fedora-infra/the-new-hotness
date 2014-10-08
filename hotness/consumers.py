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

import bugzilla

import fedmsg
import fedmsg.consumers

import hotness.cache
import hotness.helpers
import hotness.repository


class BugzillaTicketFiler(fedmsg.consumers.FedmsgConsumer):

    # This is the real production topic
    #topic = 'org.release-monitoring.prod.anitya.project.version.update'

    # For development, I am using this so I can test with this command:
    # $ fedmsg-dg-replay --msg-id 2014-77ff95ff-3373-4926-bf23-bf0754b0925c
    topic = 'org.fedoraproject.dev.anitya.project.version.update'

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

        default = 'https://partner-bugzilla.redhat.com'
        url = self.config.get('bugzilla.url', default)
        username = self.config['bugzilla.username']
        password = self.config['bugzilla.password']
        self.bugzilla = bugzilla.Bugzilla(url=url)
        self.log.info("Logging in to %s" % url)
        self.bugzilla.login(username, password)

        # Also, set up our global cache object.
        self.log.info("Configuring cache.")
        with hotness.cache.cache_lock:
            if not hasattr(hotness.cache.cache, 'backend'):
                hotness.cache.cache.configure(**self.config['hotness.cache'])

        self.repoid = self.config.get('hotness.repoid')
        self.log.info("Using hotness.repoid=%r" % self.repoid)
        self.distro = self.config.get('hotness.distro', 'Fedora')
        self.log.info("Using hotness.distro=%r" % self.distro)

        self.log.info("That new hotness ticket filer is all initialized")

    def publish(self, topic, msg):
        self.log.info("publishing topic %r" % topic)
        fedmsg.publish(modname='hotness', topic=topic, msg=msg)

    def consume(self, msg):
        topic, msg = msg['topic'], msg['body']
        self.log.info("Received %r" % msg.get('msg_id', None))

        # What is this thing called in our distro?
        mappings = dict([
            (p['distro'], p['package_name']) for p in msg['msg']['packages']
        ])
        if not self.distro in mappings:
            self.log.info("No Fedora for %r" % msg['msg']['project']['name'])
            return

        package = mappings['Fedora']

        # Is it new to us?
        version, release = hotness.repository.get_version(package, self.repoid)
        upstream = msg['msg']['upstream_version']
        self.log.info("Comparing upstream %s against repo %s-%s" % (
            upstream, version, release))
        diff = hotness.helpers.cmp_upstream_repo(upstream, (version, release))

        if diff == 1:
            self.log.info("Found a new version.")
            raise NotImplementedError
        else:
            self.publish("noop", msg=dict(
                anitya=msg, current_version=current_version
            ))

