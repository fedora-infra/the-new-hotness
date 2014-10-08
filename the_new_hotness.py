# -*- coding: utf-8 -*-
""" Fedmsg consumers that listen to `anitya <http://release-monitoring.org>`_.

Authors:    Ralph Bean <rbean@redhat.com>

"""

import socket

import bugzilla

import fedmsg
import fedmsg.consumers


class BugzillaTicketFiler(fedmsg.consumers.FedmsgConsumer):
    topic = 'org.release-monitoring.prod.anitya.*'
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

        self.log.info("That new hotness ticket filer is all initialized")

    def consume(self, msg):
        topic, msg = msg['topic'], msg['body']
        # TODO - file a bug and publish a fedmsg saying that we did so or
        # failed to do so.
