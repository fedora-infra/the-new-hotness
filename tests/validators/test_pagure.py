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
from hotness.validators import Pagure
from hotness.exceptions import HTTPException


class TestPagureInit:
    """
    Test class for `hotness.validators.Pagure.__init__` method.
    """

    def test_init(self):
        """
        Assert that Pagure class is initialized successfully.
        """
        url = "http://testing.url"
        timeout = (5, 20)
        requests_session = mock.Mock()

        validator = Pagure(url, requests_session, timeout)

        assert validator.url == url
        assert validator.requests_session == requests_session
        assert validator.timeout == timeout


class TestPagureValidate:
    """
    Test class for `hotness.validators.Pagure.validate` method.
    """

    def setup(self):
        """
        Setup phase before test.
        """
        # Initialize PDC wrapper
        url = "http://testing.url"
        timeout = (5, 20)
        requests_session = mock.Mock()

        self.validator = Pagure(url, requests_session, timeout)

    def test_validate_monitoring(self):
        """
        Assert that validation returns correct output when monitoring is set.
        """
        # Mock requests_session
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {
            "monitoring": "monitoring",
        }
        self.validator.requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.1", distro="Fedora")

        result = self.validator.validate(package)

        # Parameters for requests get call
        timeout = (5, 20)

        self.validator.requests_session.get.assert_called_with(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        assert result["monitoring"] is True
        assert result["scratch_build"] is False

    def test_validate_no_monitoring(self):
        """
        Assert that validation returns correct output when monitoring is not set.
        """
        # Mock requests_session
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {
            "monitoring": "no-monitoring",
        }
        self.validator.requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.1", distro="Fedora")

        result = self.validator.validate(package)

        # Parameters for requests get call
        timeout = (5, 20)

        self.validator.requests_session.get.assert_called_with(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        assert result["monitoring"] is False
        assert result["scratch_build"] is False

    def test_validate_monitoring_scratch(self):
        """
        Assert that validation returns correct output when monitoring with scratch build is set.
        """
        # Mock requests_session
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {
            "monitoring": "monitoring-with-scratch",
        }
        self.validator.requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.1", distro="Fedora")

        result = self.validator.validate(package)

        # Parameters for requests get call
        timeout = (5, 20)

        self.validator.requests_session.get.assert_called_with(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        assert result["monitoring"] is True
        assert result["scratch_build"] is True

    def test_validate_monitoring_is_missing(self):
        """
        Assert that validation returns correct output when monitoring option is missing.
        """
        # Mock requests_session
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {}
        self.validator.requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.1", distro="Fedora")

        result = self.validator.validate(package)

        # Parameters for requests get call
        timeout = (5, 20)

        self.validator.requests_session.get.assert_called_with(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        assert result["monitoring"] is False
        assert result["scratch_build"] is False

    def test_validate_invalid_monitoring_value(self):
        """
        Assert that validation returns correct output when monitoring value is invalid.
        """
        # Mock requests_session
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {
            "monitoring": "foobar",
        }
        self.validator.requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.1", distro="Fedora")

        result = self.validator.validate(package)

        # Parameters for requests get call
        timeout = (5, 20)

        self.validator.requests_session.get.assert_called_with(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        assert result["monitoring"] is False
        assert result["scratch_build"] is False

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
            == "Error encountered on request {}/_dg/anitya/rpms/{}".format(
                self.validator.url, package.name
            )
        )

        # Parameters for requests get call
        timeout = (5, 20)

        self.validator.requests_session.get.assert_called_with(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )
