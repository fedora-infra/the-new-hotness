# Copyright (C) 2018  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""Unit tests for the message classes."""

import unittest
import mock

from hotness_schema import UpdateDrop, UpdateBugFile


class TestUpdateDrop(unittest.TestCase):
    """Tests for `hotness_schema.messages.UpdateDrop` class."""

    def setUp(self):
        """Set up the test environment."""
        message_body = {
            "reason": "anitya",
            "trigger": {
                "msg": {"message": {"new": "Dummy"}},
                "topic": "anitya.project.map.new",
            },
        }
        self.message = UpdateDrop(body=message_body)

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.packages", new_callable=mock.PropertyMock
    )
    @mock.patch(
        "hotness_schema.messages.UpdateDrop.reason", new_callable=mock.PropertyMock
    )
    def test_summary_anitya(self, mock_reason, mock_packages):
        """Assert correct summary is returned."""
        mock_packages.return_value = ["Dummy"]
        mock_reason.return_value = "anitya"
        print(self.message.reason)
        exp = (
            "the-new-hotness saw an update for 'Dummy', "
            "but release-monitoring.org doesn't know what "
            "that project is called in Fedora land"
        )
        self.assertEqual(self.message.summary, exp)

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.packages", new_callable=mock.PropertyMock
    )
    @mock.patch(
        "hotness_schema.messages.UpdateDrop.reason", new_callable=mock.PropertyMock
    )
    def test_summary_rawhide(self, mock_reason, mock_packages):
        """Assert correct summary is returned."""
        mock_packages.return_value = ["Dummy"]
        mock_reason.return_value = "rawhide"
        print(self.message.reason)
        exp = (
            "the-new-hotness saw an update for 'Dummy', "
            "but no rawhide version of the package could be found yet"
        )
        self.assertEqual(self.message.summary, exp)

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.packages", new_callable=mock.PropertyMock
    )
    @mock.patch(
        "hotness_schema.messages.UpdateDrop.reason", new_callable=mock.PropertyMock
    )
    def test_summary_pkgdb(self, mock_reason, mock_packages):
        """Assert correct summary is returned."""
        mock_packages.return_value = ["Dummy"]
        mock_reason.return_value = "pkgdb"
        print(self.message.reason)
        exp = (
            "the-new-hotness saw an update for 'Dummy', "
            "but pkgdb says the maintainers are not interested "
            "in bugs being filed"
        )
        self.assertEqual(self.message.summary, exp)

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.packages", new_callable=mock.PropertyMock
    )
    @mock.patch(
        "hotness_schema.messages.UpdateDrop.reason", new_callable=mock.PropertyMock
    )
    def test_summary_bugzilla(self, mock_reason, mock_packages):
        """Assert correct summary is returned."""
        mock_packages.return_value = ["Dummy"]
        mock_reason.return_value = "bugzilla"
        print(self.message.reason)
        exp = (
            "the-new-hotness saw an update for 'Dummy', "
            "but the bugzilla issue couldn't be updated"
        )
        self.assertEqual(self.message.summary, exp)

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.packages", new_callable=mock.PropertyMock
    )
    @mock.patch(
        "hotness_schema.messages.UpdateDrop.reason", new_callable=mock.PropertyMock
    )
    def test_summary_dummy(self, mock_reason, mock_packages):
        """Assert correct summary is returned."""
        mock_packages.return_value = ["Dummy"]
        mock_reason.return_value = "Dummy"
        print(self.message.reason)
        exp = (
            "the-new-hotness saw an update for 'Dummy', "
            "but it got dropped for reason: 'Dummy'"
        )
        self.assertEqual(self.message.summary, exp)

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.reason", new_callable=mock.PropertyMock
    )
    def test_package_reason_anitya_message(self, mock_reason):
        """
        Assert correct package is returned, when reason is anitya and body contains
        message key.
        """
        mock_reason.return_value = "anitya"
        message_body = {
            "trigger": {
                "msg": {
                    "message": {
                        "packages": [{"distro": "Fedora", "package_name": "Dummy"}]
                    }
                }
            }
        }
        with mock.patch.dict(self.message.body, message_body):
            self.assertEqual(self.message.packages, ["Dummy"])

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.reason", new_callable=mock.PropertyMock
    )
    def test_package_reason_anitya_no_packages_in_message(self, mock_reason):
        """
        Assert correct package is returned, when reason is anitya and body is
        missing packages key in message key.
        """
        mock_reason.return_value = "anitya"
        message_body = {
            "trigger": {
                "msg": {
                    "packages": [{"distro": "Fedora", "package_name": "Dummy"}],
                    "message": "",
                }
            }
        }
        with mock.patch.dict(self.message.body, message_body):
            self.assertEqual(self.message.packages, ["Dummy"])

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.reason", new_callable=mock.PropertyMock
    )
    def test_package_package_listing(self, mock_reason):
        """Assert correct package is returned, when package_listing key is available."""
        mock_reason.return_value = "Dummy"
        message_body = {
            "trigger": {"msg": {"package_listing": {"package": {"name": "Dummy"}}}}
        }
        with mock.patch.dict(self.message.body, message_body):
            self.assertEqual(self.message.packages, ["Dummy"])

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.reason", new_callable=mock.PropertyMock
    )
    def test_package_buildsys(self, mock_reason):
        """Assert correct package is returned, when topic contains buildsys.build."""
        mock_reason.return_value = "Dummy"
        message_body = {
            "trigger": {"msg": {"name": "Dummy"}, "topic": "buildsys.build.task.change"}
        }
        with mock.patch.dict(self.message.body, message_body):
            self.assertEqual(self.message.packages, ["Dummy"])

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.reason", new_callable=mock.PropertyMock
    )
    def test_package_package(self, mock_reason):
        """Assert correct package is returned, when package key is available."""
        mock_reason.return_value = "Dummy"
        message_body = {
            "trigger": {
                "msg": {"package": {"name": "Dummy"}},
                "topic": "anitya.project.version.update",
            }
        }
        with mock.patch.dict(self.message.body, message_body):
            self.assertEqual(self.message.packages, ["Dummy"])

    def test_reason(self):
        """Assert correct reason is returned."""
        message_body = {"reason": "Dummy"}
        with mock.patch.dict(self.message.body, message_body):
            self.assertEqual(self.message.reason, "Dummy")


