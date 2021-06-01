# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Red Hat, Inc.
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
from hotness.requests import Request


class TestRequestInit:
    """
    Test class for `hotness.requests.Request.__init__` method.
    """

    def test_init(self):
        """
        Assert that request object is correctly initialized.
        """
        request = Request()

        assert request.errors == []


class TestRequestAddError:
    """
    Test class for `hotness.requests.Request.add_error` method.
    """

    def test_add_error(self):
        """
        Assert that error is added correctly.
        """
        parameter = "param"
        error = "You shall not pass!"
        request = Request()

        request.add_error(parameter, error)

        exp = [{"parameter": parameter, "error": error}]

        assert request.errors == exp


class TestRequestBool:
    """
    Test class for `hotness.requests.Request.__bool__` method.
    """

    def test_bool_true(self):
        """
        Assert that valid request returns true.
        """
        request = Request()

        assert bool(request) is True

    def test_bool_false(self):
        """
        Assert that invalid request returns false.
        """
        parameter = "param"
        error = "You shall not pass!"
        request = Request()

        request.add_error(parameter, error)

        assert bool(request) is False
