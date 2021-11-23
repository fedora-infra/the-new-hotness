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

from hotness.use_cases.package_check_use_case import PackageCheckUseCase
from hotness import responses


class TestPackageCheckUseCaseInit:
    """
    Test class for `hotness.use_cases.package_check_use_case.PackageCheckUseCase.__init__` method
    """

    def test_init(self):
        """
        Assert that the object is correctly created.
        """
        validator = mock.Mock()

        use_case = PackageCheckUseCase(validator=validator)

        assert use_case.validator == validator


class TestPackageCheckUseCaseValidate:
    """
    Test class for `hotness.use_cases.package_check_use_case.PackageCheckUseCase.validate` method
    """

    def test_validate_true(self):
        """
        Assert that the validation is called correctly and successful response
        is returned when validator returns True.
        """
        validator = mock.Mock()
        validator.validate.return_value = {"validation_output": True}

        package = mock.Mock()
        request = mock.Mock()
        request.package = package

        use_case = PackageCheckUseCase(validator=validator)

        result = use_case.validate(request)

        validator.validate.assert_called_with(package)
        assert type(result) is responses.ResponseSuccess
        assert bool(result) is True
        assert result.value == {"validation_output": True}

    def test_validate_false(self):
        """
        Assert that the validation is called correctly and successful response
        is returned when validator returns False.
        """
        validator = mock.Mock()
        validator.validate.return_value = {"validation_output": False}

        package = mock.Mock()
        request = mock.Mock()
        request.package = package

        use_case = PackageCheckUseCase(validator=validator)

        result = use_case.validate(request)

        validator.validate.assert_called_with(package)
        assert type(result) is responses.ResponseSuccess
        assert bool(result) is True
        assert result.value == {"validation_output": False}

    def test_validate_invalid_request(self):
        """
        Assert that the validate fails when request validation fails.
        """
        errors = [
            {
                "parameter": "param",
                "error": "This is not the parameter you are looking for.",
            }
        ]
        validator = mock.Mock()

        request = mock.MagicMock()
        request.__bool__.return_value = False
        request.errors = errors

        use_case = PackageCheckUseCase(validator=validator)

        result = use_case.validate(request)

        assert type(result) is responses.ResponseFailure
        assert bool(result) is False
        assert result.value == {
            "type": responses.ResponseFailure.INVALID_REQUEST_ERROR,
            "message": str(errors),
            "use_case_value": None,
        }

    def test_validate_failure(self):
        """
        Assert that the validation is called correctly and failure response
        is returned when validator raises exception.
        """
        validator = mock.Mock()
        validator.validate.side_effect = Exception("This is heresy!")

        package = mock.Mock()
        request = mock.Mock()
        request.package = package

        use_case = PackageCheckUseCase(validator=validator)

        result = use_case.validate(request)

        validator.validate.assert_called_with(package)
        assert type(result) is responses.ResponseFailure
        assert bool(result) is False
        assert result.value == {
            "type": responses.ResponseFailure.VALIDATOR_ERROR,
            "message": "Exception: This is heresy!",
            "use_case_value": None,
        }
