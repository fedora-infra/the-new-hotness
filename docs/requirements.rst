Requirements
============

This chapter describes requirements that The New Hotness needs to fulfill to be
able to work as notification system for maintainers.

List of requirements
--------------------

* Consume messages

  Fedora messaging consumer is the main part of The New Hotness

* Decide if the message should be dropped or the user should be notified

  This could be set in `dist git <https://src.fedoraproject.org>`_

* Do a scratch build and handle response from build system

  In case of The New Hotness, this is `koji <https://pagure.io/koji/>`_

* Create/update bugzilla issue

* Publish messages

* Download sources from source urls

  The New Hotness utilizes `fedpkg <https://pagure.io/fedpkg>`_ for this

* Bump spec file

  The New Hotness utilizes `rpmdevtools <https://fedoraproject.org/wiki/Rpmdevtools>`_ for this

* Create patch and attach it to bugzilla issue

  This is being done by `git format-patch` command
