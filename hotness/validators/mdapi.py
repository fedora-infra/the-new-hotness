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
import re

from . import Validator
from hotness.domain import Package
from hotness.exceptions import HTTPException
from hotness.common import RPM

from requests import Session


_logger = logging.getLogger(__name__)


class MDApi(Validator):
    """
    Wrapper around the mdapi https://mdapi.fedoraproject.org/

    It inherits the Validator abstract class and implements the validate method.

    The mdapi will be used to check for the last available package version available in
    Fedora and compare if this is newer than the provided package.

    Attributes:
        url: URL of the mdapi server
        requests_session: Session object which will be used for HTTP request
        timeout: Timeouts to HTTP request in seconds (connect timeout, read timeout)
        __rc_release_regex: Regex for parsing release field obtained from mdapi
    """

    __rc_release_regex = re.compile(r"0\.[0-9]+\.(rc|pre|beta|alpha|dev)([0-9]*)", re.I)

    def __init__(self, url: str, requests_session: Session, timeout: tuple) -> None:
        """
        Class constructor.
        """
        super(MDApi, self).__init__()
        self.url = url
        self.requests_session = requests_session
        self.timeout = timeout

    def validate(self, package: Package) -> dict:
        """
        Implementation of `Validator.validate` method. It calls the mdapi, compares
        retrieved version with package version and returns the output.

        Params:
            package: Package to check against mdapi

        Returns:
            Dictionary containing output of response and validation.
            Example:
            {
                "newer": True,
                "version": "1.0",
                "release": 1
            }

        Raises:
            HTTPException: Is raised when HTTP status code of response isn't 200.
        """
        output = {}
        mdapi_url = "{0}/koji/srcpkg/{1}".format(self.url, package.name)
        _logger.debug("Getting pkg info from %r" % mdapi_url)

        response = self.requests_session.get(mdapi_url, timeout=self.timeout)
        # If error is encountered raise exception
        if response.status_code != 200:
            raise HTTPException(
                response.status_code,
                "Error encountered on request {}".format(mdapi_url),
            )

        js = response.json()
        output["version"] = js["version"]
        output["release"] = js["release"]

        _logger.info(
            "Comparing upstream %s against repo %s-%s"
            % (package.version, output["version"], output["release"])
        )

        rc_tuple = self._get_rc(output["release"])

        mdapi_version = "{}{}{}".format(output["version"], rc_tuple[0], rc_tuple[1])

        diff = RPM.compare(package.version, mdapi_version)

        if diff == 1:
            _logger.info(
                "%s is newer than %s-%s"
                % (package.version, output["version"], output["release"])
            )
            output["newer"] = True
        else:
            _logger.info(
                "%s is not newer than %s-%s"
                % (package.version, output["version"], output["release"])
            )
            output["newer"] = False

        return output

    def _get_rc(self, release: str) -> tuple:
        """
        Get the release candidate value of a package's release

        Params:
            release: Release to parse

        Returns:
            Tuple containing string part of release and numeric part of release.
        """
        match = self.__rc_release_regex.match(release)

        if match:
            return (match.group(1), match.group(2))
        else:
            return ("", "")
