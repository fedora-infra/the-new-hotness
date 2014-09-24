# -*- coding: utf-8 -*-
""" Moksha consumer that listens to BZ over STOMP and reproduces to fedmsg.

Authors:    Ralph Bean <rbean@redhat.com>

"""

import datetime
import Queue as queue  # stdlib
import socket
import time

import bugzilla
import fedmsg
import moksha.hub.api
import moksha.hub.reactor

# These are bug fields we're going to try and pass on to fedmsg.
bug_fields = [
    'alias',
    'assigned_to',
    'attachments',
    'blocks',
    'cc',
    'classification',
    'comments',
    'component',
    'components',
    'creation_time',
    'creator',
    'depends_on',
    'description',
    'docs_contact',
    'estimated_time',
    'external_bugs',
    'fixed_in',
    'flags',
    'groups',
    'id',
    'is_cc_accessible',
    'is_confirmed',
    'is_creator_accessible',
    'is_open',
    'keywords',
    'last_change_time',
    'op_sys',
    'platform',
    'priority',
    'product',
    'qa_contact',
    'actual_time',
    'remaining_time',
    'resolution',
    'see_also',
    'severity',
    'status',
    'summary',
    'target_milestone',
    'target_release',
    'url',
    'version',
    'versions',
    'weburl',
    'whiteboard',
]


def convert_datetimes(obj):
    """ Recursively convert bugzilla DateTimes to stdlib datetimes. """

    if isinstance(obj, list):
        return [convert_datetimes(item) for item in obj]
    elif isinstance(obj, dict):
        return dict([
            (k, convert_datetimes(v))
            for k, v in obj.items()
        ])
    elif hasattr(obj, 'timetuple'):
        timestamp = time.mktime(obj.timetuple())
        return datetime.datetime.fromtimestamp(timestamp)
    else:
        return obj


class BugzillaConsumer(moksha.hub.api.Consumer):

    # This is /topic/com.redhat.bugzilla in STOMP land.
    topic = '/topic/com.redhat.bugzilla'

    def __init__(self, hub):
        super(BugzillaConsumer, self).__init__(hub)

        self.config = config = hub.config

        # Backwards compat.  We used to have a self.debug...
        self.debug = self.log.info

        products = config.get('bugzilla.products', 'Fedora, Fedora EPEL')
        self.products = [product.strip() for product in products.split(',')]

        # First, initialize fedmsg and bugzilla in this thread's context.
        hostname = socket.gethostname().split('.', 1)[0]
        fedmsg.init(name='bugzilla.%s' % hostname)

        url = self.config.get('bugzilla.url', 'https://bugzilla.redhat.com')
        username = self.config.get('bugzilla.username', None)
        password = self.config.get('bugzilla.password', None)

        self.bugzilla = bugzilla.Bugzilla(url=url)
        if username and password:
            self.debug("Logging in to %s" % url)
            self.bugzilla.login(username, password)
        else:
            self.debug("No credentials found.  Not logging in to %s" % url)

        self.debug("Initialized bz2fm STOMP consumer.")

    def consume(self, msg):
        topic, msg = msg['topic'], msg['body']

        # First, look up our bug in bugzilla.
        self.debug("Gathering metadata for #%s" % msg['bug_id'])
        bug = self.bugzilla.getbug(msg['bug_id'])

        # Drop it if we don't care about it.
        if bug.product not in self.products:
            self.debug("DROP: %r not in %r" % (bug.product, self.products))
            return

        # Parse the timestamp in msg.  It looks like 2013-05-17T02:33:00
        fmt = '%Y-%m-%dT%H:%M:%S'
        msg['timestamp'] = datetime.datetime.strptime(msg['timestamp'], fmt)

        # Find the event from the bz history that most likely corresponds here.
        self.debug("Gathering history for #%s" % msg['bug_id'])
        history = bug.get_history()['bugs'][0]['history']
        history = convert_datetimes(history)
        event = self.find_relevant_event(msg, history)

        # If there are no events in the history, then this is a new bug.
        topic = 'bug.update'
        if not event:
            topic = 'bug.new'

        self.debug("Organizing metadata for #%s" % msg['bug_id'])
        bug = dict([(attr, getattr(bug, attr, None)) for attr in bug_fields])
        bug = convert_datetimes(bug)

        self.debug("Republishing #%s" % msg['bug_id'])
        fedmsg.publish(
            modname='bugzilla',
            topic=topic,
            msg=dict(
                bug=bug,
                event=event,
            ),
        )

    @staticmethod
    def find_relevant_event(msg, history):
        """ Find the change from the BZ history with the closest timestamp to a
        given message.  Unfortunately, we can't rely on matching the timestamps
        exactly.
        """

        if not history:
            return {}

        best = history[0]
        best_delta = abs(best['when'] - msg['timestamp'])

        for event in history[1:]:
            if abs(event['when'] - msg['timestamp']) < best_delta:
                best = event
                best_delta = abs(best['when'] - msg['timestamp'])

        return best
