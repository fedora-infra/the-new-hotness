# the-new-hotness requirements
To start with Clean architecture design, we need to collect all requirements. In case of the-new-hotness, we could use as requirements existing features.

## Description of the app
The-new-hotness is consuming incoming messages and contacting various external systems to get information about the validity of the message (It's this really update? Does user wants it? Should we do a scratch build?). Based on the information we either drop the message or create/update issue in bugzilla and optionally starting scratch build. 

## List of requirements

* Consume messages
* Decide if the message should be dropped or the user should be notified
* Do a scratch build and handle response from build system
* Create/update bugzilla issue
* Publish messages
* Download sources from source urls
* Bump spec file
* Create patch and attach it to bugzilla issue

## External systems
External systems that the-new-hotness contacts.

* mdapi 

  Used to look for the newest build in koji.
  
* bugzilla

  The-new-hotness is looking for existing issue for the package and if none is found creates one.
  
* anitya

  If we receive message with new mapping, we will contact Anitya and request a new check for versions. Currently this part could be removed, because Anitya is doing checks for new version each hour.
  
* cache

  Local cache used to store the information if the package is in dist git. This will reduce the number of times we call dist git for this information to one.

* koji

  Build system used for scratch builds. First we need to upload sources to lookaside cache and than we can start the build.
  
* pdc

  PDC API is used to check if the package is retired or not.
  
* pagure

  Dist-git system containing notification settings and is checked if the package even exists. 
