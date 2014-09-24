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

        # Set up a queue to communicate between the main twisted thread
        # receiving stomp messages, and a worker thread that pulls items off
        # the queue, makes bz queries, and republishes to fedmsg.
        self.incoming = queue.Queue()

        # Last thing we do is kick off our worker(s) in a background thread.
        N = int(self.hub.config.get('bugzilla.num_workers', 1))
        self.workers = []
        for i in range(N):
            # Share our queue, log and config with our workers
            worker = WorkerThread(i, self.incoming, self.log, self.hub.config)
            moksha.hub.reactor.reactor.callInThread(worker.work)
            self.workers.append(worker)

        self.log.info("Initialized bz2fm STOMP consumer with %i workers." % N)

    def consume(self, msg):
        """ Receive a STOMP message and put it on the queue for the worker """
        self.log.info("Main thread received %r.  Queueing." % msg)
        self.incoming.put(msg)

    def stop(self):
        # Drop N quit signals in the queue, one for each worker.
        for worker in self.workers:
            self.incoming.put(StopIteration)

        super(BugzillaConsumer, self).stop()


class WorkerThread(object):
    def __init__(self, idx, incoming, log, config):
        self.idx = idx
        self.incoming = incoming
        self.log = log
        self.config = config

        products = config.get('bugzilla.products', 'Fedora, Fedora EPEL')
        self.products = [product.strip() for product in products.split(',')]

    def debug(self, msg):
        self.log.info("* thread #%i (backlog %i): %s" % (
            self.idx, self.incoming.qsize(), msg))

    def work(self):
        """ A worker thread that pulls stuff off the main thread's queue. """

        self.debug("Starting bz2fm worker.")

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

        # Then, start working, forever.
        self.debug("bz2fm worker thread waiting on incoming queue.")
        while True:
            # This is a blocking call.  It waits until a msg is available.
            msg = self.incoming.get()

            # Then we are being asked to quit
            if msg is StopIteration:
                break

            topic, msg = msg['topic'], msg['body']
            self.debug("Worker thread picking up %r" % msg)
            try:
                self.handle(topic, msg)
            except Exception as e:
                self.log.exception(e)
            self.debug("Going back to waiting on the incoming queue.")

        self.debug("Thread exiting.")

    def handle(self, topic, msg):
        # First, look up our bug in bugzilla.
        self.debug("Gathering metadata for #%s" % msg['bug_id'])
        bug = self.bugzilla.getbug(msg['bug_id'])

        # Drop it if we don't care about it.
        if bug.product not in self.products:
            self.debug("DROP: %r not in %r" % (
                bug.product, self.products))
            return

        # Parse the timestamp in msg.  It looks like 2013-05-17T02:33:00
        fmt = '%Y-%m-%dT%H:%M:%S'
        msg['timestamp'] = datetime.datetime.strptime(msg['timestamp'], fmt)

        # Find the event from the bz history that most likely corresponds here.
        self.debug("Gathering history for #%s" % msg['bug_id'])
        history = bug.get_history()['bugs'][0]['history']
        history = convert_datetimes(history)

        self.debug("Organizing metadata for #%s" % msg['bug_id'])
        bug = dict([(attr, getattr(bug, attr, None)) for attr in bug_fields])
        bug = convert_datetimes(bug)

        comment = self.find_relevant_item(msg, bug['comments'], 'time')
        event = self.find_relevant_item(msg, history, 'when')

        # If there are no events in the history, then this is a new bug.
        topic = 'bug.update'
        if not event and len(bug['comments']) == 1:
            topic = 'bug.new'

        self.debug("Republishing #%s" % msg['bug_id'])
        fedmsg.publish(
            modname='bugzilla',
            topic=topic,
            msg=dict(
                bug=bug,
                event=event,
                comment=comment,
            ),
        )

    @staticmethod
    def find_relevant_item(msg, history, key):
        """ Find the change from the BZ history with the closest timestamp to a
        given message.  Unfortunately, we can't rely on matching the timestamps
        exactly so instead we say that if the best match is within 60s of the
        message, then return it.  Otherwise return None.
        """

        if not history:
            return None

        best = history[0]
        best_delta = abs(best[key] - msg['timestamp'])

        for event in history[1:]:
            if abs(event[key] - msg['timestamp']) < best_delta:
                best = event
                best_delta = abs(best[key] - msg['timestamp'])

        if best_delta < datetime.timedelta(seconds=60):
            return best
        else:
            return None
