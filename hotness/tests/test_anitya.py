# -*- coding: utf-8 -*-
#
# Copyright (C) 2017-2020 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""Unit tests for :mod:`hotness.anitya`."""

from unittest import mock

from hotness import anitya
from hotness.tests.test_base import HotnessTestCase


class ForceCheckTests(HotnessTestCase):
    """
    Test class for testing `force_check` method in `Anitya` class.
    """

    def setUp(self):
        super(ForceCheckTests, self).setUp()
        self.anitya = anitya.Anitya()

    @mock.patch("hotness.anitya._log")
    def test_force_check_error(self, mock_log):
        """
        Assert that warning is in log when error is encountered during force check.
        """
        self.anitya.force_check(0, "")

        self.assertIn(
            "Anitya error: 'No such project'", mock_log.warning.call_args_list[0][0][0]
        )

    @mock.patch("hotness.anitya._log")
    def test_force_check_success(self, mock_log):
        """
        Assert that info is in log when force check is successful.
        """
        self.anitya.force_check(55612, "007")

        self.assertIn(
            "Check yielded upstream versions '0.0.2, 0.0.1' for 007",
            mock_log.info.call_args_list[0][0][0],
        )
