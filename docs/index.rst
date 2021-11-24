.. The New Hotness documentation master file, created by
   sphinx-quickstart on Mon Nov 21 16:11:04 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to The New Hotness documentation!
=========================================

The New Hotness is a service that integrates with `Anitya <https://github.com/fedora-infra/anitya/>`_
via `Fedora-messaging <https://github.com/fedora-infra/fedora-messaging>`_
to automatically perform tasks when a project is updated.
For example, the Fedora project uses it to file Bugzilla reports when new versions are available.
The New Hotness attempts to build the new version and reports problems on the bug it files.

:Github page: https://github.com/fedora-infra/the-new-hotness

User guide
----------

.. toctree::
   :maxdepth: 2

   user-guide

Admin guide
-----------

.. toctree::
   :maxdepth: 2

   admin-guide

Developer guide
---------------

.. toctree::
   :maxdepth: 2

   dev-guide
   requirements
   ca-design
   message-schema

Releases
--------

.. toctree::
   :maxdepth: 2

   release-notes

