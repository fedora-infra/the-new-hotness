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

* Or join #fedora-fedmsg IRC channel on freenode and watch for ``hotness``
  messages.

Development
^^^^^^^^^^^

Contributions are welcome, check out `contribution guidelines <https://the-new-hotness.readthedocs.io/en/stable/dev-guide.html#contribution-guidelines>`_.

Future Plans
^^^^^^^^^^^^

- Kick off koji scratch builds of new upstream releases and comment in existing
  bugs with the status.
- Attach patches to bugs of simple revbump changes?
- Add support for creating github issues for flathub projects
