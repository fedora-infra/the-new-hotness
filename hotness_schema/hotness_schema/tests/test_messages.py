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
        self.message = UpdateDrop()

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.summary", new_callable=mock.PropertyMock
    )
    def test__str__(self, mock_property):
        """Assert correct string is returned."""
        mock_property.return_value = "Dummy"
        self.assertEqual(self.message.__str__(), "Dummy")

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.project", new_callable=mock.PropertyMock
    )
    @mock.patch(
        "hotness_schema.messages.UpdateDrop.reason", new_callable=mock.PropertyMock
    )
    def test_summary_anitya(self, mock_reason, mock_project):
        """Assert correct summary is returned."""
        mock_project.return_value = "Dummy"
        mock_reason.return_value = "anitya"
        print(self.message.reason)
        exp = (
            "the-new-hotness saw an update for 'Dummy', "
            "but release-monitoring.org doesn't know what "
            "that project is called in Fedora land"
        )
        self.assertEqual(self.message.summary, exp)

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.project", new_callable=mock.PropertyMock
    )
    @mock.patch(
        "hotness_schema.messages.UpdateDrop.reason", new_callable=mock.PropertyMock
    )
    def test_summary_rawhide(self, mock_reason, mock_project):
        """Assert correct summary is returned."""
        mock_project.return_value = "Dummy"
        mock_reason.return_value = "rawhide"
        print(self.message.reason)
        exp = (
            "the-new-hotness saw an update for 'Dummy', "
            "but no rawhide version of the package could be found yet"
        )
        self.assertEqual(self.message.summary, exp)

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.project", new_callable=mock.PropertyMock
    )
    @mock.patch(
        "hotness_schema.messages.UpdateDrop.reason", new_callable=mock.PropertyMock
    )
    def test_summary_pkgdb(self, mock_reason, mock_project):
        """Assert correct summary is returned."""
        mock_project.return_value = "Dummy"
        mock_reason.return_value = "pkgdb"
        print(self.message.reason)
        exp = (
            "the-new-hotness saw an update for 'Dummy', "
            "but pkgdb says the maintainers are not interested "
            "in bugs being filed"
        )
        self.assertEqual(self.message.summary, exp)

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.project", new_callable=mock.PropertyMock
    )
    @mock.patch(
        "hotness_schema.messages.UpdateDrop.reason", new_callable=mock.PropertyMock
    )
    def test_summary_bugzilla(self, mock_reason, mock_project):
        """Assert correct summary is returned."""
        mock_project.return_value = "Dummy"
        mock_reason.return_value = "bugzilla"
        print(self.message.reason)
        exp = (
            "the-new-hotness saw an update for 'Dummy', "
            "but the bugzilla issue couldn't be updated"
        )
        self.assertEqual(self.message.summary, exp)

    @mock.patch(
        "hotness_schema.messages.UpdateDrop.project", new_callable=mock.PropertyMock
    )
    @mock.patch(
        "hotness_schema.messages.UpdateDrop.reason", new_callable=mock.PropertyMock
    )
    def test_summary_dummy(self, mock_reason, mock_project):
        """Assert correct summary is returned."""
        mock_project.return_value = "Dummy"
        mock_reason.return_value = "Dummy"
        print(self.message.reason)
        exp = (
            "the-new-hotness saw an update for 'Dummy', "
            "but it got dropped for reason: 'Dummy'"
        )
        self.assertEqual(self.message.summary, exp)

    def test_project(self):
        """Assert correct project is returned."""
        self.message.body = {"trigger": {"msg": {"project": "Dummy"}}}
        self.assertEqual(self.message.project, "Dummy")

    def test_reason(self):
        """Assert correct reason is returned."""
        self.message.body = {"reason": "Dummy"}
        self.assertEqual(self.message.reason, "Dummy")


class TestUpdateBugFile(unittest.TestCase):
    """Tests for `hotness_schema.messages.UpdateBugFile` class."""

    def setUp(self):
        """Set up the test environment."""
        self.message = UpdateBugFile()

    @mock.patch(
        "hotness_schema.messages.UpdateBugFile.summary", new_callable=mock.PropertyMock
    )
    def test__str__(self, mock_property):
        """Assert correct string is returned."""
        mock_property.return_value = "Dummy"
        self.assertEqual(self.message.__str__(), "Dummy")

    @mock.patch(
        "hotness_schema.messages.UpdateBugFile.package", new_callable=mock.PropertyMock
    )
    def test_summary(self, mock_property):
        """Assert correct summary is returned."""
        mock_property.return_value = "Dummy"
        exp = "the-new-hotness filed a bug on 'Dummy'"
        self.assertEqual(self.message.summary, exp)

    def test_package(self):
        """Assert correct package is returned."""
        self.message.body = {"package": "Dummy"}
        self.assertEqual(self.message.package, "Dummy")
