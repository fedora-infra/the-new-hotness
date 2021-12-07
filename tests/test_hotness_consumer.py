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
import json
import os
import traceback
from unittest import mock

from fedora_messaging.message import Message

from hotness.hotness_consumer import HotnessConsumer
from hotness.domain import Package
from hotness.exceptions import BuilderException, DownloadException

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures/"))


def create_message(topic: str, name: str) -> Message:
    """
    Prepare message for testing. Reads the body of message
    from `FIXTURES_DIR` file specified by `name`` and creates
    `Message` object with specified `topic`.

    Params:
        topic: Topic of the created message
        name: Name of the file to read message body from

    Returns:
        Message for testing.
    """
    fixture = os.path.join(FIXTURES_DIR, topic, name + ".json")
    with open(fixture, "r") as fp:
        body = json.load(fp)

    message = Message(topic=topic, body=body)

    return message


class TestHotnessConsumerInit:
    """
    Test class for `hotness.hotness_consumer.HotnessConsumer.__init__`.
    """

    @mock.patch("hotness.hotness_consumer.Koji")
    @mock.patch("hotness.hotness_consumer.Cache")
    @mock.patch("hotness.hotness_consumer.bz_notifier")
    @mock.patch("hotness.hotness_consumer.FedoraMessaging")
    @mock.patch("hotness.hotness_consumer.bz_patcher")
    @mock.patch("hotness.hotness_consumer.MDApi")
    @mock.patch("hotness.hotness_consumer.Pagure")
    @mock.patch("hotness.hotness_consumer.PDC")
    def test_init(
        self,
        mock_pdc_new,
        mock_pagure_new,
        mock_mdapi_new,
        mock_bz_patcher_new,
        mock_fm_new,
        mock_bz_notifier_new,
        mock_cache_new,
        mock_koji_new,
    ):
        """
        Assert that initialization works fine.
        """
        mock_koji = mock.MagicMock()
        mock_koji_new.return_value = mock_koji
        mock_cache = mock.MagicMock()
        mock_cache_new.return_value = mock_cache
        mock_bugzilla_notifier = mock.Mock()
        mock_bz_notifier_new.return_value = mock_bugzilla_notifier
        mock_fedora_messaging = mock.Mock()
        mock_fm_new.return_value = mock_fedora_messaging
        mock_bugzilla_patcher = mock.Mock()
        mock_bz_patcher_new.return_value = mock_bugzilla_patcher
        mock_mdapi = mock.Mock()
        mock_mdapi_new.return_value = mock_mdapi
        mock_pagure = mock.Mock()
        mock_pagure_new.return_value = mock_pagure
        mock_pdc = mock.Mock()
        mock_pdc_new.return_value = mock_pdc

        consumer = HotnessConsumer()

        assert (
            consumer.short_desc_template == "%(name)s-%(latest_upstream)s is available"
        )
        assert (
            consumer.description_template
            == """
Latest upstream release: %(latest_upstream)s

Current version/release in %(repo_name)s: %(repo_version)s-%(repo_release)s

URL: %(url)s


    Please consult the package updates policy before you
issue an update to a stable branch:
    https://docs.fedoraproject.org/en-US/fesco/Updates_Policy


More information about the service that created this bug can be found at:

    %(explanation_url)s


    Please keep in mind that with any upstream change, there may also be packaging
    changes that need to be made. Specifically, please remember that it is your
    responsibility to review the new version to ensure that the licensing is still
    correct and that no non-free or legally problematic items have been added
    upstream.

Based on the information from anitya: https://release-monitoring.org/project/%(projectid)s/
"""
        )
        assert (
            consumer.explanation_url
            == "https://fedoraproject.org/wiki/upstream_release_monitoring"
        )
        assert consumer.distro == "Fedora"
        assert consumer.repoid == "rawhide"
        assert consumer.builder_koji == mock_koji
        assert consumer.database_cache == mock_cache
        assert consumer.notifier_bugzilla == mock_bugzilla_notifier
        assert consumer.notifier_fedora_messaging == mock_fedora_messaging
        assert consumer.patcher_bugzilla == mock_bugzilla_patcher
        assert consumer.validator_mdapi == mock_mdapi
        assert consumer.validator_pagure == mock_pagure
        assert consumer.validator_pdc == mock_pdc

        mock_koji_new.assert_called_with(
            server_url="https://koji.fedoraproject.org/kojihub",
            web_url="https://koji.fedoraproject.org/koji",
            kerberos_args={
                "krb_principal": "",
                "krb_keytab": "",
                "krb_ccache": "",
                "krb_proxyuser": "",
                "krb_sessionopts": dict(timeout=3600, krb_rdns=False),
            },
            git_url="https://src.fedoraproject.org/cgit/rpms/{package}.git",
            user_email=(
                "Upstream Monitor",
                "<upstream-release-monitoring@fedoraproject.org>",
            ),
            opts=dict(scratch=True),
            priority=30,
            target_tag="rawhide",
        )

        mock_cache_new.assert_called_once()

        mock_bz_notifier_new.assert_called_with(
            server_url="https://partner-bugzilla.redhat.com",
            reporter="Upstream Release Monitoring",
            username=None,
            password=None,
            api_key="",
            product="Fedora",
            keywords="FutureFeature, Triaged",
            version="rawhide",
            status="NEW",
        )

        mock_fm_new.assert_called_with(prefix="hotness")

        mock_bz_patcher_new.assert_called_with(
            server_url="https://partner-bugzilla.redhat.com",
            username=None,
            password=None,
            api_key="",
        )

        mock_mdapi_new.assert_called_with(
            url="https://apps.fedoraproject.org/mdapi",
            requests_session=mock.ANY,
            timeout=(15, 15),
        )

        mock_pagure_new.assert_called_with(
            url="https://src.fedoraproject.org",
            requests_session=mock.ANY,
            timeout=(15, 15),
        )

        mock_pdc_new.assert_called_with(
            url="https://pdc.fedoraproject.org",
            requests_session=mock.ANY,
            timeout=(15, 15),
            branch="rawhide",
            package_type="rpm",
        )


class TestHotnessConsumerCall:
    """
    Test class for `hotness.hotness_consumer.HotnessConsumer.__call__`.
    """

    @mock.patch("hotness.hotness_consumer.Koji")
    @mock.patch("hotness.hotness_consumer.Cache")
    @mock.patch("hotness.hotness_consumer.bz_notifier")
    @mock.patch("hotness.hotness_consumer.FedoraMessaging")
    @mock.patch("hotness.hotness_consumer.bz_patcher")
    @mock.patch("hotness.hotness_consumer.MDApi")
    @mock.patch("hotness.hotness_consumer.Pagure")
    @mock.patch("hotness.hotness_consumer.PDC")
    def setup(
        self,
        mock_pdc_new,
        mock_pagure_new,
        mock_mdapi_new,
        mock_bz_patcher_new,
        mock_fm_new,
        mock_bz_notifier_new,
        mock_cache_new,
        mock_koji_new,
    ):
        """
        Create hotness consumer for tests.
        It is accessible as `self.consumer`.
        """
        mock_koji = mock.MagicMock()
        mock_koji_new.return_value = mock_koji
        mock_cache = mock.MagicMock()
        mock_cache_new.return_value = mock_cache
        mock_bugzilla_notifier = mock.Mock()
        mock_bz_notifier_new.return_value = mock_bugzilla_notifier
        mock_fedora_messaging = mock.Mock()
        mock_fm_new.return_value = mock_fedora_messaging
        mock_bugzilla_patcher = mock.Mock()
        mock_bz_patcher_new.return_value = mock_bugzilla_patcher
        mock_mdapi = mock.Mock()
        mock_mdapi_new.return_value = mock_mdapi
        mock_pagure = mock.Mock()
        mock_pagure_new.return_value = mock_pagure
        mock_pdc = mock.Mock()
        mock_pdc_new.return_value = mock_pdc

        self.consumer = HotnessConsumer()

    #
    #  anitya.project.version.update topic
    #
    def test_call_anitya_update_no_distro_mapping(self):
        """
        Assert that message is handled correctly when there is no distribution mapping
        in update message.
        """
        message = create_message("anitya.project.version.update", "no_mapping")
        self.consumer.__call__(message)

        exp_package = Package(name="pg-semver", version="0.17.0", distro="")

        exp_opts = {
            "body": {
                "trigger": {"msg": message.body, "topic": message.topic},
                "reason": "anitya",
            }
        }

        self.consumer.notifier_fedora_messaging.notify.assert_called_with(
            exp_package, "update.drop", exp_opts
        )

    def test_call_anitya_update(self):
        """
        Assert that update message is handled correctly.
        """
        message = create_message("anitya.project.version.update", "fedora_mapping")
        self.consumer.validator_pagure.validate.return_value = {
            "monitoring": True,
            "scratch_build": True,
        }
        self.consumer.validator_pdc.validate.return_value = {
            "retired": False,
            "count": 1,
        }
        self.consumer.validator_mdapi.validate.return_value = {
            "newer": True,
            "version": "0.16.0",
            "release": 1,
        }
        self.consumer.notifier_bugzilla.notify.return_value = {"bz_id": 100}
        self.consumer.builder_koji.build.return_value = {
            "build_id": 1000,
            "patch": "Let's patch this heresy!",
            "patch_filename": "patch_heresy.0001",
            "message": "",
        }

        self.consumer.__call__(message)

        package = Package(name="flatpak", version="1.0.4", distro="Fedora")

        self.consumer.validator_pagure.validate.assert_called_with(package)
        self.consumer.validator_pdc.validate.assert_called_with(package)
        self.consumer.validator_mdapi.validate.assert_called_with(package)
        self.consumer.notifier_bugzilla.notify.assert_called_with(
            package,
            self.consumer.description_template
            % dict(
                latest_upstream=package.version,
                repo_name=self.consumer.repoid,
                repo_version="0.16.0",
                repo_release=1,
                url=message.body["project"]["homepage"],
                explanation_url=self.consumer.explanation_url,
                projectid=message.body["project"]["id"],
            ),
            {"bz_short_desc": "flatpak-1.0.4 is available"},
        )
        self.consumer.builder_koji.build.assert_called_with(package, {"bz_id": 100})
        self.consumer.database_cache.insert.assert_called_with("1000", "100")
        self.consumer.patcher_bugzilla.submit_patch.assert_called_with(
            package,
            "Let's patch this heresy!",
            {"bz_id": 100, "patch_filename": "patch_heresy.0001"},
        )

        exp_opts = {
            "body": {
                "trigger": {"msg": message.body, "topic": message.topic},
                "bug": {"bug_id": 100},
                "package": package.name,
            }
        }

        self.consumer.notifier_fedora_messaging.notify.assert_called_with(
            package, "update.bug.file", exp_opts
        )

    def test_call_anitya_update_scratch_build_message(self):
        """
        Assert that update message and bugzilla ticket is updated correctly when builder
        returns additional message.
        """
        message = create_message("anitya.project.version.update", "fedora_mapping")
        self.consumer.validator_pagure.validate.return_value = {
            "monitoring": True,
            "scratch_build": True,
        }
        self.consumer.validator_pdc.validate.return_value = {
            "retired": False,
            "count": 1,
        }
        self.consumer.validator_mdapi.validate.return_value = {
            "newer": True,
            "version": "0.16.0",
            "release": 1,
        }
        self.consumer.notifier_bugzilla.notify.return_value = {"bz_id": 100}
        self.consumer.builder_koji.build.return_value = {
            "build_id": 1000,
            "patch": "Let's patch this heresy!",
            "patch_filename": "patch_heresy.0001",
            "message": "Emperor protects!",
        }

        self.consumer.__call__(message)

        package = Package(name="flatpak", version="1.0.4", distro="Fedora")

        self.consumer.validator_pagure.validate.assert_called_with(package)
        self.consumer.validator_pdc.validate.assert_called_with(package)
        self.consumer.validator_mdapi.validate.assert_called_with(package)
        self.consumer.notifier_bugzilla.notify.assert_has_calls(
            [
                mock.call(
                    package,
                    self.consumer.description_template
                    % dict(
                        latest_upstream=package.version,
                        repo_name=self.consumer.repoid,
                        repo_version="0.16.0",
                        repo_release=1,
                        url=message.body["project"]["homepage"],
                        explanation_url=self.consumer.explanation_url,
                        projectid=message.body["project"]["id"],
                    ),
                    {"bz_short_desc": "flatpak-1.0.4 is available"},
                ),
                mock.call(
                    package,
                    "Emperor protects!",
                    {"bz_id": 100},
                ),
            ]
        )
        self.consumer.builder_koji.build.assert_called_with(package, {"bz_id": 100})
        self.consumer.database_cache.insert.assert_called_with("1000", "100")
        self.consumer.patcher_bugzilla.submit_patch.assert_called_with(
            package,
            "Let's patch this heresy!",
            {"bz_id": 100, "patch_filename": "patch_heresy.0001"},
        )

        exp_opts = {
            "body": {
                "trigger": {"msg": message.body, "topic": message.topic},
                "bug": {"bug_id": 100},
                "package": package.name,
            }
        }

        self.consumer.notifier_fedora_messaging.notify.assert_called_with(
            package, "update.bug.file", exp_opts
        )

    def test_call_anitya_update_scratch_build_failure(self):
        """
        Assert that update message is handled correctly when scratch build fails to start.
        """
        message = create_message("anitya.project.version.update", "fedora_mapping")
        self.consumer.validator_pagure.validate.return_value = {
            "monitoring": True,
            "scratch_build": True,
        }
        self.consumer.validator_pdc.validate.return_value = {
            "retired": False,
            "count": 1,
        }
        self.consumer.validator_mdapi.validate.return_value = {
            "newer": True,
            "version": "0.16.0",
            "release": 1,
        }
        builder_exception = BuilderException(
            "This is heresy!",
            std_out="This is a standard output",
            std_err="This is an error output",
        )
        self.consumer.notifier_bugzilla.notify.return_value = {"bz_id": 100}
        self.consumer.builder_koji.build.side_effect = builder_exception
        self.consumer.__call__(message)

        package = Package(name="flatpak", version="1.0.4", distro="Fedora")

        self.consumer.validator_pagure.validate.assert_called_with(package)
        self.consumer.validator_pdc.validate.assert_called_with(package)
        self.consumer.validator_mdapi.validate.assert_called_with(package)
        self.consumer.notifier_bugzilla.notify.assert_has_calls(
            [
                mock.call(
                    package,
                    self.consumer.description_template
                    % dict(
                        latest_upstream=package.version,
                        repo_name=self.consumer.repoid,
                        repo_version="0.16.0",
                        repo_release=1,
                        url=message.body["project"]["homepage"],
                        explanation_url=self.consumer.explanation_url,
                        projectid=message.body["project"]["id"],
                    ),
                    {"bz_short_desc": "flatpak-1.0.4 is available"},
                ),
                mock.call(
                    package,
                    (
                        "Scratch build failed. Details bellow:\n\n"
                        "BuilderException: {}\n"
                        "Traceback:\n"
                        "{}\n"
                        "If you think this issue is caused by some bug in the-new-hotness, "
                        "please report it on the-new-hotness issue tracker: "
                        "{}"
                    ).format(
                        str(builder_exception),
                        "".join(traceback.format_tb(builder_exception.__traceback__)),
                        self.consumer.hotness_issue_tracker,
                    ),
                    {"bz_id": 100},
                ),
            ]
        )
        self.consumer.builder_koji.build.assert_called_with(package, {"bz_id": 100})

        exp_opts = {
            "body": {
                "trigger": {"msg": message.body, "topic": message.topic},
                "bug": {"bug_id": 100},
                "package": package.name,
            }
        }

        self.consumer.notifier_fedora_messaging.notify.assert_called_with(
            package, "update.bug.file", exp_opts
        )

    def test_call_anitya_update_scratch_build_download_failure(self):
        """
        Assert that update message is handled correctly when scratch build is started,
        but download of sources fails.
        """
        message = create_message("anitya.project.version.update", "fedora_mapping")
        self.consumer.validator_pagure.validate.return_value = {
            "monitoring": True,
            "scratch_build": True,
        }
        self.consumer.validator_pdc.validate.return_value = {
            "retired": False,
            "count": 1,
        }
        self.consumer.validator_mdapi.validate.return_value = {
            "newer": True,
            "version": "0.16.0",
            "release": 1,
        }
        download_exception = DownloadException(
            "This is heresy!",
        )
        self.consumer.notifier_bugzilla.notify.return_value = {"bz_id": 100}
        self.consumer.builder_koji.build.side_effect = download_exception
        self.consumer.__call__(message)

        package = Package(name="flatpak", version="1.0.4", distro="Fedora")

        self.consumer.validator_pagure.validate.assert_called_with(package)
        self.consumer.validator_pdc.validate.assert_called_with(package)
        self.consumer.validator_mdapi.validate.assert_called_with(package)
        self.consumer.notifier_bugzilla.notify.assert_has_calls(
            [
                mock.call(
                    package,
                    self.consumer.description_template
                    % dict(
                        latest_upstream=package.version,
                        repo_name=self.consumer.repoid,
                        repo_version="0.16.0",
                        repo_release=1,
                        url=message.body["project"]["homepage"],
                        explanation_url=self.consumer.explanation_url,
                        projectid=message.body["project"]["id"],
                    ),
                    {"bz_short_desc": "flatpak-1.0.4 is available"},
                ),
                mock.call(
                    package,
                    (
                        "Scratch build failed. Details bellow:\n\n"
                        "DownloadException: {}\n"
                        "Traceback:\n"
                        "{}\n"
                        "If you think this issue is caused by some bug in the-new-hotness, "
                        "please report it on the-new-hotness issue tracker: "
                        "{}"
                    ).format(
                        str(download_exception),
                        "".join(traceback.format_tb(download_exception.__traceback__)),
                        self.consumer.hotness_issue_tracker,
                    ),
                    {"bz_id": 100},
                ),
            ]
        )
        self.consumer.builder_koji.build.assert_called_with(package, {"bz_id": 100})

    def test_call_anitya_update_scratch_build_post_build_failure(self):
        """
        Assert that update message is handled correctly when scratch build is started,
        but there is failure in post build process.
        """
        message = create_message("anitya.project.version.update", "fedora_mapping")
        self.consumer.validator_pagure.validate.return_value = {
            "monitoring": True,
            "scratch_build": True,
        }
        self.consumer.validator_pdc.validate.return_value = {
            "retired": False,
            "count": 1,
        }
        self.consumer.validator_mdapi.validate.return_value = {
            "newer": True,
            "version": "0.16.0",
            "release": 1,
        }
        builder_exception = BuilderException(
            "This is heresy!",
            std_out="This is a standard output",
            std_err="This is an error output",
            value={"build_id": 1000},
        )
        self.consumer.notifier_bugzilla.notify.return_value = {"bz_id": 100}
        self.consumer.builder_koji.build.side_effect = builder_exception
        self.consumer.__call__(message)

        package = Package(name="flatpak", version="1.0.4", distro="Fedora")

        self.consumer.validator_pagure.validate.assert_called_with(package)
        self.consumer.validator_pdc.validate.assert_called_with(package)
        self.consumer.validator_mdapi.validate.assert_called_with(package)
        self.consumer.notifier_bugzilla.notify.assert_has_calls(
            [
                mock.call(
                    package,
                    self.consumer.description_template
                    % dict(
                        latest_upstream=package.version,
                        repo_name=self.consumer.repoid,
                        repo_version="0.16.0",
                        repo_release=1,
                        url=message.body["project"]["homepage"],
                        explanation_url=self.consumer.explanation_url,
                        projectid=message.body["project"]["id"],
                    ),
                    {"bz_short_desc": "flatpak-1.0.4 is available"},
                ),
                mock.call(
                    package,
                    (
                        "Scratch build failed. Details bellow:\n\n"
                        "BuilderException: {}\n"
                        "Traceback:\n"
                        "{}\n"
                        "If you think this issue is caused by some bug in the-new-hotness, "
                        "please report it on the-new-hotness issue tracker: "
                        "{}"
                    ).format(
                        str(builder_exception),
                        "".join(traceback.format_tb(builder_exception.__traceback__)),
                        self.consumer.hotness_issue_tracker,
                    ),
                    {"bz_id": 100},
                ),
            ]
        )
        self.consumer.builder_koji.build.assert_called_with(package, {"bz_id": 100})

        exp_opts = {
            "body": {
                "trigger": {"msg": message.body, "topic": message.topic},
                "bug": {"bug_id": 100},
                "package": package.name,
            }
        }

        self.consumer.notifier_fedora_messaging.notify.assert_called_with(
            package, "update.bug.file", exp_opts
        )
        self.consumer.database_cache.insert.assert_called_with("1000", "100")

    def test_call_anitya_update_no_monitoring(self):
        """
        Assert that update message is handled correctly when monitoring is not set.
        """
        message = create_message("anitya.project.version.update", "fedora_mapping")
        self.consumer.validator_pagure.validate.return_value = {
            "monitoring": False,
            "scratch_build": True,
        }

        self.consumer.__call__(message)

        package = Package(name="flatpak", version="1.0.4", distro="Fedora")

        self.consumer.validator_pagure.validate.assert_called_with(package)

        exp_opts = {
            "body": {
                "trigger": {"msg": message.body, "topic": message.topic},
                "reason": "monitoring settings",
            }
        }

        self.consumer.notifier_fedora_messaging.notify.assert_called_with(
            package, "update.drop", exp_opts
        )

    def test_call_anitya_update_no_scratch_build(self):
        """
        Assert that update message is handled correctly, when scratch build
        is not required.
        """
        message = create_message("anitya.project.version.update", "fedora_mapping")
        self.consumer.validator_pagure.validate.return_value = {
            "monitoring": True,
            "scratch_build": False,
        }
        self.consumer.validator_pdc.validate.return_value = {
            "retired": False,
            "count": 1,
        }
        self.consumer.validator_mdapi.validate.return_value = {
            "newer": True,
            "version": "0.16.0",
            "release": 1,
        }
        self.consumer.notifier_bugzilla.notify.return_value = {"bz_id": 100}

        self.consumer.__call__(message)

        package = Package(name="flatpak", version="1.0.4", distro="Fedora")

        self.consumer.validator_pagure.validate.assert_called_with(package)
        self.consumer.validator_pdc.validate.assert_called_with(package)
        self.consumer.validator_mdapi.validate.assert_called_with(package)
        self.consumer.notifier_bugzilla.notify.assert_called_with(
            package,
            self.consumer.description_template
            % dict(
                latest_upstream=package.version,
                repo_name=self.consumer.repoid,
                repo_version="0.16.0",
                repo_release=1,
                url=message.body["project"]["homepage"],
                explanation_url=self.consumer.explanation_url,
                projectid=message.body["project"]["id"],
            ),
            {"bz_short_desc": "flatpak-1.0.4 is available"},
        )
        self.consumer.builder_koji.build.assert_not_called()

        exp_opts = {
            "body": {
                "trigger": {"msg": message.body, "topic": message.topic},
                "bug": {"bug_id": 100},
                "package": package.name,
            }
        }

        self.consumer.notifier_fedora_messaging.notify.assert_called_with(
            package, "update.bug.file", exp_opts
        )

    def test_call_anitya_update_pagure_exception(self):
        """
        Assert that update message is handled correctly when pagure validator fails.
        """
        message = create_message("anitya.project.version.update", "fedora_mapping")
        self.consumer.validator_pagure.validate.side_effect = Exception()

        self.consumer.__call__(message)

        package = Package(name="flatpak", version="1.0.4", distro="Fedora")

        self.consumer.validator_pagure.validate.assert_called_with(package)

        exp_opts = {
            "body": {
                "trigger": {"msg": message.body, "topic": message.topic},
                "reason": "dist-git",
            }
        }

        self.consumer.notifier_fedora_messaging.notify.assert_called_with(
            package, "update.drop", exp_opts
        )

    def test_call_anitya_update_retired(self):
        """
        Assert that update message is handled correctly, when package is retired.
        """
        message = create_message("anitya.project.version.update", "fedora_mapping")
        self.consumer.validator_pagure.validate.return_value = {
            "monitoring": True,
            "scratch_build": False,
        }
        self.consumer.validator_pdc.validate.return_value = {
            "retired": True,
            "count": 0,
        }

        self.consumer.__call__(message)

        package = Package(name="flatpak", version="1.0.4", distro="Fedora")

        self.consumer.validator_pagure.validate.assert_called_with(package)
        self.consumer.validator_pdc.validate.assert_called_with(package)

        exp_opts = {
            "body": {
                "trigger": {"msg": message.body, "topic": message.topic},
                "reason": "retired",
            }
        }

        self.consumer.notifier_fedora_messaging.notify.assert_called_with(
            package, "update.drop", exp_opts
        )

    def test_call_anitya_update_pdc_exception(self):
        """
        Assert that update message is handled correctly, when pdc raises exception.
        """
        message = create_message("anitya.project.version.update", "fedora_mapping")
        self.consumer.validator_pagure.validate.return_value = {
            "monitoring": True,
            "scratch_build": False,
        }
        self.consumer.validator_pdc.validate.side_effect = Exception()

        self.consumer.__call__(message)

        package = Package(name="flatpak", version="1.0.4", distro="Fedora")

        self.consumer.validator_pagure.validate.assert_called_with(package)
        self.consumer.validator_pdc.validate.assert_called_with(package)

        exp_opts = {
            "body": {
                "trigger": {"msg": message.body, "topic": message.topic},
                "reason": "pdc",
            }
        }

        self.consumer.notifier_fedora_messaging.notify.assert_called_with(
            package, "update.drop", exp_opts
        )

    def test_call_anitya_update_old_version(self):
        """
        Assert that update message is handled correctly if the upstream version is
        already in mdapi.
        """
        message = create_message("anitya.project.version.update", "fedora_mapping")
        self.consumer.validator_pagure.validate.return_value = {
            "monitoring": True,
            "scratch_build": True,
        }
        self.consumer.validator_pdc.validate.return_value = {
            "retired": False,
            "count": 1,
        }
        self.consumer.validator_mdapi.validate.return_value = {
            "newer": False,
            "version": "1.0.4",
            "release": 1,
        }

        self.consumer.__call__(message)

        package = Package(name="flatpak", version="1.0.4", distro="Fedora")

        self.consumer.validator_pagure.validate.assert_called_with(package)
        self.consumer.validator_pdc.validate.assert_called_with(package)
        self.consumer.validator_mdapi.validate.assert_called_with(package)

        exp_opts = {
            "body": {
                "trigger": {"msg": message.body, "topic": message.topic},
                "reason": "not newer",
            }
        }

        self.consumer.notifier_fedora_messaging.notify.assert_called_with(
            package, "update.drop", exp_opts
        )

    def test_call_anitya_update_mdapi_exception(self):
        """
        Assert that update message is handled correctly if MDAPI raises exception.
        """
        message = create_message("anitya.project.version.update", "fedora_mapping")
        self.consumer.validator_pagure.validate.return_value = {
            "monitoring": True,
            "scratch_build": True,
        }
        self.consumer.validator_pdc.validate.return_value = {
            "retired": False,
            "count": 1,
        }
        self.consumer.validator_mdapi.validate.side_effect = Exception()

        self.consumer.__call__(message)

        package = Package(name="flatpak", version="1.0.4", distro="Fedora")

        self.consumer.validator_pagure.validate.assert_called_with(package)
        self.consumer.validator_pdc.validate.assert_called_with(package)
        self.consumer.validator_mdapi.validate.assert_called_with(package)

        exp_opts = {
            "body": {
                "trigger": {"msg": message.body, "topic": message.topic},
                "reason": "mdapi",
            }
        }

        self.consumer.notifier_fedora_messaging.notify.assert_called_with(
            package, "update.drop", exp_opts
        )

    def test_call_anitya_update_bugzilla_exception(self):
        """
        Assert that update message is handled correctly, when bugzilla raises exception.
        """
        message = create_message("anitya.project.version.update", "fedora_mapping")
        self.consumer.validator_pagure.validate.return_value = {
            "monitoring": True,
            "scratch_build": True,
        }
        self.consumer.validator_pdc.validate.return_value = {
            "retired": False,
            "count": 1,
        }
        self.consumer.validator_mdapi.validate.return_value = {
            "newer": True,
            "version": "0.16.0",
            "release": 1,
        }
        self.consumer.notifier_bugzilla.notify.side_effect = Exception()

        self.consumer.__call__(message)

        package = Package(name="flatpak", version="1.0.4", distro="Fedora")

        self.consumer.validator_pagure.validate.assert_called_with(package)
        self.consumer.validator_pdc.validate.assert_called_with(package)
        self.consumer.validator_mdapi.validate.assert_called_with(package)
        self.consumer.notifier_bugzilla.notify.assert_called_with(
            package,
            self.consumer.description_template
            % dict(
                latest_upstream=package.version,
                repo_name=self.consumer.repoid,
                repo_version="0.16.0",
                repo_release=1,
                url=message.body["project"]["homepage"],
                explanation_url=self.consumer.explanation_url,
                projectid=message.body["project"]["id"],
            ),
            {"bz_short_desc": "flatpak-1.0.4 is available"},
        )

        exp_opts = {
            "body": {
                "trigger": {"msg": message.body, "topic": message.topic},
                "reason": "bugzilla",
            }
        }

        self.consumer.notifier_fedora_messaging.notify.assert_called_with(
            package, "update.drop", exp_opts
        )

    #
    #  buildsys.task.state.change topic
    #

    def test_call_buildsys_task_build_completed(self):
        """
        Assert that message is handled correctly when the build is completed.
        """
        message = create_message("buildsys.task.state.change", "build_completed")

        self.consumer.database_cache.retrieve.return_value = {
            "key": "90100954",
            "value": "100",
        }

        self.consumer.notifier_bugzilla.notify.return_value = {"bz_id": "100"}

        self.consumer.__call__(message)

        self.consumer.database_cache.retrieve.assert_called_with("90100954")

        package = Package(name="globus-callout", version="4.0", distro="Fedora")

        self.consumer.notifier_bugzilla.notify.assert_called_with(
            package,
            (
                "koschei's scratch build of globus-callout-4.0-1.fc29.src.rpm for f29 completed "
                "http://koji.fedoraproject.org/koji/taskinfo?taskID=90100954"
            ),
            {
                "bz_id": 100,
            },
        )

    def test_call_buildsys_task_build_completed_staging(self):
        """
        Assert that message is handled correctly when the build is completed on staging.
        """
        message = create_message("buildsys.task.state.change", "build_completed")
        message.topic = "org.fedoraproject.stg.buildsys.task.state.change"

        self.consumer.database_cache.retrieve.return_value = {
            "key": "90100954",
            "value": "100",
        }

        self.consumer.notifier_bugzilla.notify.return_value = {"bz_id": "100"}

        self.consumer.__call__(message)

        self.consumer.database_cache.retrieve.assert_called_with("90100954")

        package = Package(name="globus-callout", version="4.0", distro="Fedora")

        self.consumer.notifier_bugzilla.notify.assert_called_with(
            package,
            (
                "koschei's scratch build of globus-callout-4.0-1.fc29.src.rpm for f29 completed "
                "http://koji.stg.fedoraproject.org/koji/taskinfo?taskID=90100954"
            ),
            {
                "bz_id": 100,
            },
        )

    def test_call_buildsys_task_build_multiple_targets(self):
        """
        Assert that message is handled correctly when the build is completed and have multiple
        targets.
        """
        message = create_message("buildsys.task.state.change", "build_multiple_targets")

        self.consumer.database_cache.retrieve.return_value = {
            "key": "90100954",
            "value": "100",
        }

        self.consumer.notifier_bugzilla.notify.return_value = {"bz_id": "100"}

        self.consumer.__call__(message)

        self.consumer.database_cache.retrieve.assert_called_with("90100954")

        package = Package(name="globus-callout", version="4.0", distro="Fedora")

        self.consumer.notifier_bugzilla.notify.assert_called_with(
            package,
            (
                "koschei's scratch build of globus-callout-4.0-1.fc29.src.rpm for "
                "f29, f30, and 2 others completed "
                "http://koji.fedoraproject.org/koji/taskinfo?taskID=90100954"
            ),
            {
                "bz_id": 100,
            },
        )

    def test_call_buildsys_task_build_no_target(self):
        """
        Assert that message is handled correctly when the build is completed and have no target.
        """
        message = create_message("buildsys.task.state.change", "build_no_target")

        self.consumer.database_cache.retrieve.return_value = {
            "key": "90100954",
            "value": "100",
        }

        self.consumer.notifier_bugzilla.notify.return_value = {"bz_id": "100"}

        self.consumer.__call__(message)

        self.consumer.database_cache.retrieve.assert_called_with("90100954")

        package = Package(name="globus-callout", version="4.0", distro="Fedora")

        self.consumer.notifier_bugzilla.notify.assert_called_with(
            package,
            (
                "koschei's scratch build of globus-callout-4.0-1.fc29.src.rpm completed "
                "http://koji.fedoraproject.org/koji/taskinfo?taskID=90100954"
            ),
            {
                "bz_id": 100,
            },
        )

    def test_call_buildsys_task_build_failed(self):
        """
        Assert that message is handled correctly when the build was failed.
        """
        message = create_message("buildsys.task.state.change", "build_failed")

        self.consumer.database_cache.retrieve.return_value = {
            "key": "90100954",
            "value": "100",
        }

        self.consumer.notifier_bugzilla.notify.return_value = {"bz_id": "100"}

        self.consumer.__call__(message)

        self.consumer.database_cache.retrieve.assert_called_with("90100954")

        package = Package(name="globus-callout", version="4.0", distro="Fedora")

        self.consumer.notifier_bugzilla.notify.assert_called_with(
            package,
            (
                "koschei's scratch build of globus-callout-4.0-1.fc29.src.rpm for f29 failed "
                "http://koji.fedoraproject.org/koji/taskinfo?taskID=90100954"
            ),
            {
                "bz_id": 100,
            },
        )

    def test_call_buildsys_task_build_canceled(self):
        """
        Assert that message is handled correctly when the build was canceled.
        """
        message = create_message("buildsys.task.state.change", "build_canceled")

        self.consumer.database_cache.retrieve.return_value = {
            "key": "90100954",
            "value": "100",
        }

        self.consumer.notifier_bugzilla.notify.return_value = {"bz_id": "100"}

        self.consumer.__call__(message)

        self.consumer.database_cache.retrieve.assert_called_with("90100954")

        package = Package(name="globus-callout", version="4.0", distro="Fedora")

        self.consumer.notifier_bugzilla.notify.assert_called_with(
            package,
            (
                "koschei's scratch build of globus-callout-4.0-1.fc29.src.rpm for f29 was canceled "
                "http://koji.fedoraproject.org/koji/taskinfo?taskID=90100954"
            ),
            {
                "bz_id": 100,
            },
        )

    def test_call_buildsys_task_build_not_in_done_state(self):
        """
        Assert that message is handled correctly when the build is not in done state.
        """
        message = create_message("buildsys.task.state.change", "build")

        self.consumer.database_cache.retrieve.return_value = {
            "key": "90100954",
            "value": "100",
        }

        self.consumer.__call__(message)

        self.consumer.database_cache.retrieve.assert_called_with("90100954")

        self.consumer.notifier_bugzilla.notify.assert_not_called()

    def test_call_buildsys_task_build_database_retrieve_failure(self):
        """
        Assert that message is handled correctly when we can't retrieve value from database.
        """
        message = create_message("buildsys.task.state.change", "build")

        self.consumer.database_cache.retrieve.side_effect = Exception(
            "This is tech heresy!"
        )

        self.consumer.__call__(message)

        self.consumer.database_cache.retrieve.assert_called_with("90100954")

        self.consumer.notifier_bugzilla.notify.assert_not_called()

    def test_call_buildsys_task_build_not_in_database(self):
        """
        Assert that message is handled correctly when the build is not in database.
        """
        message = create_message("buildsys.task.state.change", "build")

        self.consumer.database_cache.retrieve.return_value = {
            "key": "90100954",
            "value": "",
        }

        self.consumer.__call__(message)

        self.consumer.database_cache.retrieve.assert_called_with("90100954")

        self.consumer.notifier_bugzilla.notify.assert_not_called()

    def test_call_buildsys_task_build_secondary(self):
        """
        Assert that message is handled correctly when the build is not primary.
        """
        message = create_message("buildsys.task.state.change", "build_secondary")

        self.consumer.__call__(message)

        # Assert that nothing is called
        self.consumer.database_cache.retrieve.assert_not_called()

    def test_call_buildsys_task_non_build(self):
        """
        Assert that message is handled correctly when the task is non build.
        """
        message = create_message("buildsys.task.state.change", "non_build_method")

        self.consumer.__call__(message)

        # Assert that nothing is called
        self.consumer.database_cache.retrieve.assert_not_called()