class TestUpdateBugFile(unittest.TestCase):
    """Tests for `hotness_schema.messages.UpdateBugFile` class."""

    def setUp(self):
        """Set up the test environment."""
        message_body = {
            "trigger": {
                "msg": {"message": {"new": "dummy"}},
                "topic": "anitya.project.map.new",
            }
        }
        self.message = UpdateBugFile(body=message_body)

    @mock.patch(
        "hotness_schema.messages.UpdateBugFile.packages", new_callable=mock.PropertyMock
    )
    def test_summary(self, mock_property):
        """Assert correct summary is returned."""
        mock_property.return_value = ["Dummy"]
        exp = "the-new-hotness filed a bug on 'Dummy'"
        self.assertEqual(self.message.summary, exp)

    def test_packages_trigger_map_new(self):
        """Assert correct package is returned."""
        message_body = {
            "trigger": {
                "msg": {"message": {"new": "Dummy"}},
                "topic": "anitya.project.map.new",
            }
        }

        with mock.patch.dict(self.message.body, message_body):
            self.assertEqual(self.message.packages, ["Dummy"])

    def test_packages_trigger_else(self):
        """Assert correct packages are returned."""
        message_body = {
            "trigger": {
                "msg": {
                    "message": {
                        "packages": [
                            {"distro": "Fedora", "package_name": "Dummy"},
                            {"distro": "Fedora", "package_name": "Ordo Hereticus"},
                        ]
                    }
                },
                "topic": "anitya.project.version.update",
            }
        }

        with mock.patch.dict(self.message.body, message_body):
            self.assertEqual(self.message.packages, ["Dummy", "Ordo Hereticus"])
