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
    $ vagrant up
    $ vagrant ssh

Before you can run ``the-new-hotness``, you need to add your bugzilla credentials
to the configuration. You can set these credentials in ``~/config.toml``
in the virtual machine.

You also need to acquire a valid Kerberos ticket to perform Koji scratch builds.
You can get this by performing ``kinit <fas-username>@FEDORAPROJECT.ORG``.

.. warning::
    Services will fail to start if you do not provide valid credentials.

You now have a functional development environment. The message of the day for the virtual machine
has some helpful tips, but the basic services can be started in the virtual machine with::

    $ systemctl --user start hotness.service

Log output is viewable with ``journalctl --user-unit hotness.service``.

You can also use aliases:

   ``hotstart`` - start the-new-hotness
   ``hotstop`` - stop the-new-hotness
   ``hotlog`` - show log of the-new-hotness

For other aliases look in the ``~/.bashrc`` file.

Using Docker / Podman
^^^^^^^^^^^^^^^^^^^^^

Using Docker you will be able to control each service (hotness app, RabbitMQ, Redis, etc.) separately. You can turn off Redis or RabbitMQ or both, then connect to external services or use them with the application. 

Requirements:

* Docker / Podman (version +3 with podman-docker)
* Docker Compose

Next, clone the repository and start containers::

    $ git clone https://github.com/fedora-infra/the-new-hotness.git
    $ cd the-new-hotness
    $ make up

Hotness container starts after the start of containers running services required by the-new-hotness. Usually, it takes around 10-30 seconds depends on the computer power.

.. list-table:: Container Service Informations:
   :widths: 25 25 50
   :header-rows: 1

   * - Name 1
     - Url
     - Credentials
   * - RabbitMQ
     - http://localhost:5672
     - hotness:hotness
   * - RabbitMQ Management UI
     - http://localhost:15672
     - hotness:hotness
   * - Redis
     - http://localhost:6379
     - not required

Makefile scripts that provide easier container management:

* ``make up`` Starts all the container services
* ``make restart`` Restarts all the container services that are either stopped or running 
* ``make halt`` Stops and removes the containers
* ``make bash`` Connects to hotness container
* ``make logs`` Shows all logs of all containers

Project files are bound to each other with host and container. Whenever you change any project file from the host or the container, the same change will happen on the opposite side as well.

After connecting to hotness container you can run the applicaton with::

    $ fedora-messaging consume

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
with ``fedora-messaging-replay.py``::

    $ python3 devel/fedmsg-messaging-replay.py <msg-id>

There's a helpful script to retrieve message IDs. From the root of the repository::

    $ python devel/anitya_messages.py

Release notes
=============

To add entries to the release notes, create a file in the ``news`` directory
with the ``source.type`` name format, where the ``source`` part of the filename is:

* ``42`` when the change is described in issue ``42``
* ``PR42`` when the change has been implemented in pull request ``42``, and
  there is no associated issue
* ``username`` for contributors (``author`` extention). It should be the
  username part of their commit's email address.

And where ``type`` is label of the issue or PR that is named ``type.label``. If the issue or PR is missing a label, please ask maintainer to add one.

News type can be one of the following:

* ``feature``: for new features
* ``bug``: for bug fixes
* ``api``: for API changes
* ``dev``: for development-related changes
* ``author``: for contributor names
* ``other``: for other changes
  
For example:

If this PR is solving issue #714 labeled as ``type.bug`` and named "Javascript error on add project page", the file inside news should be called 714.bug (PR714.bug if the PR does not have any linked issue and the PR number is 714) and the content of the file would be:

``Javascript error on add project page``

Matching the issue title.

The text inside the file will be used as entry text.
A preview of the release notes can be generated with ``towncrier --draft``.

Release testing guide
=====================

Before releasing a new version it is good to try deployment in `staging environment <https://os.stg.fedoraproject.org>`_.
To deploy the release candidate to staging follow these steps:

1. Clone the-new-hotness repository::

    $ git clone git@github.com:fedora-infra/the-new-hotness.git

2. Checkout the staging branch::

    $ git checkout staging

3. Rebase the current staging branch to master::

    $ git rebase master

4. Push the changes back to staging branch::

    $ git push origin staging

The new staging branch will be automatically deployed in the `staging environment <https://os.stg.fedoraproject.org>`_.

.. note::
    This guide assumes that you have write permissions for the-new-hotness repository.

Release Guide
=============

To do the release you need following python packages installed::

    wheel
    twine
    towncrier

If you are a maintainer and wish to make a release, follow these steps:

1. Change the version in ``hotness.__init__.__version__``. This is used to set the
   version in the documentation project and the setup.py file.

2. (Optional) Update ``version`` in ``hotness_schema/setup.py`` script.

3. Get authors of commits by ``python get-authors.py``.

.. note::
   This script must be executed in ``news`` folder, because it
   creates files in current working directory.

4. Generate the changelog by running ``towncrier``.

.. note::
    If you added any news fragment in the previous step, you might see ``towncrier``
    complaining about removing them, because they are not committed in git.
    Just ignore this and remove all of them manually; release notes will be generated
    anyway.

5. Remove every remaining news fragment from ``news`` folder.

6. Commit your changes with message *the-new-hotness <version>*.

7. Tag a release with ``git tag -s <version>``.

8. Don't forget to ``git push --tags``.

9. Build the Python packages with ``python setup.py sdist bdist_wheel``.

10. Upload the packages with ``twine upload dist/<dists>``.

11. (Optional) Repeat steps 7 and 8 in ``hotness_schema`` folder.

12. Create new release on `GitHub releases <https://github.com/fedora-infra/the-new-hotness/releases>`_.

13. Deploy the new version in staging::

     $ git checkout staging
     $ git rebase master
     $ git push origin staging

14. When successfully tested in staging deploy to production::

     $ git checkout production
     $ git rebase staging
     $ git push origin production

.. note::
    Optional steps are required only if you want to release a new version of message schema.
