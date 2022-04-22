.. image:: https://img.shields.io/pypi/v/the-new-hotness.svg
  :target: https://pypi.org/project/the-new-hotness/

.. image:: https://readthedocs.org/projects/the-new-hotness/badge/?version=latest
  :alt: Documentation Status
  :target: https://the-new-hotness.readthedocs.io/en/latest/?badge=latest

the-new-hotness
---------------

`Fedora-messaging <https://github.com/fedora-infra/fedora-messaging>`_ consumer that listens to `release-monitoring.org
<http://release-monitoring.org>`_ and files bugzilla bugs in response (to
notify packagers that they can update their packages).

For additional information see `documentation <https://the-new-hotness.readthedocs.io/en/stable/>`_.

Seeing it in action
^^^^^^^^^^^^^^^^^^^

To see recent messages from the-new-hotness:

* Check Fedora's `datagrepper
  <https://apps.fedoraproject.org/datagrepper/raw?category=hotness&delta=2592000>`_

* Or join #fedora-fedmsg IRC channel on `libera <https://libera.chat/>`_ and watch for ``hotness``
  messages.

To see recent koji builds started by the-new-hotness:

* Check Fedora's `koji builds
  <https://koji.fedoraproject.org/koji/tasks?owner=the-new-hotness/release-monitoring.org&state=all>`_

Development
^^^^^^^^^^^

Contributions are welcome, check out `contribution guidelines <https://the-new-hotness.readthedocs.io/en/stable/dev-guide.html#contribution-guidelines>`_.
