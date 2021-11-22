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
from hotness.validators import MDApi
from hotness.exceptions import HTTPException


class TestMDAPIInit:
    """
    Test class for `hotness.validators.MDApi.__init__` method.
    """

    def test_init(self):
        """
        Assert that mdapi class is initialized successfully.
        """
        url = "http://testing.url"
        timeout = (5, 20)
        requests_session = mock.Mock()

        validator = MDApi(url, requests_session, timeout)

        assert validator.url == url
        assert validator.requests_session == requests_session
        assert validator.timeout == timeout


class TestMDAPIValidate:
    """
    Test class for `hotness.validators.MDApi.validate` method.
    """

    def test_validate(self):
        """
        Assert that validation returns correct.
        """
        url = "http://testing.url"
        timeout = (5, 20)

        # Mock requests_session
        requests_session = mock.Mock()

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {"version": "1.0", "release": "1.fc34"}
        requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.1", distro="Fedora")

        validator = MDApi(url, requests_session, timeout)

        result = validator.validate(package)

        requests_session.get.assert_called_with(
            url + "/koji/srcpkg/test", timeout=timeout
        )

        assert result["newer"] is True
        assert result["version"] == "1.0"
        assert result["release"] == "1.fc34"

    def test_validate_old(self):
        """
        Assert that validation returns correct output when the version is older.
        """
        url = "http://testing.url"
        timeout = (5, 20)

        # Mock requests_session
        requests_session = mock.Mock()

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {"version": "1.1", "release": "1.fc34"}
        requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")

        validator = MDApi(url, requests_session, timeout)

        result = validator.validate(package)

        requests_session.get.assert_called_with(
            url + "/koji/srcpkg/test", timeout=timeout
        )

        assert result["newer"] is False
        assert result["version"] == "1.1"
        assert result["release"] == "1.fc34"

    def test_validate_same(self):
        """
        Assert that validation returns correct output when the versions are same.
        """
        url = "http://testing.url"
        timeout = (5, 20)

        # Mock requests_session
        requests_session = mock.Mock()

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {"version": "1.0", "release": "1.fc34"}
        requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")

        validator = MDApi(url, requests_session, timeout)

        result = validator.validate(package)

        requests_session.get.assert_called_with(
            url + "/koji/srcpkg/test", timeout=timeout
        )

        assert result["newer"] is False
        assert result["version"] == "1.0"
        assert result["release"] == "1.fc34"

    def test_validate_rc_in_release(self):
        """
        Assert that validation returns correct output when the release contains release
        candidate values.
        """
        url = "http://testing.url"
        timeout = (5, 20)

        # Mock requests_session
        requests_session = mock.Mock()

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {"version": "1.0", "release": "0.1.rc1.fc34"}
        requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.0rc2", distro="Fedora")

        validator = MDApi(url, requests_session, timeout)

        result = validator.validate(package)

        requests_session.get.assert_called_with(
            url + "/koji/srcpkg/test", timeout=timeout
        )

        assert result["newer"] is True
        assert result["version"] == "1.0"
        assert result["release"] == "0.1.rc1.fc34"

    def test_validate_response_not_ok(self):
        """
        Assert that validation raises HTTPException when response code is not 200.
        """
        url = "http://testing.url"
        timeout = (5, 20)

        # Mock requests_session
        requests_session = mock.Mock()

        response = mock.Mock()
        response.status_code = 500

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")

        validator = MDApi(url, requests_session, timeout)
        validator.requests_session.get.return_value = response

        with pytest.raises(HTTPException) as ex:
            validator.validate(package)

        assert ex.value.error_code == 500
        assert (
            ex.value.message
            == "Error encountered on request {}/koji/srcpkg/test".format(url)
        )

        requests_session.get.assert_called_with(
            url + "/koji/srcpkg/test", timeout=timeout
        )
