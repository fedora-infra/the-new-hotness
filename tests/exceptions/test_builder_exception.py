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

from hotness.exceptions import BuilderException


class TestBuilderExceptionInit:
    """
    Test class for `hotness.exceptions.BuilderException.__init__` method.
    """

    def test_init(self):
        """
        Assert that exception is created correctly.
        """
        exception = BuilderException("This error is a tech heresy!")

        with pytest.raises(Exception):
            raise exception

        assert exception.message == "This error is a tech heresy!"

    def test_init_optional_arguments(self):
        """
        Assert that exception is created correctly.
        """
        exception = BuilderException(
            "This error is a tech heresy!",
            value={"build_id": 100},
            std_out="This is a standard output",
            std_err="This is an error output",
        )

        with pytest.raises(Exception):
            raise exception

        assert exception.message == "This error is a tech heresy!"
        assert exception.value == {"build_id": 100}
        assert exception.std_out == "This is a standard output"
        assert exception.std_err == "This is an error output"


class TestBuilderExceptionStr:
    """
    Test class for `hotness.exceptions.BuilderException.__str__` method.
    """

    def test_str(self):
        """
        Assert that the string representation of exception is correct.
        """
        exception = BuilderException("This error is a tech heresy!")

        assert str(exception) == ("Build failed:\n" "This error is a tech heresy!\n")

    def test_str_build_id(self):
        """
        Assert that the string representation of exception is correct
        when build id is available.
        """
        exception = BuilderException(
            "This error is a tech heresy!", value={"build_id": 100}
        )

        assert str(exception) == (
            "Build started, but failure happened during post build operations:\n"
            "This error is a tech heresy!\n"
        )

    def test_str_std_err_out(self):
        """
        Assert that the string representation of exception is correct
        when stderr and stdout are available.
        """
        exception = BuilderException(
            "This error is a tech heresy!",
            std_err="This blasphemy should never happen!",
            std_out="Praise Slaanesh!",
        )

        assert str(exception) == (
            "Build failed:\n"
            "This error is a tech heresy!\n\n"
            "StdOut:\n"
            "Praise Slaanesh!\n\n"
            "StdErr:\n"
            "This blasphemy should never happen!\n"
        )
