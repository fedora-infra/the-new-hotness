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

from hotness.use_cases.package_scratch_build_use_case import PackageScratchBuildUseCase
from hotness import responses


class TestPackageScratchBuildUseCaseInit:
    """
    Test class for
    `hotness.use_cases.package_scratch_build_use_case.PackageScratchBuildUseCase.__init__`
    method
    """

    def test_init(self):
        """
        Assert that the object is correctly created.
        """
        builder = mock.Mock()

        use_case = PackageScratchBuildUseCase(builder=builder)

        assert use_case.builder == builder


class TestPackageScratchBuildUseCaseBuild:
    """
    Test class for
    `hotness.use_cases.package_scratch_build_use_case.PackageScratchBuildUseCase.build` method
    """

    def test_build(self):
        """
        Assert that the build is called correctly and successful response
        is returned when build is started.
        """
        builder = mock.Mock()
        builder.build.return_value = {"build_id": 1}

        package = mock.Mock()
        opts = {}
        request = mock.Mock()
        request.package = package
        request.opts = opts

        use_case = PackageScratchBuildUseCase(builder=builder)

        result = use_case.build(request)

        builder.build.assert_called_with(package, opts)
        assert type(result) is responses.ResponseSuccess
        assert bool(result) is True
        assert result.value == {"build_id": 1}

    def test_build_invalid_request(self):
        """
        Assert that the build fails when request validation fails.
        """
        errors = [
            {
                "parameter": "param",
                "error": "This is not the parameter you are looking for.",
            }
        ]
        builder = mock.Mock()

        request = mock.MagicMock()
        request.__bool__.return_value = False
        request.errors = errors

        use_case = PackageScratchBuildUseCase(builder=builder)

        result = use_case.build(request)

        assert type(result) is responses.ResponseFailure
        assert bool(result) is False
        assert result.value == {
            "type": responses.ResponseFailure.INVALID_REQUEST_ERROR,
            "message": str(errors),
            "use_case_value": None,
        }

    def test_build_failure(self):
        """
        Assert that the build is called correctly and failure response
        is returned when builder raises exception.
        """
        builder = mock.Mock()
        builder.build.side_effect = Exception("This is heresy!")

        package = mock.Mock()
        opts = {}
        request = mock.Mock()
        request.package = package
        request.opts = opts

        use_case = PackageScratchBuildUseCase(builder=builder)

        result = use_case.build(request)

        builder.build.assert_called_with(package, opts)
        assert type(result) is responses.ResponseFailure
        assert bool(result) is False
        assert result.value == {
            "type": responses.ResponseFailure.BUILDER_ERROR,
            "message": "Exception: This is heresy!",
            "use_case_value": None,
        }
