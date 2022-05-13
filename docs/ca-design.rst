Clean architecture design
=========================

This design describes files and directories structure of the-new-hotness based
on the requirements using clean architecture design. The clean architecture description
will be split to three parts (Entities, Use Cases, External systems) according to clean
architecture design.

Main source file will be `hotness_consumer.py` and will consume and publish messages using
Fedora messaging.

Entities
--------

Inner definitions of objects we will work with. This is the core of the whole application.
Bellow is the application structure.

* domain

  Directory where every domain related source is stored.

  * **__init__.py**

    Module init file.

  * **package.py**

    Internal definition of package. Easily convertable to dict.

Use cases
---------

Use cases corresponds to requirements. This layer will define what the application can do.
Bellow is the directory structure for this layer. This layer also contains abstract classes
which will be inherited by external systems and response/requests definition with any exceptions.

* use_cases

  Directory containing every use_case for this application.

  * **package_check_use_case.py**

    This class will do various checks on the package. This will be done by calling abstract classes
    for external systems. Reports any error using response object.

  * **package_scratch_build_use_case.py**

    This class will start the scratch build and does any error handling when the start of the build
    fails.

  * **notify_user_use_case.py**

    This class will notify the user and does any error handling related to notifier. 

  * **submit_patch_use_case.py**

    This class will submit patch using provided patcher. In current situation this
    will be bugzilla, in future this could be packit.

  * **insert_data_use_case.py**

    This class will insert data to database using the provided database. 

  * **retrieve_data_use_case.py**

    This class will retrieve data from database using the provided database. 

* validators

  Directory containing every external system wrapper that is called to check something.
  In this layer I will only describe the abstract class, which will be inherited by other systems.

  * **__init__.py**

    Module init file.

  * **validator.py**

    Abstract class that needs to be inherited by any external system that is used to validate package.
    This will define the methods that will be called by `package_check_use_case` class.

* builders

  Directory containing any builder. In this layer I will only describe abstract class,
  which will be then inherited in upper layer.

  * **__init__.py**

    Module init file.

  * **builder.py**

    Abstract class that needs to be inherited by any external system that is called to start build.
    This will define methods that will be called by `package_scratch_build_use_case` class.

* notifiers

  Directory containing external systems used to notify users.
  In this layer I will only describe abstract class,
  which will be then inherited in upper layer.

  * **__init__.py**

    Module init file.

  * **notifier.py**

    Abstract class that needs to be inherited by any external system that is called to notify user.
    This will define methods that will be called by `notify_user_use_case` class.

* patchers

  Directory containing external systems used to submit patch created by the-new-hotness.
  In this layer I will only describe abstract class, which will be then inherited in upper layer.

  * **__init__.py**

    Module init file.

  * **patcher.py**

    Abstract class that needs to be inherited by any external system that is called to submit patch.
    This will define methods that will be called by `submit_patch_use_case` class.

* databases

  Directory containing external systems used to store data.

  * **__init__.py**

    Module init file.

  * **database.py**

    Abstract class that needs to be inherited by any external system that is called
    to store/load some persistent data. This will define methods that will be called
    by `insert_data_use_case` and `retrieve_data_use_case` class.

* request_objects

  This directory contains every request object which is passed to use cases.

  * **__init__.py**

    Module init file.

  * **request.py**

    Parent class for requests, needs to be inherited by every request object.
    It defines methods for error management and `__bool__` method,
    which returns `True` if all request attributes are valid and `False` if there is any error.
    This allows for easy verification if request is valid.
    Every use case should validate the request before starting working with it.

  * **package_request.py**

    Request passed to `package_check_use_case`. This request object contains package object.

  * **build_request.py**

    Request passed to `package_scratch_build_use_case`. This request object contains package object
    and optional attributes as dict.

  * **notify_request.py**

    Request passed to `notify_user_use_case`. This request object is inherited from
    `package_request_object` and provides message (String) as optional attributes as dict.

  * **submit_patch_request.py**

    Request passed to `submit_patch_use_case`. This request object is inherited from
    `package_request_object` and provides patch (string) and optional attributes provided as dict.

  * **insert_data_request.py**

    Request passed to `insert_data_use_case`. This request object contains key/value pair
    that will be saved to database.

  * **retrieve_data_request.py**

    Request passed to `retrieve_data_use_case`. This request object retrieves value for
    specific key from database.

* response_objects

  This directory contains every response object which could be returned by use cases.

  * **__init__.py**

    Module init file.

  * **response.py**

    Abstract class which is inherited by other responses. This class also defines
    constants for any response code. Defines `__bool__` method.

  * **response_success.py**

    This class is inherited from `response.py` and is returned when use case finishes successfully.
    Implements `__bool__` method that returns `True` and value attribute, which contains return
    value from use case if any.

  * **response_failure.py**

    This class is inherited from `response.py` and is returned when use case finishes with failure.
    Implements `__bool__` method that returns `False`, value property contains type of error and
    exception with error message and optionally a partial value returned by use case.

* exceptions

  This directory contains any specific exception that could be thrown by any wrapper for external
  system.

  * **__init__.py**

    Module init file.

  * **base_exception.py**

    This is a base class which is inherited by every other exception. It defines attributes
    that are expected by `response_failure.py`.

  * **builder_exception.py**

    This exception should be thrown when builder encounter error that is related to external builder.

  * **notifier_exception.py**

    This exception should be thrown when notifier encounter error that is related to external notifier.

  * **download_exception.py**

    This exception should be thrown when builder can't download the sources for package.

  * **html_exception.py**

    This exception should be thrown when HTML request is unsuccessful and returns anything
    else than 200.

External systems
----------------

This is the outer layer of clean architecture and contains wrappers that are calling external
systems and any helper class used by the wrappers. Wrappers will inherit abstract class
defined in use cases layer.

* validators

  Directory containing every external system contacted to check validity of package.

  * **mdapi.py**

    Class that is checking if the package is newer or not than the package currently available
    in Fedora using mdapi system. Inherits from `validator.py`.

  * **pdc.py**

    Class that is checking if the package is retired or not in Fedora using PDC API.
    Inherits from `validator.py`.

  * **pagure.py**

    Class that retrieves the notification settings from Pagure. Inherits from `validator.py`.

* builders

  Directory containing any builder.

  * **koji.py**

    Class that is used to prepare and start build in Koji. Inherits from `builder.py`.

* notifiers

  Directory containing external systems used to notify users.

  * **bugzilla.py**

    This class contains every method that is needed to create/update issue in bugzilla.
    Inherits from `notifier.py`.

  * **fedora_messaging.py**

    This class is wrapper above Fedora messaging publisher. Inherits from `notifier.py`.

* patchers

  Directory containing external systems used to submit patch created by the-new-hotness.

  * **bugzilla.py**

    This class contains every method that is needed to attach patch to existing issue in bugzilla.
    Inherits from `patcher.py`.

* databases

  Directory containing external systems acting like a database for the-new-hotness.

  * **cache.py**

    This class contains cache for storing key/value entries. Inherits from `database.py`.

  * **redis.py**

    This class contains every method that is needed to insert, retrieve data from Redis database.
    Inherits from `database.py`.

* common

  This directory contains classes that are shared between various external systems.

  * **__init__.py**

    Module init file.

  * **rpm.py**

    This class contains various method for working with rpm packages.

  * **config.py**

    This class implements centralized app configuration.
