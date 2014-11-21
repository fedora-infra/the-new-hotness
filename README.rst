`Fedmsg <http://fedmsg.com>`_ consumer that listens to `release-monitoring.org
<http://release-monitoring.org>`_ and files bugzilla bugs in response (to
notify packagers that they can update their packages).

Set up your environment with::

    $ sudo yum install rpm yum-utils

    $ virtualenv my-env --system-site-packages
    $ source my-env/bin/activate

    $ python setup.py develop

And then run it with::

    $ fedmsg-hub

It should pick up the the-new-hotness consumer and start running.

Future Plans
------------

- Kick off koji scratch builds of new upstream releases and comment in existing
  bugs with the status.
- Attach patches to bugs of simple revbump changes?

Hacking
-------

0. Create a virtualenv, then install deps and the hotness itself with ``python setup.py develop``
1. Can you run it?  Try running ``fedmsg-hub`` in your virtualenv.  Does it look like it starts without tracebacks?
2. You may need to edit ``fedmsg.d/hotness-example.py`` and add 'bugzilla'
   username and password.  To create those for yourself, check out
   https://partner-bugzilla.redhat.com/ (that's a "test" bugzilla instance that
   you can do whatever to -- it gets repaved every so often and it never sends
   emails to people so we can spam test stuff in tickets without worry)
3. If you can get it running, it will be useful to be able to locally fake
   messages from anitya (release-monitoring.org).., for that you'll need to:

3.1. Add a new file to ``fedmsg.d/`` called ``fedmsg.d/relay.py`` and add these contents to it::

    config = dict(
        endpoints={
            # This is the output side of the relay to which the-new-hotness
            # can listen (where the-new-hotness is running as a part of 'fedmsg-hub')
            "relay_outbound": [
                "tcp://127.0.0.1:4001",
            ],
        },

        # This is the input side of the relay to which 'fedmsg-logger' and 'fedmsg-dg-replay' will send messages.
        # It will just repeat those messages out the 'relay_outbound' endpoint on your own box.
        relay_inbound=[
            "tcp://127.0.0.1:2003",
        ],
    )

3.2. Open three terminals, activate your virtualenv in all three and cd into the the-new-hotness/ dir.
3.3. In one terminal run ``fedmsg-relay`` with no arguments.  It should start in the foreground and show some logs and then sit there.  It shouldn't have any tracebacks going by.
3.4. In another terminal run ``fedmsg-tail --really-pretty``.  It should start up and just sit there, waiting for messages to arrive.
3.5. In the third terminal run ``echo "liberation" | fedmsg-logger``.  If you look at the second terminal from point 3.3, It should have a JSON blob show up. Success!  you just sent a fedmsg message locally to a fedmsg-relay which then got bounced over to fedmsg-tail.

4. Keep 'fedmsg-relay' open cause you'll need it.  Keep 'fedmsg-tail' open for debugging.
5. Find anitya messages from the past here http://apps.fedoraproject.org/datagrepper/raw?category=anitya
6. Get the 'msg-id' from one of them and replay it on your local fedmsg-relay
   by running
   ``fedmsg-dg-replay --msg-id 2014-cf0182f1-9ecb-48a7-a999-6f24a529b669``
7. Watch what happens in the 'fedmsg-hub' logs.  Did it file a bug?  Did it explode?  Hack!
