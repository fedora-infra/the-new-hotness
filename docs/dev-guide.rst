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

Unit tests
^^^^^^^^^^

All unit tests must pass. All new code should have 100% test coverage.
Any bugfix should be accompanied by one or more unit tests to demonstrate the fix.
If you are unsure how to write unit tests for your code,
we will be happy to help you during the code review process.


Development environment
-----------------------

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

You now have a functional development environment. The message of the day for the virtual machine
has some helpful tips, but the basic services can be started in the virtual machine with::

    $ systemctl --user start hub.service relay.service

Log output is viewable with ``journalctl``.

Simulating updates
^^^^^^^^^^^^^^^^^^

You can now replay actual messages the production deployment of Anitya has sent
with ``fedmsg-dg-replay``::

    $ fedmsg-dg-replay --msg-id <msg-id>

There's a helpful script to retrieve message IDs. From the root of the repository::

    $ python devel/anitya_messages.py
