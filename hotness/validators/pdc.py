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

from . import Validator
from hotness.domain import Package
from hotness.exceptions import HTTPException

from requests import Session


_logger = logging.getLogger(__name__)


class PDC(Validator):
    """
    Wrapper around PDC (Product definition center) https://pdc.fedoraproject.org

    It inherits the Validator abstract class and implements the validate method.

    The PDC wrapper is used to check if the package is retired in Fedora.

    Attributes:
        url: URL of the PDC server
        requests_session: Session object which will be used for HTTP request
        timeout: Timeouts to HTTP request in seconds (connect timeout, read timeout)
        branch: Branch to check (rawhide, f34, f33...)
        package_type: Type of package to check (rpm, module...)
    """

    def __init__(
        self,
        url: str,
        requests_session: Session,
        timeout: tuple,
        branch: str,
        package_type: str,
    ) -> None:
        """
        Class constructor.
        """
        self.url = url
        self.requests_session = requests_session
        self.timeout = timeout
        self.branch = branch
        self.package_type = package_type

    def validate(self, package: Package) -> dict:
        """
        Implementation of `Validator.validate` method. It calls the PDC, checks the response
        and returns the output.

        Params:
            package: Package to check in PDC

        Returns:
            Dictionary containing output of response and validation.
            Example:
            {
                "retired": True,
                "count": "0",  # Number of active branches found
            }

        Raises:
            HTTPException: Is raised when HTTP status code of response isn't 200.
        """
        output = {}
        pdc_url = "{0}/rest_api/v1/component-branches/".format(self.url)
        params = dict(
            name=self.branch,
            global_component=package.name,
            type=self.package_type,
            active=True,
        )
        _logger.debug(
            "Checking {} to see if {} is retired, {}".format(pdc_url, package, params)
        )
        response = self.requests_session.get(
            pdc_url, params=params, timeout=self.timeout
        )

        if not response.status_code == 200:
            raise HTTPException(
                response.status_code, "Error encountered on request {}".format(pdc_url)
            )

        js = response.json()
        # If there are zero active rawhide branches for this package, then it is
        # retired.
        output["retired"] = js["count"] == 0
        output["active_branches"] = js["count"]

        return output
