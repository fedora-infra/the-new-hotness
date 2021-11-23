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

from hotness.use_cases.submit_patch_use_case import SubmitPatchUseCase
from hotness import responses


class TestSubmitPatchUseCaseInit:
    """
    Test class for
    `hotness.use_cases.SubmitPatchUseCase.__init__`
    method
    """

    def test_init(self):
        """
        Assert that the object is correctly created.
        """
        patcher = mock.Mock()

        use_case = SubmitPatchUseCase(patcher=patcher)

        assert use_case.patcher == patcher


class TestSubmitPatchUseCaseSubmitPatch:
    """
    Test class for
    `hotness.use_cases.SubmitPatchUseCase.submit_patch` method
    """

    def test_submit_patch(self):
        """
        Assert that the submit_patch is called correctly and successful response
        is returned when patch is submitted.
        """
        patcher = mock.Mock()
        patcher.submit_patch.return_value = {"response": "success"}

        package = mock.Mock()
        patch = "Fix everything"
        request = mock.Mock()
        request.package = package
        request.patch = patch
        request.opts = {}

        use_case = SubmitPatchUseCase(patcher=patcher)

        result = use_case.submit_patch(request)

        patcher.submit_patch.assert_called_with(package, patch, {})
        assert type(result) is responses.ResponseSuccess
        assert bool(result) is True
        assert result.value == {"response": "success"}

    def test_build_invalid_request(self):
        """
        Assert that the submit_patch fails when request validation fails.
        """
        errors = [
            {
                "parameter": "param",
                "error": "This is not the parameter you are looking for.",
            }
        ]
        patcher = mock.Mock()

        request = mock.MagicMock()
        request.__bool__.return_value = False
        request.errors = errors

        use_case = SubmitPatchUseCase(patcher=patcher)

        result = use_case.submit_patch(request)

        assert type(result) is responses.ResponseFailure
        assert bool(result) is False
        assert result.value == {
            "type": responses.ResponseFailure.INVALID_REQUEST_ERROR,
            "message": str(errors),
            "use_case_value": None,
        }

    def test_build_failure(self):
        """
        Assert that the submit_patch is called correctly and failure response
        is returned when patcher raises exception.
        """
        patcher = mock.Mock()
        patcher.submit_patch.side_effect = Exception("This is heresy!")

        package = mock.Mock()
        patch = "Fix everything"
        request = mock.Mock()
        request.package = package
        request.patch = patch
        request.opts = {}

        use_case = SubmitPatchUseCase(patcher=patcher)

        result = use_case.submit_patch(request)

        patcher.submit_patch.assert_called_with(package, patch, {})
        assert type(result) is responses.ResponseFailure
        assert bool(result) is False
        assert result.value == {
            "type": responses.ResponseFailure.PATCHER_ERROR,
            "message": "Exception: This is heresy!",
            "use_case_value": None,
        }
