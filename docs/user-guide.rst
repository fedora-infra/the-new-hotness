User guide
==========

This chapter describes how the user (packager) can interact with The New Hotness.


Notifications settings
----------------------

The notifications settings for The New Hotness can be set in the
`dist git <https://src.fedoraproject.org>`_. The option is available for each
package as `Monitoring status` option on the left side of the package repository site.

.. note::
   The setting doesn't matter if the project is not created in
   `Anitya <https://release-monitoring.org>`_.

Following is the explanation of the `Monitoring status` options:

* *No-Monitoring* - Project will not be monitored and The New Hotness will drop any
  update for this project

* *Monitoring* - Project will be monitored by The New Hotness and Bugzilla ticket will
  be created each time a new version will be discovered by Anitya.

* *Monitoring and scratch builds* - Project will be monitored by The New Hotness and
  Bugzilla notification will be created each time a new version will be discovered by
  Anitya. Additionally a scratch build will be started for the new version.

* *Monitoring all* - Project will be monitored by The New Hotness and Bugzilla
  notification will be created for every version that will be discovered by Anitya.
  This could cause issues with duplicates in case the version will be deleted and
  retrieved again in Anitya.

* *Monitoring all and scratch builds* - Project will be monitored by The New Hotness
  and Bugzilla notification will be created for every version that will be discovered
  by Anitya. Additionally a scratch build will be started for the newest version retrieved,
  if the version is newer than the one already available in
  `mdapi <https://pagure.io/mdapi>`_. This could cause issues with duplicates in case
  the version will be deleted and retrieved again in Anitya.

.. note::
   The *Monitoring all* and *Monitoring all and scratch builds* options are supported by
   The New Hotness, but not yet available on `dist git <https://src.fedoraproject.org>`_.

Creating a project in Anitya
----------------------------

For The New Hotness to function properly there have to be a project in
`Anitya <https://release-monitoring.org>`_. For the information how to create
a new project, look at the
`user guide in Anitya documentation <https://anitya.readthedocs.io/en/stable/user-guide.html>`_.
