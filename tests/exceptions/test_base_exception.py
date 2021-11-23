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
import pytest

from hotness.exceptions import BaseHotnessException


class TestBaseExceptionInit:
    """
    Test class for `hotness.exceptions.BaseHotnessException.__init__` method.
    """

    def test_init(self):
        """
        Assert that exception is created correctly.
        """
        exception = BaseHotnessException("This error is a tech heresy!")

        with pytest.raises(Exception):
            raise exception

        assert exception.message == "This error is a tech heresy!"

    def test_init_optional_arguments(self):
        """
        Assert that exception is created correctly.
        """
        exception = BaseHotnessException(
            "This error is a tech heresy!",
            value={"build_id": 100},
        )

        with pytest.raises(Exception):
            raise exception

        assert exception.message == "This error is a tech heresy!"
        assert exception.value == {"build_id": 100}


class TestBaseExceptionStr:
    """
    Test class for `hotness.exceptions.BaseHotnessException.__str__` method.
    """

    def test_str(self):
        """
        Assert that the string representation of exception is correct.
        """
        exception = BaseHotnessException("This error is a tech heresy!")

        assert str(exception) == "This error is a tech heresy!"
