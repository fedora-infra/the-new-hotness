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

    @pytest.mark.parametrize(
        "monitoring_value",
        [
            "monitoring",
            "no-monitoring",
            "monitoring-with-scratch",
            "monitoring-all",
            "monitoring-all-scratch",
            "monitoring-stable",
            "monitoring-stable-scratch",
        ],
    )
    def test_validate_monitoring(self, monitoring_value):
        """
        Assert that validation returns correct output when monitoring is set.
        """
        # Mock requests_session
        response_retired = mock.Mock()
        response_retired.status_code = 404
        response_config = mock.Mock()
        response_config.status_code = 404
        response_monitoring_setting = mock.Mock()
        response_monitoring_setting.status_code = 200
        response_monitoring_setting.json.return_value = {
            "monitoring": monitoring_value,
        }
        self.validator.requests_session.get.side_effect = [
            response_retired,
            response_config,
            response_monitoring_setting,
        ]

        # Prepare package
        package = Package(name="test", version="1.1", distro="Fedora")

        result = self.validator.validate(package)

        # Parameters for requests get call
        timeout = (5, 20)

        self.validator.requests_session.get.assert_any_call(
            self.validator.url
            + "/rpms/"
            + package.name
            + "/blob/"
            + self.validator.branch
            + "/f/dead.package",
            timeout=timeout,
        )

        self.validator.requests_session.get.assert_any_call(
            self.validator.url + "/_dg/anitya/rpms/{}".format(package.name),
            timeout=timeout,
        )

        self.validator.requests_session.get.assert_any_call(
            self.validator.url
            + "/rpms/"
            + package.name
            + "/raw/"
            + self.validator.branch
            + "/f/monitoring.toml",
            timeout=timeout,
        )

        assert 3 == self.validator.requests_session.get.call_count

        if monitoring_value != "no-monitoring":
            assert result["monitoring"] is True
        else:
            assert result["monitoring"] is False
        assert result["bugzilla"] is True
        if monitoring_value.startswith("monitoring-all"):
            assert result["all_versions"] is True
        else:
            assert result["all_versions"] is False
        if monitoring_value.startswith("monitoring-stable"):
            assert result["stable_only"] is True
        else:
            assert result["stable_only"] is False
        if "scratch" in monitoring_value:
            assert result["scratch_build"] is True
        else:
            assert result["scratch_build"] is False
        assert result["retired"] is False

    def test_validate_monitoring_is_missing(self):
        """
        Assert that validation returns correct output when monitoring option is missing.
        """
        # Mock requests_session
        response_retired = mock.Mock()
        response_retired.status_code = 404
        response_config = mock.Mock()
        response_config.status_code = 404
        response_monitoring_setting = mock.Mock()
        response_monitoring_setting.status_code = 200
        response_monitoring_setting.json.return_value = {}
        self.validator.requests_session.get.side_effect = [
            response_retired,
            response_config,
            response_monitoring_setting,
        ]

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
        assert result["bugzilla"] is True
        assert result["all_versions"] is False
        assert result["stable_only"] is False
        assert result["scratch_build"] is False
        assert result["retired"] is False

    def test_validate_invalid_monitoring_value(self):
        """
        Assert that validation returns correct output when monitoring value is invalid.
        """
        # Mock requests_session
        response_retired = mock.Mock()
        response_retired.status_code = 404
        response_config = mock.Mock()
        response_config.status_code = 404
        response_monitoring_setting = mock.Mock()
        response_monitoring_setting.status_code = 200
        response_monitoring_setting.json.return_value = {
            "monitoring": "foobar",
        }
        self.validator.requests_session.get.side_effect = [
            response_retired,
            response_config,
            response_monitoring_setting,
        ]

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
        assert result["bugzilla"] is True
        assert result["all_versions"] is False
        assert result["stable_only"] is False
        assert result["scratch_build"] is False
        assert result["retired"] is False

    @pytest.mark.parametrize("statuscode", (500, 404))
    def test_validate_response_monitoring_not_ok(self, statuscode):
        """
        Assert that validation raises HTTPException when response code is 500 or 404.
        """
        # Mock requests_session
        response_retired = mock.Mock()
        response_retired.status_code = 404
        response_config = mock.Mock()
        response_config.status_code = 404
        response_monitoring_setting = mock.Mock()
        response_monitoring_setting.status_code = statuscode
        response_monitoring_setting.json.return_value = {
            "monitoring": "foobar",
        }
        self.validator.requests_session.get.side_effect = [
            response_retired,
            response_config,
            response_monitoring_setting,
        ]

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

        assert 3 == self.validator.requests_session.get.call_count

    def test_validate_response_retired_not_ok(self):
        """
        Assert that validation raises HTTPException when response code is 500
        for the retirement call.
        """
        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        response500 = mock.Mock()
        response500.status_code = 500
        self.validator.requests_session.get.return_value = response500

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

        self.validator.requests_session.get.assert_called_with(
            self.validator.url
            + "/rpms/{0}/blob/{1}/f/dead.package".format(package.name, branch),
            timeout=timeout,
        )

        assert 1 == self.validator.requests_session.get.call_count

    def test_validate_retired(self):
        """
        Assert that Pagure returns correct output when package is retired.
        """
        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        response200 = mock.Mock()
        response200.status_code = 200
        self.validator.requests_session.get.return_value = response200
        result = self.validator.validate(package)

        # Parameters for requests get call
        timeout = (5, 20)
        branch = "rawhide"

        self.validator.requests_session.get.assert_called_with(
            self.validator.url
            + "/rpms/{0}/blob/{1}/f/dead.package".format(package.name, branch),
            timeout=timeout,
        )

        assert 1 == self.validator.requests_session.get.call_count
        assert result["retired"] is True

    @pytest.mark.parametrize(
        "monitoring_config",
        [
            {
                "monitoring": False,
                "bugzilla": True,
                "all_versions": True,
                "stable_only": True,
                "scratch_build": True,
            },
            {
                "monitoring": False,
                "all_versions": True,
            },
            {},
        ],
    )
    def test_monitoring_config(self, monitoring_config):
        """
        Test that monitoring config is correctly processed.
        """
        # Convert monitoring_config dict to toml format
        toml_str = ""
        for key, value in monitoring_config.items():
            toml_str = toml_str + f"{key} = {str(value).lower()}\n"

        # Mock requests_session
        response_retired = mock.Mock()
        response_retired.status_code = 404
        response_config = mock.Mock()
        response_config.status_code = 200
        response_config.text = toml_str
        self.validator.requests_session.get.side_effect = [
            response_retired,
            response_config,
        ]

        # Prepare package
        package = Package(name="test", version="1.1", distro="Fedora")

        result = self.validator.validate(package)

        # Parameters for requests get call
        timeout = (5, 20)

        self.validator.requests_session.get.assert_any_call(
            self.validator.url
            + "/rpms/"
            + package.name
            + "/raw/"
            + self.validator.branch
            + "/f/monitoring.toml",
            timeout=timeout,
        )

        assert 2 == self.validator.requests_session.get.call_count

        assert result["monitoring"] is monitoring_config.get("monitoring", True)
        assert result["bugzilla"] is monitoring_config.get("bugzilla", True)
        assert result["all_versions"] is monitoring_config.get("all_versions", False)
        assert result["stable_only"] is monitoring_config.get("stable_only", False)
        assert result["scratch_build"] is monitoring_config.get("scratch_build", False)
        assert result["retired"] is False
