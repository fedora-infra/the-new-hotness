Contributing
============

The New Hotness welcomes contributions! This document should help you get started.


Contribution Guidelines
-----------------------

When you make a pull request, a Fedora Infrastructure team member will review your
code. Please make sure you follow the guidelines below:

Code style
^^^^^^^^^^

We follow the `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ style guide for Python.
The test suite includes a test that enforces the required style, so all you need to do is
run the tests to ensure your code follows the style. If the unit test passes, you are
good to go!

We are using `Black <https://github.com/ambv/black>` to automatically format
the source code. It is also checked in CI. The Black webpage contains
instructions to configure your editor to run it on the files you edit.

Unit tests
^^^^^^^^^^

All unit tests must pass. All new code should have 100% test coverage.
Any bugfix should be accompanied by one or more unit tests to demonstrate the fix.
If you are unsure how to write unit tests for your code,
we will be happy to help you during the code review process.


Development environment
-----------------------

Using Vagrant
^^^^^^^^^^^^^

The best way to set up a development enviroment is to use `Vagrant <https://vagrantup.com/>`_.
To get started, install Vagrant::

    $ sudo dnf install vagrant libvirt vagrant-libvirt vagrant-sshfs ansible

Next, clone the repository and configure your Vagrantfile::

    $ git clone https://github.com/fedora-infra/the-new-hotness.git
    $ cd the-new-hotness
    $ cp Vagrantfile.example Vagrantfile
    $ vagrant up
    $ vagrant ssh

Before you can run ``the-new-hotness``, you need to add your bugzilla credentials
to the configuration. You can set these credentials in ``~/.fedmsg.d/hotness.py``
in the virtual machine.

You also need to acquire a valid Kerberos ticket to perform Koji scratch builds.
You can get this by performing ``kinit <fas-username>@FEDORAPROJECT.ORG``.

.. warning::
    Services will fail to start if you do not provide valid credentials.

You now have a functional development environment. The message of the day for the virtual machine
has some helpful tips, but the basic services can be started in the virtual machine with::

    $ systemctl --user start hub.service relay.service

Log output is viewable with ``journalctl --user-unit relay.service --user-unit hub.service``.

Using Python virtual env
^^^^^^^^^^^^^^^^^^^^^^^^

Set up your environment with::

    $ sudo yum install rpm yum-utils

    $ virtualenv my-env --system-site-packages
    $ source my-env/bin/activate

    $ python setup.py develop

And then run it with::

    $ fedmsg-hub

It should pick up the the-new-hotness consumer and start running.

Hacking
'''''''

1. Can you run it?  Try running ``PYTHONPATH=.fedmsg-hub`` in your virtualenv.
   Does it look like it starts without tracebacks?
2. You may need to edit ``fedmsg.d/hotness-example.py`` and add 'bugzilla'
   username and password.  To create those for yourself, check out
   https://partner-bugzilla.redhat.com/ (that's a "test" bugzilla instance that
   you can do whatever to -- it gets repaved every so often and it never sends
   emails to people so we can spam test stuff in tickets without worry)
3. If you can get it running, it will be useful to be able to locally fake
   messages from anitya (release-monitoring.org).., for that you'll need to:
4. Add a new file to ``fedmsg.d/`` called ``fedmsg.d/relay.py`` and add these
   contents to it::

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

5. Open three terminals, activate your virtualenv in all three and cd into the the-new-hotness/ dir.
6. In one terminal run ``fedmsg-relay`` with no arguments.  It should start in
   the foreground and show some logs and then sit there.  It shouldn't have any
   tracebacks going by.
7. In another terminal run ``fedmsg-tail --really-pretty``.  It should start up
   and just sit there, waiting for messages to arrive.
8. In the third terminal run ``echo "liberation" | fedmsg-logger``.  If you
   look at the second terminal from point 3.3, It should have a JSON blob show
   up. Success!  you just sent a fedmsg message locally to a fedmsg-relay which
   then got bounced over to fedmsg-tail.

9. Keep 'fedmsg-relay' open cause you'll need it.  Keep 'fedmsg-tail' open for debugging.
10. Find anitya messages from the past here http://apps.fedoraproject.org/datagrepper/raw?category=anitya
11. Get the 'msg-id' from one of them and replay it on your local fedmsg-relay
    by running
    ``fedmsg-dg-replay --msg-id 2014-cf0182f1-9ecb-48a7-a999-6f24a529b669``
12. Watch what happens in the 'fedmsg-hub' logs.  Did it file a bug?  Did it explode?  Hack!

Simulating updates
^^^^^^^^^^^^^^^^^^

You can now replay actual messages the production deployment of Anitya has sent
with ``fedmsg-dg-replay``::

    $ fedmsg-dg-replay --msg-id <msg-id>

There's a helpful script to retrieve message IDs. From the root of the repository::

    $ python devel/anitya_messages.py
