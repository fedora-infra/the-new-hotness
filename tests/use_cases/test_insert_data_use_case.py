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
from unittest import mock

from hotness.use_cases import InsertDataUseCase
from hotness import responses


class TestInsertDataUseCaseInit:
    """
    Test class for `hotness.use_cases.InsertDataUseCase.__init__` method
    """

    def test_init(self):
        """
        Assert that the object is correctly created.
        """
        database = mock.Mock()

        use_case = InsertDataUseCase(database=database)

        assert use_case.database == database


class TestInsertDataUseCaseInsert:
    """
    Test class for `hotness.use_cases.InsertDataUseCase.insert` method
    """

    def test_insert(self):
        """
        Assert that the insert is called correctly and successful response
        is returned when no error is encountered.
        """
        key = "key"
        value = "value"
        database = mock.Mock()
        database.insert.return_value = {"key": key, "value": value}

        request = mock.MagicMock()
        request.key = key
        request.value = value
        request.__bool__.return_value = True

        use_case = InsertDataUseCase(database=database)

        result = use_case.insert(request)

        database.insert.assert_called_with(key, value)
        assert type(result) is responses.ResponseSuccess
        assert bool(result) is True
        assert result.value == {"key": key, "value": value}

    def test_insert_invalid_request(self):
        """
        Assert that the insert fails when request validation fails.
        """
        errors = [
            {
                "parameter": "param",
                "error": "This is not the parameter you are looking for.",
            }
        ]
        database = mock.Mock()

        request = mock.MagicMock()
        request.__bool__.return_value = False
        request.errors = errors

        use_case = InsertDataUseCase(database=database)

        result = use_case.insert(request)

        assert type(result) is responses.ResponseFailure
        assert bool(result) is False
        assert result.value == {
            "type": responses.ResponseFailure.INVALID_REQUEST_ERROR,
            "message": str(errors),
            "use_case_value": None,
        }

    def test_insert_failure(self):
        """
        Assert that the insert is called correctly and failure response
        is returned when database raises exception.
        """
        key = "key"
        value = "value"
        database = mock.Mock()
        database.insert.side_effect = Exception("This is heresy!")

        request = mock.MagicMock()
        request.key = key
        request.value = value
        request.__bool__.return_value = True

        use_case = InsertDataUseCase(database=database)

        result = use_case.insert(request)

        database.insert.assert_called_with(key, value)
        assert type(result) is responses.ResponseFailure
        assert bool(result) is False
        assert result.value == {
            "type": responses.ResponseFailure.DATABASE_ERROR,
            "message": "Exception: This is heresy!",
            "use_case_value": None,
        }
