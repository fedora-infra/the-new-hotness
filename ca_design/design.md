# Clean architecture design
This design document describes files and directories structure of the-new-hotness based on the requirements.md document using clean architecture design. The document will be split to three parts according to clean architecture design.

Main source file will be `hotness.py` and will consume and publish messages using Fedora messaging.

## Entities
Inner definitions of objects we will work with. This is the core of the whole application. Bellow is the directory structure.

### domain
Directory where every domain related source is stored.

#### __init__.py
Module init file.

#### package.py
Internal definition of package. It should be easily converted to json.

## Use cases
Use cases corresponds to requirements. This layer will define what the application can do. Bellow is the directory structure for this layer. This layer also contains abstract classes which will be inherited by external systems and response/requests definition with any exceptions.

### use_cases
Directory containing every use_case for this application.

#### package_check_use_case.py
This class will do various checks on the package. This will be done by calling abstract classes for external systems. Reports any error using response object.

#### package_scratch_build_use_case.py
This class will start the scratch build and does any error handling when the start of the build fails. 

#### notify_user_use_case.py
This class will notify the user and does any error handling related to notifier. 

#### submit_patch_use_case.py
This class will submit patch using provided patcher. In current situation this will be bugzilla, in future this could be packit. 

### validators 
Directory containing every external system wrapper that is called to check something. In this layer I will only describe the abstract class, which will be inherited by other systems.

#### __init__.py
Module init file.

#### validator.py
Abstract class that needs to be inherited by any external system that is used to validate package. This will define the methods that will be called by `package_check_use_case` class.

### builders
Directory containing any builder. In this layer I will only describe abstract class, which will be then inherited in upper layer.

#### __init__.py
Module init file.

#### builder.py
Abstract class that needs to be inherited by any external system that is called to start build. This will define methods that will be called by `package_scratch_build_use_case` class.

### notifiers
Directory containing external systems used to notify users. In this layer I will only describe abstract class, which will be then inherited in upper layer.

#### __init__.py
Module init file.

#### notifier.py
Abstract class that needs to be inherited by any external system that is called to notify user. This will define methods that will be called by `notify_user_use_case` class.

### patchers
Directory containing external systems used to submit patch created by the-new-hotness. In this layer I will only describe abstract class, which will be then inherited in upper layer.

#### __init__.py
Module init file.

#### patcher.py
Abstract class that needs to be inherited by any external system that is called to submit patch. This will define methods that will be called by `submit_patch_use_case` class.

### request_objects
This directory contains every request object which is passed to use cases.

#### __init__.py
Module init file.

#### package_request_object.py
Request passed to `package_check_use_case` and `package_scratch_build_use_case`. This request object contains package object.

#### notify_request_object.py
Request passed to `notify_user_use_case`. This request object is inherited from `package_request_object` and provides message (String) as additional attribute.

#### submit_patch_request_object.py
Request passed to `submit_patch_use_case`. This request object is inherited from `package_request_object` and provides path to file (String) and description as additional attributes.

### response_objects
This directory contains every response object which could be returned by use cases.

#### __init__.py
Module init file.

#### response.py
Abstract class which is inherited by other responses. This class also defines constants for any response code. Defines `__bool__` method.

#### response_success.py
This class is inherited from `response.py` and is returned when use case finishes successfully. Implements `__bool__` method that returns `True` and value attribute, which contains return value from use case if any.

#### response_failure.py
This class is inherited from `response.py` and is returned when use case finishes with failure. Implements `__bool__` method that returns `False`, value property contains type of error and exception with error message.

### exceptions
This directory contains any specific exception that could be thrown by any wrapper for external system.

#### __init__.py
Module init file.

#### html_exception.py
This exception should be thrown when HTML request is unsuccessful and returns anything else than 200.

## External systems
This is the outer layer of clean architecture and contains wrappers that are calling external systems and any helper class used by the wrappers. Wrappers will inherit abstract class defined in use cases layer.

### validators
Directory containing every external system contacted to check validity of package. 

#### mdapi.py
Class that is checking if the package is newer or not than the package currently available in Fedora using mdapi system. Inherits from `validator.py`. 

#### pdc.py
Class that is checking if the package is retired or not in Fedora using PDC API. Inherits from `validator.py`. 

#### pagure.py
Class that is checking if the package exists in Fedora and retrieves the notification settings from Pagure. Inherits from `validator.py`. Exists check is only done once and than saved in the cache using `cache.py`. 

### builders
Directory containing any builder.

#### koji.py
Class that is used to prepare and start build in Koji. Inherits from `builder.py`.

### notifiers
Directory containing external systems used to notify users.

#### bugzilla.py
This class contains every method that is needed to create/update issue in bugzilla. Inherits from `notifier.py`.

### patchers
Directory containing external systems used to submit patch created by the-new-hotness.

#### bugzilla.py
This class contains every method that is needed to attach patch to existing issue in bugzilla. Inherits from `patcher.py`.

### common
This directory contains classes that are shared between various external systems.

#### __init__.py
Module init file.

#### rpm.py
This class contains various method for working with rpm packages.

### storage
This directory contains classes representing storage.

#### __init__.py
Module init file.

#### cache.py
Class representing cache used by various external systems.
