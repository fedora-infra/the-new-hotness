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
from hotness.responses.response_success import ResponseSuccess


class TestResponseSuccessInit:
    """
    Test class for `hotness.responses.response_success.ResponseSuccess.__init__` method.
    """

    def test_init(self):
        """
        Assert that object is created correctly.
        """
        response = ResponseSuccess(value="something")

        assert response.value == "something"
        assert response.type == ResponseSuccess.SUCCESS


class TestResponseSuccessBool:
    """
    Test class for `hotness.responses.response_success.ResponseSuccess.__bool__` method.
    """

    def test_bool(self):
        """
        Assert that response success is True.
        """
        response = ResponseSuccess(value=None)

        assert bool(response) is True
