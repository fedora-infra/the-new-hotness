Fedmsg consumer that listens to anitya and files bugzilla bugs in response.

Run with::

    $ sudo yum install rpm yum-utils

    $ virtualenv my-env --system-site-packages
    $ source my-env/bin/activate

    $ python setup.py develop

    $ fedmsg-hub

It should pick up the the-new-hotness consumer and start running.
