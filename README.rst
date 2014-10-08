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
