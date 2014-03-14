Moksha consumer that listens to BZ over STOMP and reproduces to fedmsg

Try it out::

    cp development.ini.example development.ini

Edit it to point at your STOMP broker.

Run with::

    moksha-hub

It should pick up the bugzilla2fedmsg consumer.
