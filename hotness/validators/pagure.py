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
import logging
from typing import Optional, Tuple, Union

from . import Validator
from hotness.domain import Package
from hotness.exceptions import HTTPException

from requests import Session


# Accepted monitoring statuses
MONITORING_STATUSES = [
    "monitoring",
    "monitoring-with-scratch",
    "monitoring-all",
    "monitoring-all-scratch",
    "monitoring-stable",
    "monitoring-stable-scratch",
    "no-monitoring",
]

# Monitoring statuses that requires scratch build
MONITORING_STATUSES_SCRATCH_BUILD = [
    "monitoring-with-scratch",
    "monitoring-all-scratch",
    "monitoring-stable-scratch",
]

_logger = logging.getLogger(__name__)


class Pagure(Validator):
    """
    Wrapper around Pagure dist-git https://src.fedoraproject.org

    It inherits the Validator abstract class and implements the validate method.

    The Pagure wrapper is used to check if the package owner in Fedora wants to be notified
    about new version and optionally run a scratch build.

    Attributes:
        url: URL of the PDC server
        requests_session: Session object which will be used for HTTP request
        timeout: Timeouts to HTTP request in seconds (connect timeout, read timeout)
    """

    def __init__(
        self,
        url: str,
        requests_session: Session,
        timeout: Optional[Union[float, Tuple[float, float], Tuple[float, None]]],
    ) -> None:
        """
        Class constructor.
        """
        self.url = url
        self.requests_session = requests_session
        self.timeout = timeout

    def validate(self, package: Package) -> dict:
        """
        Implementation of `Validator.validate` method. It calls the Pagure dist-git, checks if the
        package owner wants to be monitored and returns the output.

        Params:
            package: Package to check in Pagure

        Returns:
            Dictionary containing output of response and validation.
            Example:
            {
                "monitoring": True,  # If the packager wants to be notified or not
                "all_versions": True,  # If the packager wants to be notified about every
                                       # version received by Anitya
                "stable_only": True,  # If the packager wants to be notified only about
                                      # stable versions received by Anitya
                "scratch_build": False  # If the packager wants to run a scratch build or not
            }

        Raises:
            HTTPException: Is raised when HTTP status code of response isn't 200.
        """
        output = {
            "monitoring": False,
            "scratch_build": False,
            "stable_only": False,
            "all_versions": False,
        }
        dist_git_url = "{0}/_dg/anitya/rpms/{1}".format(self.url, package.name)
        _logger.debug(
            "Checking {} to see if {} is monitored.".format(dist_git_url, package.name)
        )
        response = self.requests_session.get(dist_git_url, timeout=self.timeout)

        if not response.status_code == 200:
            raise HTTPException(
                response.status_code,
                "Error encountered on request {}".format(dist_git_url),
            )

        data = response.json()
        monitoring_value = data.get("monitoring", "no-monitoring")

        # Fill the output based on the monitoring value
        # Invalid = monitoring: False; scrach_build: False; all_versions: False; stable_only: False
        # monitoring =
        #   monitoring: True; scrach_build: False; all_versions: False; stable_only: False
        # monitoring-with-scratch =
        #   monitoring: True; scrach_build: True; all_versions: False; stable_only: False
        # monitoring-all =
        #   monitoring: True; scrach_build: False; all_versions: True; stable_only: False
        # monitoring-all-scratch =
        #   monitoring: True; scrach_build: True; all_versions: True; stable_only: False
        # monitoring-stable =
        #   monitoring: True; scrach_build: False; all_versions: True; stable_only: True
        # monitoring-stable-scratch =
        #   monitoring: True; scrach_build: True; all_versions: True; stable_only: True
        # no-monitoring =
        #   monitoring: False; scrach_build: False; all_versions: False; stable_only: False
        if monitoring_value not in MONITORING_STATUSES:
            _logger.info(
                "Unknown status '{}' recovered from {}".format(
                    dist_git_url, monitoring_value
                )
            )

        if monitoring_value.startswith("monitoring"):
            output["monitoring"] = True

        if monitoring_value.startswith("monitoring-all"):
            output["all_versions"] = True

        if monitoring_value.startswith("monitoring-stable"):
            output["stable_only"] = True

        if monitoring_value in MONITORING_STATUSES_SCRATCH_BUILD:
            output["scratch_build"] = True

        return output
