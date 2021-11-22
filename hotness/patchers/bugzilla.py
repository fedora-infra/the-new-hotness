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
import os
from tempfile import TemporaryDirectory

import bugzilla

from hotness.exceptions import PatcherException
from hotness.domain.package import Package
from .patcher import Patcher


_logger = logging.getLogger(__name__)


class Bugzilla(Patcher):
    """
    This class is a wrapper for https://bugzilla.redhat.com/
    It submit patches to Bugzilla.

    Attributes:
        bugzilla (bugzilla.Bugzilla): Bugzilla session
    """

    def __init__(
        self,
        server_url: str,
        username: str,
        password: str,
        api_key: str,
    ) -> None:
        """
        Class constructor.

        It initializes bugzilla session using the provided credentials.
        If the `api_key` is not provided, it will try to establish a session
        using `username` and `password`.

        Params:
            server_url: URL of the bugzilla server
            username: Username to use for authentication
            password: Password to use for authentication
            api_key: API key to use for authentication

        Raises:
            PatcherException: When the bugzilla session can't be established
        """
        super(Bugzilla, self).__init__()
        if api_key:
            self.bugzilla = bugzilla.Bugzilla(
                url=server_url, api_key=api_key, cookiefile=None, tokenfile=None
            )
        elif username and password:
            self.bugzilla = bugzilla.Bugzilla(
                url=server_url,
                user=username,
                password=password,
                cookiefile=None,
                tokenfile=None,
            )
        else:
            raise PatcherException(
                "Authentication info not provided! Provide either 'username' and 'password' "
                "or API key."
            )
        self.bugzilla.bug_autorefresh = True

    def submit_patch(self, package: Package, patch: str, opts: dict) -> dict:
        """
        This method is inherited from `hotness.patchers.Patcher`.

        It attaches file to existing ticket in bugzilla.

        Params:
            package: Package to create notification for
            patch: Patch to attach, it needs to be converted to file first
            opts: Additional options for bugzilla. Example:
                {
                    "bz_id": 100, # Bugzilla ticket id, if provided the
                                  # new message will be added as new comment to this ticket
                    "patch_filename": "patch" # Name of the file, that should be attached
                }

        Returns:
            Dictionary containing ticket bugzilla id
            Example:
            {
                "bz_id": 100
            }
        """
        output = {}
        bug_id = opts.get("bz_id", 0)
        filename = opts.get("patch_filename", "")
        if bug_id == 0 or not filename:
            raise PatcherException(
                "Additional parameters are missing! "
                "Please provide `bz_id` and `patch_filename`."
            )

        # Write file to temporary directory
        # and stop bandit from complaining about a hardcoded temporary directory
        # because it's needed for OpenShift
        with TemporaryDirectory(prefix="thn-", dir="/var/tmp") as tmp:  # nosec
            filepath = os.path.join(tmp, filename)
            with open(filepath, "w") as f:
                f.write(patch)

            _logger.debug("Attaching file to bug %r" % bug_id)
            description = "Update to {} (#{})".format(package.version, bug_id)
            self.bugzilla.attachfile(bug_id, filepath, description, is_patch=True)
            _logger.info("Attached file to bug: %r" % bug_id)

        output["bz_id"] = bug_id
        return output
