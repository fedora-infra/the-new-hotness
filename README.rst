the-new-hotness
---------------

`Fedmsg <http://fedmsg.com>`_ consumer that listens to `release-monitoring.org
<http://release-monitoring.org>`_ and files bugzilla bugs in response (to
notify packagers that they can update their packages).

For additional information see `documentation <https://the-new-hotness.readthedocs.io/en/stable/>`_.

Development
^^^^^^^^^^^

Contributions are welcomed, check out `contribution guide <https://the-new-hotness.readthedocs.io/en/stable/dev-guide.html#contribution-guidelines>_`.

Future Plans
^^^^^^^^^^^^

- Kick off koji scratch builds of new upstream releases and comment in existing
  bugs with the status.
- Attach patches to bugs of simple revbump changes?
- Add support for creating github issues for flathub projects
