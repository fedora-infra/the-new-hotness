# -*- coding: utf-8 -*-
""" Moksha consumer that listens to BZ over STOMP and reproduces to fedmsg.

Authors:    Ralph Bean <rbean@redhat.com>

"""

import Queue as queue  # stdlib
import socket

import bugzilla
import fedmsg
import moksha.hub.api
import moksha.hub.reactor


class BugzillaConsumer(moksha.hub.api.Consumer):

    # Really, we want to use this specific topic to listen to.
    #topic = 'bugzilla.please'
    # But for testing, we'll just listen to all topics with this:
    topic = '*'

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
        topic, msg = msg['topic'], msg['body']
        self.log.info("Main thread received %r" % topic)
        self.queue.put((topic, msg,))

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
        for topic, msg in self.queue.get():
            self.log.info("Worker thread picking up %r" % topic)
            self.handle(topic, msg)

    def handle(self, topic, msg):
        bug = self.bugzilla.getbug(msg['bug_id'])

        if bug.product not in self.products:
            self.log.debug("DROP: %r not in %r" % (bug.product, self.products))
            return

        history = bug.get_history()['bugs'][0]['history']
        event = self.find_relevant_event(msg, history)

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
        best_delta = math.fabs(best['when'] - msg['timestamp'])

        for event in history[1:]:
            if math.fabs(event['when'] - msg['timestamp']) < best_delta:
                best = event
                best_delta = math.fabs(best['when'] - msg['timestamp'])

        return best
