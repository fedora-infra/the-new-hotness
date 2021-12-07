# -*- coding: utf-8 -*-
#
# Copyright © 2021  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
import logging

import requests
from requests.packages.urllib3.util import retry
from anitya_schema.project_messages import ProjectVersionUpdated

from hotness.config import config
from hotness.domain import Package
from hotness.builders import Koji
from hotness.databases import Cache
from hotness.notifiers import Bugzilla as bz_notifier, FedoraMessaging
from hotness.patchers import Bugzilla as bz_patcher
from hotness.validators import MDApi, Pagure, PDC
from hotness.requests import (
    BuildRequest,
    InsertDataRequest,
    NotifyRequest,
    PackageRequest,
    RetrieveDataRequest,
    SubmitPatchRequest,
)
from hotness.use_cases import (
    InsertDataUseCase,
    NotifyUserUseCase,
    PackageScratchBuildUseCase,
    PackageCheckUseCase,
    RetrieveDataUseCase,
    SubmitPatchUseCase,
)

_logger = logging.getLogger(__name__)

# Prefix used for the topic of published messages
PREFIX = "hotness"


class HotnessConsumer(object):
    """
    A fedora-messaging consumer that is the heart of the-new-hotness.

    This consumer subscribes to the following topics:

    * 'org.fedoraproject.prod.buildsys.task.state.change'
      handled by :method:`BugzillaTicketFiler.handle_buildsys_scratch`

    * 'org.release-monitoring.prod.anitya.project.version.update'
      handled by :method:`BugzillaTicketFiler.handle_anitya_version_update`

    * 'org.release-monitoring.prod.anitya.project.map.new'
      handled by :method:`BugzillaTicketFiler.handle_anitya_map_new`

    Attributes:
        short_desc_template (str): Short description template for notifier
        description_template (str): Template for the message content
        distro (str): Distro to watch the updates for
        builder_koji (`Koji`): Koji builder to use for scratch builds
        database_cache (`Cache`): Database that will be used for holding key/value
                                  for build id/bug id
        notifier_bugzilla (`bz_notifier`): Bugzilla notifier for creating and updating
                                           tickets in Bugzilla
        notifier_fedora_messaging (`FedoraMessaging`): Fedora messaging notifier to send
                                                       fedora messages to broker
        patcher_bugzilla (`bz_patcher`): Bugzilla patcher for attaching patcher to tickets
                                         in Bugzilla
        validator_mdapi (`MDApi`): MDApi validator to retrieve the metadata for package
        validator_pagure (`Pagure`): Pagure dist git for retrieval of notification settings
        validator_pdc (`PDC`): PDC validator to check if package is retired
    """

    def __init__(self):
        """
        Consumer initialization.

        It loads the configuration and then initializes all external systems
        use cases will call.
        """
        # Prepare requests session
        requests_session = requests.Session()
        timeout = (
            config["connect_timeout"],
            config["read_timeout"],
        )
        retries = config["requests_retries"]
        retry_conf = retry.Retry(
            total=retries, connect=retries, read=retries, backoff_factor=1
        )
        retry_conf.BACKOFF_MAX = 5
        requests_session.mount(
            "http://", requests.adapters.HTTPAdapter(max_retries=retry_conf)
        )
        requests_session.mount(
            "https://", requests.adapters.HTTPAdapter(max_retries=retry_conf)
        )

        # Initialize attributes
        self.short_desc_template = config["bugzilla"]["short_desc_template"]
        self.description_template = config["bugzilla"]["description_template"]
        self.explanation_url = config["bugzilla"]["explanation_url"]
        self.distro = config["distro"]
        self.repoid = config["repoid"]
        self.hotness_issue_tracker = config["hotness_issue_tracker"]
        self.builder_koji = Koji(
            server_url=config["koji"]["server"],
            web_url=config["koji"]["weburl"],
            kerberos_args={
                "krb_principal": config["koji"]["krb_principal"],
                "krb_keytab": config["koji"]["krb_keytab"],
                "krb_ccache": config["koji"]["krb_ccache"],
                "krb_proxyuser": config["koji"]["krb_proxyuser"],
                "krb_sessionopts": config["koji"]["krb_sessionopts"],
            },
            git_url=config["koji"]["git_url"],
            user_email=tuple(config["koji"]["user_email"]),
            opts=config["koji"]["opts"],
            priority=config["koji"]["priority"],
            target_tag=config["koji"]["target_tag"],
        )
        self.database_cache = Cache()
        self.notifier_bugzilla = bz_notifier(
            server_url=config["bugzilla"]["url"],
            reporter=config["bugzilla"]["reporter"],
            username=config["bugzilla"]["user"],
            password=config["bugzilla"]["password"],
            api_key=config["bugzilla"]["api_key"],
            product=config["bugzilla"]["product"],
            keywords=config["bugzilla"]["keywords"],
            version=config["bugzilla"]["version"],
            status=config["bugzilla"]["bug_status"],
        )
        self.notifier_fedora_messaging = FedoraMessaging(prefix=PREFIX)
        self.patcher_bugzilla = bz_patcher(
            server_url=config["bugzilla"]["url"],
            username=config["bugzilla"]["user"],
            password=config["bugzilla"]["password"],
            api_key=config["bugzilla"]["api_key"],
        )
        self.validator_mdapi = MDApi(
            url=config["mdapi_url"], requests_session=requests_session, timeout=timeout
        )
        self.validator_pagure = Pagure(
            url=config["dist_git_url"],
            requests_session=requests_session,
            timeout=timeout,
        )
        self.validator_pdc = PDC(
            url=config["pdc_url"],
            requests_session=requests_session,
            timeout=timeout,
            branch=config["repoid"],
            package_type="rpm",
        )

    def __call__(self, msg: "fedora_messaging.message.Message") -> None:  # noqa: F821
        """
        Called when a message is received from RabbitMQ queue.

        Params:
            msg: The message we received from the queue.
        """
        topic, body, msg_id = msg.topic, msg.body, msg.id
        _logger.debug("Received %r" % msg_id)

        if topic.endswith("anitya.project.version.update"):
            message = ProjectVersionUpdated(topic=topic, body=body)
            self._handle_anitya_version_update(message)
        elif topic.endswith("buildsys.task.state.change"):
            self._handle_buildsys_scratch(msg)

    def _handle_buildsys_scratch(
        self, message: "fedora_messaging.message.Message"  # noqa: F821
    ) -> None:
        """
        Message handler for build messages.

        This handler checks if we have build in the database, checks if the build
        is in completed state and follow up comment is added to bugzilla issues.

        Topic: `org.fedoraproject.prod.buildsys.task.state.change`

        Params:
          message: Message to process
        """
        msg_id, body = message.id, message.body
        instance = body["instance"]

        if instance != "primary":
            _logger.debug("Ignoring secondary arch task...")
            return

        method = body["method"]

        if method != "build":
            _logger.debug("Ignoring non-build task...")
            return

        task_id = body["info"]["id"]
        # Retrieve the build_id with bz_id from cache
        retrieve_data_request = RetrieveDataRequest(key=str(task_id))
        retrieve_data_cache_use_case = RetrieveDataUseCase(self.database_cache)
        response = retrieve_data_cache_use_case.retrieve(retrieve_data_request)
        if not response:
            _logger.error(
                "Couldn't retrieve value for build %s from cache." % str(task_id)
            )
            return

        if not response.value["value"]:
            _logger.debug(
                "ignoring [%s] as it's not one of our outstanding "
                "builds" % str(task_id)
            )
            return

        bz_id = response.value["value"]

        _logger.info("Handling koji scratch msg %r" % msg_id)

        # see koji.TASK_STATES for all values
        done_states = {
            "CLOSED": "completed",
            "FAILED": "failed",
            "CANCELED": "canceled",
        }

        state = body["new"]
        if state not in done_states:
            _logger.info("The build is not in done state. Dropping message.")
            return

        link = f"http://koji.fedoraproject.org/koji/taskinfo?taskID={task_id}"

        # One last little switch-a-roo for stg
        if ".stg." in message.topic:
            link = f"http://koji.stg.fedoraproject.org/koji/taskinfo?taskID={task_id}"

        owner = body["owner"]
        srpm = body["srpm"]
        target = ""
        if body.get("info", {}).get("request"):
            targets = set()
            for item in body["info"]["request"]:
                if not isinstance(item, (dict, list)) and not item.endswith(".rpm"):
                    targets.add(item)
            if targets:
                target = " for %s" % (self._list_to_series(targets))

        texts_for_state = {
            "FAILED": f"{owner}'s scratch build of {srpm}{target} failed",
            "CLOSED": f"{owner}'s scratch build of {srpm}{target} completed",
            "CANCELED": f"{owner}'s scratch build of {srpm}{target} was canceled",
        }

        text = texts_for_state[state]

        description = text + " " + link

        package_name = "-".join(srpm.split("-")[:-2])
        package_version = srpm.split("-")[-2]

        package = Package(
            name=package_name, version=package_version, distro=self.distro
        )

        notify_request = NotifyRequest(
            package=package, message=description, opts={"bz_id": int(bz_id)}
        )
        notifier_bugzilla_use_case = NotifyUserUseCase(self.notifier_bugzilla)
        notifier_bugzilla_use_case.notify(notify_request)

    def _list_to_series(
        self, items: list, N: int = 3, oxford_comma: bool = True
    ) -> str:
        """Convert a list of things into a comma-separated string.
        >>> list_to_series(['a', 'b', 'c', 'd'])
        'a, b, and 2 others'
        >>> list_to_series(['a', 'b', 'c', 'd'], N=4, oxford_comma=False)
        'a, b, c and d'

        Params:
            items: List of strings to concatenate
            N: Number of items to show in concatenated list
            oxford_comma: Flag for setting if comma should be added before 'and'

        Returns:
            Concatenated string of items separated by comma
        """
        # uniqify items + sort them to have predictable (==testable) ordering
        items = list(sorted(set(items)))

        if len(items) == 1:
            return items[0]

        if len(items) > N:
            items[N - 1 :] = ["%i others" % (len(items) - N + 1)]

        first = ", ".join(items[:-1])

        conjunction = " and "
        if oxford_comma and len(items) > 2:
            conjunction = "," + conjunction

        return first + conjunction + items[-1]

    def _handle_anitya_version_update(self, message: ProjectVersionUpdated) -> None:
        """
        Message handler for new versions found by Anitya.

        This handler deals with new versions found by Anitya. A new upstream
        release can map to several downstream packages, so each package in
        Rawhide (if any) are checked against the newly released version. If
        they are older than the new version, a bug is filed.

        Topic: `org.release-monitoring.prod.anitya.project.version.update`

        Publishes to `update.drop` if:
            * there is no mapping to Fedora
            * any validation fails
            * bug is already in Bugzilla

        Publishes to `update.bug.file` if the bug is filled.

        Params:
            message: Message to process.
        """
        _logger.info("Handling anitya msg %r" % message.id)
        package = None
        fedora_messaging_use_case = NotifyUserUseCase(self.notifier_fedora_messaging)

        # No mapping for the distribution we want to watch, just sent the message and
        # be done with it
        if self.distro not in message.distros:
            _logger.info(
                "No %r mapping for %r. Dropping." % (self.distro, message.project_name)
            )
            package = Package(
                name=message.project_name, version=message.version, distro=""
            )

            opts = {
                "body": {
                    "trigger": {"msg": message.body, "topic": message.topic},
                    "reason": "anitya",
                }
            }

            notify_request = NotifyRequest(
                package=package, message="update.drop", opts=opts
            )
            fedora_messaging_use_case.notify(notify_request)

        for mapping in message.mappings:
            if mapping["distro"] == self.distro:
                package = Package(
                    name=mapping["package_name"],
                    version=message.version,
                    distro=self.distro,
                )

                validation_output = self._validate_package(package)

                # Check if validation failed
                if validation_output["reason"]:
                    opts = {
                        "body": {
                            "trigger": {"msg": message.body, "topic": message.topic},
                            "reason": validation_output["reason"],
                        }
                    }

                    notify_request = NotifyRequest(
                        package=package, message="update.drop", opts=opts
                    )
                    fedora_messaging_use_case.notify(notify_request)
                    return

                scratch_build = validation_output["scratch_build"]

                current_version = validation_output["version"]
                current_release = validation_output["release"]

                # Comment on bugzilla
                bz_id = self._comment_on_bugzilla_with_template(
                    package=package,
                    current_version=current_version,
                    current_release=current_release,
                    project_homepage=message.project_homepage,
                    project_id=message.project_id,
                )

                # Failure happened when communicating with bugzilla
                if bz_id == -1:
                    opts = {
                        "body": {
                            "trigger": {"msg": message.body, "topic": message.topic},
                            "reason": "bugzilla",
                        }
                    }

                    notify_request = NotifyRequest(
                        package=package, message="update.drop", opts=opts
                    )
                    fedora_messaging_use_case.notify(notify_request)
                    return

                # Send Fedora messaging notification
                opts = {
                    "body": {
                        "trigger": {"msg": message.body, "topic": message.topic},
                        "bug": {"bug_id": bz_id},
                        "package": package.name,
                    }
                }

                notify_request = NotifyRequest(
                    package=package, message="update.bug.file", opts=opts
                )
                fedora_messaging_use_case.notify(notify_request)

                # Do a scratch build
                if scratch_build:
                    self._handle_scratch_build(package, bz_id)

    def _validate_package(self, package: Package) -> dict:
        """
        Validates the package with every external validator.
        Used validators:
            * Pagure (dist-git): To retrieve monitoring settings
            * PDC: To check if package is retired or not
            * MDAPI: To check if the package is newer

        Params:
            package: Package to validate

        Returns:
            Dictionary containing output from the validators.
            Example:
            {
                # Monitoring setting for scratch build
                "scratch_build": True,
                # Current version in MDAPI
                "version": "1.0.0",
                # Current release in MDAPI
                "release": 1,
                # Reason for validation failure, empty if no validation successful
                "reason": ""
            }
        """
        output = {"scratch_build": False, "version": "", "release": 0, "reason": ""}
        # Check if we are monitoring the package
        validate_request = PackageRequest(package)
        validate_pagure_use_case = PackageCheckUseCase(self.validator_pagure)
        response = validate_pagure_use_case.validate(validate_request)

        # We encountered an issue during retrieving of monitoring settings
        if not response:
            _logger.error(
                "Couldn't retrieve monitoring settings for %r. Dropping." % package.name
            )
            output["reason"] = "dist-git"
            return output

        # Maintainer doesn't want to monitor the package
        if not response.value["monitoring"]:
            _logger.info("Repo says not to monitor %r. Dropping." % package.name)
            output["reason"] = "monitoring settings"
            return output

        output["scratch_build"] = response.value["scratch_build"]

        # Check if the package is retired in PDC
        validate_pdc_use_case = PackageCheckUseCase(self.validator_pdc)
        response = validate_pdc_use_case.validate(validate_request)

        # We encountered an issue with PDC
        if not response:
            _logger.error(
                "Couldn't retrieve retired information for %r. Dropping." % package.name
            )
            output["reason"] = "pdc"
            return output

        # Package is retired
        if response.value["retired"]:
            _logger.info("Package %r is retired. Dropping." % package.name)
            output["reason"] = "retired"
            return output

        # Check if the version is newer
        validate_mdapi_use_case = PackageCheckUseCase(self.validator_mdapi)
        response = validate_mdapi_use_case.validate(validate_request)

        # We encountered an issue with MDAPI
        if not response:
            _logger.error("Couldn't retrieve metadata for %r. Dropping." % package.name)
            output["reason"] = "mdapi"
            return output

        # Version in upstream is not newer
        if not response.value["newer"]:
            _logger.info(
                "Message doesn't contain newer version of %r. Dropping." % package.name
            )
            output["reason"] = "not newer"
            return output

        output["version"] = response.value["version"]
        output["release"] = response.value["release"]
        return output

    def _comment_on_bugzilla_with_template(
        self,
        package: Package,
        current_version: str,
        current_release: int,
        project_homepage: str,
        project_id: int,
    ) -> int:
        """
        Comment on bugzilla bug using the configured template.

        Params:
            package: Package to comment on.
            current_version: Current version of package in distro
            current_release: Current release of package in distro
            project_homepage: Upstream homepage
            project_id: Project id in Anitya

        Returns:
            Bugzilla ticket id. -1 if failure was encountered.
        """
        bz_id = -1
        # Prepare message for bugzilla
        description = self.description_template % dict(
            latest_upstream=package.version,
            repo_name=self.repoid,
            repo_version=current_version,
            repo_release=current_release,
            url=project_homepage,
            explanation_url=self.explanation_url,
            projectid=project_id,
        )
        notify_request = NotifyRequest(
            package=package,
            message=description,
            opts={
                "bz_short_desc": self.short_desc_template
                % dict(name=package.name, latest_upstream=package.version)
            },
        )
        notifier_bugzilla_use_case = NotifyUserUseCase(self.notifier_bugzilla)
        response = notifier_bugzilla_use_case.notify(notify_request)

        if not response:
            return bz_id

        bz_id = response.value["bz_id"]

        return bz_id

    def _handle_scratch_build(self, package: Package, bz_id: int) -> None:
        """
        Start scratch build in builder, insert build_id to database
        and attach patch to bugzilla bug.

        Params:
            package: Package to start scratch build for
            bz_id: Bugzilla bug id to reference in build
        """
        build_request = BuildRequest(package=package, opts={"bz_id": bz_id})
        build_koji_use_case = PackageScratchBuildUseCase(self.builder_koji)
        response = build_koji_use_case.build(build_request)
        if not response:
            message = "Scratch build failed. Details bellow:\n\n"
            message = message + response.message
            if response.traceback:
                message = message + "\nTraceback:\n{}\n".format(
                    "".join(response.traceback)
                )
            message = message + (
                "If you think this issue is caused by some bug in the-new-hotness, "
                "please report it on the-new-hotness issue tracker: "
                "{}".format(self.hotness_issue_tracker)
            )
            notify_request = NotifyRequest(
                package=package,
                message=message,
                opts={"bz_id": bz_id},
            )
            notifier_bugzilla_use_case = NotifyUserUseCase(self.notifier_bugzilla)
            notifier_bugzilla_use_case.notify(notify_request)

            # Insert the build_id to cache if available
            if response.use_case_value and "build_id" in response.use_case_value:
                build_id = response.use_case_value["build_id"]
                insert_data_request = InsertDataRequest(
                    key=str(build_id), value=str(bz_id)
                )
                insert_data_cache_use_case = InsertDataUseCase(self.database_cache)
                response = insert_data_cache_use_case.insert(insert_data_request)
            return

        build_id = response.value["build_id"]
        patch = response.value["patch"]
        patch_filename = response.value["patch_filename"]
        message = response.value["message"]
        if message:
            notify_request = NotifyRequest(
                package=package,
                message=message,
                opts={"bz_id": bz_id},
            )
            notifier_bugzilla_use_case = NotifyUserUseCase(self.notifier_bugzilla)
            notifier_bugzilla_use_case.notify(notify_request)

        # Save the build_id with bz_id to cache
        insert_data_request = InsertDataRequest(key=str(build_id), value=str(bz_id))
        insert_data_cache_use_case = InsertDataUseCase(self.database_cache)
        response = insert_data_cache_use_case.insert(insert_data_request)

        # Attach patch to Bugzilla
        submit_patch_request = SubmitPatchRequest(
            package=package,
            patch=patch,
            opts={"bz_id": bz_id, "patch_filename": patch_filename},
        )
        submit_patch_bugzilla_use_case = SubmitPatchUseCase(self.patcher_bugzilla)
        response = submit_patch_bugzilla_use_case.submit_patch(submit_patch_request)
