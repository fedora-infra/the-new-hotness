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


class BugzillaConsumer(moksha.hub.api.Consumer):

    # This is /topic/bugzilla in STOMP land.
    topic = '/topic/bugzilla'

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

    def __init__(self, hub):
        super(BugzillaConsumer, self).__init__(hub)
        products = hub.config.get('bugzilla.products', 'Fedora, Fedora EPEL')
        self.products = [product.strip() for product in products.split(',')]

        # Set up a queue to communicate between the main twisted thread
        # receiving stomp messages, and a worker thread that pulls items off
        # the queue, makes bz queries, and republishes to fedmsg.
        self.queue = queue.Queue()

        # Last thing we do is kick off our worker in a background thread.
        moksha.hub.reactor.reactor.callInThread(self.worker)
        self.log.info("Initialized bugzilla2fedmsg STOMP consumer.")

    def consume(self, msg):
        """ Receive a STOMP message and put it on the queue for the worker """
        self.log.info("Main thread received %r.  Queueing." % msg)
        self.queue.put([msg])

    def worker(self):
        """ A worker thread that pulls stuff off the main thread's queue. """

        self.log.info("Starting bugzilla2fedmsg worker thread.")

        # First, initialize fedmsg and bugzilla in this thread's context.
        hostname = socket.gethostname().split('.', 1)[0]
        fedmsg.init(name='bugzilla.%s' % hostname)

        self.bugzilla = bugzilla.Bugzilla(url=self.hub.config.get(
            'bugzilla.url', 'https://bugzilla.redhat.com'))

        # Then, start working, forever.
        self.log.info("bugzilla2fedmsg worker thread listening to the queue.")
        for msg in self.queue.get():
            topic, msg = msg['topic'], msg['body']
            self.log.info("Worker thread picking up %r" % msg)
            self.handle(topic, msg)

    def handle(self, topic, msg):

        # First, look up our bug in bugzilla.
        bug = self.bugzilla.getbug(msg['bug_id'])

        # Drop it if we don't care about it.
        if bug.product not in self.products:
            self.log.info("* DROP: %r not in %r" % (
                bug.product, self.products))
            return

        # Parse the timestamp in msg.  It looks like 2013-05-17T02:33:00
        fmt = '%Y-%m-%dT%H:%M:%S'
        msg['timestamp'] = datetime.datetime.strptime(msg['timestamp'], fmt)

        # Find the event from the bz history that most likely corresponds here.
        self.log.info("* Gathering history for #%s" % msg['bug_id'])
        history = bug.get_history()['bugs'][0]['history']
        history = self.convert_datetimes(history)
        event = self.find_relevant_event(msg, history)

        # If there are no events in the history, then this is a new bug.
        topic = 'bug.update'
        if not event:
            topic = 'bug.new'

        self.log.info("* Gathering metadata for #%s" % msg['bug_id'])
        bug = dict([
            (field, getattr(bug, field, None))
            for field in self.bug_fields
        ])
        bug = self.convert_datetimes(bug)

        self.log.info("* Republishing #%s" % msg['bug_id'])
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

    @staticmethod
    def convert_datetimes(obj):
        """ Recursively convert bugzilla DateTimes to stdlib datetimes. """

        if isinstance(obj, list):
            return [BugzillaConsumer.convert_datetimes(item) for item in obj]
        elif isinstance(obj, dict):
            return dict([
                (k, BugzillaConsumer.convert_datetimes(v))
                for k, v in obj.items()
            ])
        elif hasattr(obj, 'timetuple'):
            timestamp = time.mktime(obj.timetuple())
            return datetime.datetime.fromtimestamp(timestamp)
        else:
            return obj
