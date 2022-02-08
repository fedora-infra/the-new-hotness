Administration
==============

This guide will take you through installation and configuration process of
The New Hotness, so you are able to run The New Hotness in your own infrastructure.

Installation
------------

The New Hotness is available through `PyPi <https://pypi.org/project/the-new-hotness/>`_.

Prior to the installation itself there are few dependencies that need to be on the system.
Because The New Hotness is running in Fedora infrastructure so this guide assumes you
are running Fedora as your main system and thus need to install following packages. These tools
are used by The New Hotness to work with the packages::

  $ sudo dnf install -y fedpkg rpmdevtools

You can install the latest version by running::

  $ pip install the-new-hotness

External systems
----------------

The New Hotness communicates with multiple external systems to provide all the functionality.
To be able to use maximum potential of The New Hotness, you need to connect it to following
external systems:

* `mdapi <https://pagure.io/mdapi>`_

  Metadata API hosted by Fedora. The New Hotness uses it to look for the newest build in koji.
  
* `bugzilla <https://www.bugzilla.org/>`_

  The New Hotness is looking for existing issue for the package in bugzilla and if
  none is found creates one.
  
* `anitya <https://github.com/fedora-infra/anitya>`_

  The New Hotness is consuming fedora messages from Anitya and looking for updates
  of the packages that we want to process.
  
* cache

  This is not really an external system, but it's used as one by The New Hotness.
  Local cache is used to store the information about build if we start a scratch build.
  This will help us to keep track of the builds and correctly react to buildsys fedora
  message.

.. note::
   Local cache will be replaced by Redis in future.

* `koji <https://pagure.io/koji/>`_

  Koji is a build system used to start scratch builds. First we need to upload sources
  to lookaside cache and than we can start the build.
  
* `pdc <https://github.com/product-definition-center/product-definition-center>`_

  PDC (Product Definition Center) API is used to check if the package is retired or not.
  
* `pagure <https://pagure.io/pagure>`_

  Dist-git system used by Fedora containing notification settings for The New Hotness and is checked
  if the package even exists. 

Configuration
-------------

The New Hotness configuration is read from the `consumer_config` section of the
`fedora messaging configuration <https://fedora-messaging.readthedocs.io/en/stable/configuration.html>`_.

The configuration is using the TOML format and the sample could be found below.

.. include:: ../config/config.toml.example
   :literal:
