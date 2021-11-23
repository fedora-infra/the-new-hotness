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
from unittest import mock

from hotness.domain import Package
from hotness.validators import PDC
from hotness.exceptions import HTTPException


class TestPDCInit:
    """
    Test class for `hotness.validators.PDC.__init__` method.
    """

    def test_init(self):
        """
        Assert that PDC class is initialized successfully.
        """
        url = "http://testing.url"
        timeout = (5, 20)
        requests_session = mock.Mock()
        branch = "rawhide"
        package_type = "rpm"

        validator = PDC(url, requests_session, timeout, branch, package_type)

        assert validator.url == url
        assert validator.requests_session == requests_session
        assert validator.timeout == timeout
        assert validator.branch == branch
        assert validator.package_type == package_type


class TestPDCValidate:
    """
    Test class for `hotness.validators.PDC.validate` method.
    """

    def setup(self):
        """
        Setup phase before test.
        """
        # Initialize PDC wrapper
        url = "http://testing.url"
        timeout = (5, 20)
        requests_session = mock.Mock()
        branch = "rawhide"
        package_type = "rpm"

        self.validator = PDC(url, requests_session, timeout, branch, package_type)

    def test_validate_retired(self):
        """
        Assert that PDC returns correct output when package is retired.
        """
        # Mock requests_session
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {
            "count": 0,
        }
        self.validator.requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.1", distro="Fedora")

        result = self.validator.validate(package)

        # Parameters for requests get call
        timeout = (5, 20)
        params = {
            "name": self.validator.branch,
            "global_component": package.name,
            "type": self.validator.package_type,
            "active": True,
        }

        self.validator.requests_session.get.assert_called_with(
            self.validator.url + "/rest_api/v1/component-branches/",
            params=params,
            timeout=timeout,
        )

        assert result["retired"] is True
        assert result["active_branches"] == 0

    def test_validate_not_retired(self):
        """
        Assert that PDC returns correct output when package is retired.
        """
        # Mock requests_session
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {
            "count": 1,
        }
        self.validator.requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.1", distro="Fedora")

        result = self.validator.validate(package)

        # Parameters for requests get call
        timeout = (5, 20)
        params = {
            "name": self.validator.branch,
            "global_component": package.name,
            "type": self.validator.package_type,
            "active": True,
        }

        self.validator.requests_session.get.assert_called_with(
            self.validator.url + "/rest_api/v1/component-branches/",
            params=params,
            timeout=timeout,
        )

        assert result["retired"] is False
        assert result["active_branches"] == 1

    def test_validate_response_not_ok(self):
        """
        Assert that validation raises HTTPException when response code is not 200.
        """
        # Mock requests_session
        response = mock.Mock()
        response.status_code = 500
        self.validator.requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")

        with pytest.raises(HTTPException) as ex:
            self.validator.validate(package)

        assert ex.value.error_code == 500
        assert (
            ex.value.message
            == "Error encountered on request {}/rest_api/v1/component-branches/".format(
                self.validator.url
            )
        )

        # Parameters for requests get call
        timeout = (5, 20)
        params = {
            "name": self.validator.branch,
            "global_component": package.name,
            "type": self.validator.package_type,
            "active": True,
        }

        self.validator.requests_session.get.assert_called_with(
            self.validator.url + "/rest_api/v1/component-branches/",
            params=params,
            timeout=timeout,
        )
