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
        branch = "rawhide"
        package_type = "rpm"

        validator = Pagure(url, requests_session, timeout, branch, package_type)

        assert validator.url == url
        assert validator.requests_session == requests_session
        assert validator.timeout == timeout
        assert validator.branch == branch
        assert validator.package_type == package_type


class TestPagureValidate:
    """
    Test class for `hotness.validators.Pagure.validate` method.
    """

    def setup_method(self):
        """
        Setup phase before test.
        """
        # Initialize Retired wrapper
        url = "http://testing.url"
        timeout = (5, 20)
        requests_session = mock.Mock()
        branch = "rawhide"
        package_type = "rpm"

        self.validator = Pagure(url, requests_session, timeout, branch, package_type)

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

        self.validator.requests_session.get.assert_any_call(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        self.validator.requests_session.get.assert_any_call(
            self.validator.url
            + "/rpms/"
            + package.name
            + "/blob/"
            + self.validator.branch
            + "/f/dead.package",
            timeout=timeout,
        )

        assert 2 == self.validator.requests_session.get.call_count

        assert result["monitoring"] is True
        assert result["all_versions"] is False
        assert result["stable_only"] is False
        assert result["scratch_build"] is False
        assert result["retired"] is True

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

        self.validator.requests_session.get.assert_any_call(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        assert result["monitoring"] is False
        assert result["all_versions"] is False
        assert result["stable_only"] is False
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

        self.validator.requests_session.get.assert_any_call(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        assert result["monitoring"] is True
        assert result["all_versions"] is False
        assert result["stable_only"] is False
        assert result["scratch_build"] is True

    def test_validate_monitoring_all(self):
        """
        Assert that validation returns correct output when monitoring for all versions
        is set.
        """
        # Mock requests_session
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {
            "monitoring": "monitoring-all",
        }
        self.validator.requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.1", distro="Fedora")

        result = self.validator.validate(package)

        # Parameters for requests get call
        timeout = (5, 20)

        self.validator.requests_session.get.assert_any_call(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        assert result["monitoring"] is True
        assert result["all_versions"] is True
        assert result["stable_only"] is False
        assert result["scratch_build"] is False

    def test_validate_monitoring_all_scratch(self):
        """
        Assert that validation returns correct output when monitoring for all versions
        with scratch build is set.
        """
        # Mock requests_session
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {
            "monitoring": "monitoring-all-scratch",
        }
        self.validator.requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.1", distro="Fedora")

        result = self.validator.validate(package)

        # Parameters for requests get call
        timeout = (5, 20)

        self.validator.requests_session.get.assert_any_call(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        assert result["monitoring"] is True
        assert result["all_versions"] is True
        assert result["stable_only"] is False
        assert result["scratch_build"] is True

    def test_validate_monitoring_stable(self):
        """
        Assert that validation returns correct output when monitoring for stable versions
        is set.
        """
        # Mock requests_session
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {
            "monitoring": "monitoring-stable",
        }
        self.validator.requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.1", distro="Fedora")

        result = self.validator.validate(package)

        # Parameters for requests get call
        timeout = (5, 20)

        self.validator.requests_session.get.assert_any_call(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        assert result["monitoring"] is True
        assert result["all_versions"] is False
        assert result["stable_only"] is True
        assert result["scratch_build"] is False

    def test_validate_monitoring_stable_scratch(self):
        """
        Assert that validation returns correct output when monitoring for stable versions
        with scratch build is set.
        """
        # Mock requests_session
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {
            "monitoring": "monitoring-stable-scratch",
        }
        self.validator.requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.1", distro="Fedora")

        result = self.validator.validate(package)

        # Parameters for requests get call
        timeout = (5, 20)

        self.validator.requests_session.get.assert_any_call(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        assert result["monitoring"] is True
        assert result["all_versions"] is False
        assert result["stable_only"] is True
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

        self.validator.requests_session.get.assert_any_call(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        assert result["monitoring"] is False
        assert result["all_versions"] is False
        assert result["stable_only"] is False
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

        self.validator.requests_session.get.assert_any_call(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        assert result["monitoring"] is False
        assert result["all_versions"] is False
        assert result["stable_only"] is False
        assert result["scratch_build"] is False

    @pytest.mark.parametrize("statuscode", (500, 404))
    def test_validate_response_monitoring_not_ok(self, statuscode):
        """
        Assert that validation raises HTTPException when response code is 500 or 404.
        """
        response = mock.Mock()
        response.status_code = statuscode

        self.validator.requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")

        with pytest.raises(HTTPException) as ex:
            self.validator.validate(package)

        if statuscode == 500:
            assert ex.value.error_code == 500
            assert (
                ex.value.message
                == "Error encountered on request http://testing.url/_dg/anitya/rpms/test"
            )
        else:
            assert ex.value.error_code == 404
            assert (
                ex.value.message
                == "Error encountered on request http://testing.url/_dg/anitya/rpms/test"
            )

        # Parameters for requests get call
        timeout = (5, 20)

        self.validator.requests_session.get.assert_called_with(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        assert 1 == self.validator.requests_session.get.call_count

    def test_validate_response_monitoring_ok_retired_not_ok(self):
        """
        Assert that validation raises HTTPException when response code is 200
        for the monitoring call, but 500 for the retirement call.
        """
        response = mock.Mock()

        self.validator.requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        response200 = mock.Mock()
        response200.status_code = 200
        response500 = mock.Mock()
        response500.status_code = 500
        self.validator.requests_session.get.side_effect = [response200, response500]

        with pytest.raises(HTTPException) as ex:
            self.validator.validate(package)

        assert ex.value.error_code == 500
        assert (
            ex.value.message == "Error encountered on request http://testing.url"
            "/rpms/test/blob/rawhide/f/dead.package"
        )

        # Parameters for requests get call
        timeout = (5, 20)
        branch = "rawhide"

        self.validator.requests_session.get.assert_any_call(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )
        self.validator.requests_session.get.assert_called_with(
            self.validator.url
            + "/rpms/{0}/blob/{1}/f/dead.package".format(package.name, branch),
            timeout=timeout,
        )

        assert 2 == self.validator.requests_session.get.call_count

    def test_validate_not_retired(self):
        """
        Assert that Pagure returns correct output when package is retired.
        """
        response = mock.Mock()

        self.validator.requests_session.get.return_value = response

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        response200 = mock.Mock()
        response200.status_code = 200
        response404 = mock.Mock()
        response404.status_code = 404
        self.validator.requests_session.get.side_effect = [response200, response404]
        result = self.validator.validate(package)

        # Parameters for requests get call
        timeout = (5, 20)
        branch = "rawhide"

        self.validator.requests_session.get.assert_any_call(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )
        self.validator.requests_session.get.assert_called_with(
            self.validator.url
            + "/rpms/{0}/blob/{1}/f/dead.package".format(package.name, branch),
            timeout=timeout,
        )

        assert 2 == self.validator.requests_session.get.call_count
        assert result["retired"] is False
