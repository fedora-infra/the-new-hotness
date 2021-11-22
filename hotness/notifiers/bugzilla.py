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

import bugzilla

from hotness.exceptions import NotifierException
from hotness.domain.package import Package
from .notifier import Notifier


_logger = logging.getLogger(__name__)


class Bugzilla(Notifier):
    """
    This class is a wrapper for https://bugzilla.redhat.com/
    It creates or updates the ticket in Bugzilla and also handles Bugzilla
    session.

    Attributes:
        reporter (str): Reporter e-mail to use
        bugzilla (bugzilla.Bugzilla): Bugzilla session
        base_query (dict): Base query to use when looking for ticket in bugzilla
        bug_status_early (list): Statuses assigned to ticket in early stages
        bug_status_open (list): `bug_status_early` + statuses when the ticket is still considered
                                open
        bug_status_closed (list): List of statuses in which the ticket is considered closed
        new_bug (dict): Parameters for creating a new_bug in Bugzilla
    """

    base_query = {
        "query_format": "advanced",
        "emailreporter1": "1",
        "emailtype1": "exact",
    }

    bug_status_early = ["NEW", "ASSIGNED"]
    bug_status_open = bug_status_early + [
        "MODIFIED",
        "ON_DEV",
        "ON_QA",
        "VERIFIED",
        "FAILS_QA",
        "RELEASE_PENDING",
        "POST",
    ]

    bug_status_closed = ["CLOSED"]

    new_bug = {
        "op_sys": "Unspecified",
        "platform": "Unspecified",
        "bug_severity": "unspecified",
    }

    def __init__(
        self,
        server_url: str,
        reporter: str,
        username: str,
        password: str,
        api_key: str,
        product: str,
        keywords: str,
        version: str,
        status: str,
    ) -> None:
        """
        Class constructor.

        It initializes bugzilla session using the provided credentials.
        If the `api_key` is not provided, it will try to establish a session
        using `username` and `password`. If none of these authentication
        methods is provided it raises an `NotifierException`.

        Params:
            server_url: URL of the bugzilla server
            reporter: Reporter e-mail to use
            username: Username to use for authentication
            password: Password to use for authentication
            api_key: API key to use for authentication
            product: Product to assign the ticket to
            keywords: Keywords for the new ticket
            version: Version of product to assign to new ticket
            status: Status of the new bug

        Raises:
            NotifierException: When the bugzilla session can't be established
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
            raise NotifierException(
                "Authentication info not provided! Provide either 'username' and 'password' "
                "or API key."
            )
        self.bugzilla.bug_autorefresh = True

        self.reporter = reporter

        self.base_query["product"] = product
        self.base_query["email1"] = username

        self.new_bug["product"] = product
        if keywords:
            self.new_bug["keywords"] = keywords
        self.new_bug["version"] = version
        self.new_bug["status"] = status

    def notify(self, package: Package, message: str, opts: dict) -> dict:
        """
        This method is inherited from `hotness.notifiers.Notifier`.

        It either follows up on existing bug if bug id is provided or creates
        a new ticket if bug id is not provided and no ticket is found.

        Params:
            package: Package to create notification for
            message: Message to post
            opts: Additional options for bugzilla. Example:
                {
                    "bz_id": 100, # Bugzilla ticket id, if provided the
                                  # new message will be added as new comment to this ticket
                    "bz_short_desc": "test-1.0 is available" # Short description (title) to use
                                                             # when searching for the ticket
                                                             # If not found the new bug will be
                                                             # created with this short description
                                                             # containing `message`
                }

        Returns:
            Dictionary containing ticket bugzilla id
            Example:
            {
                "bz_id": 100
            }

        Raises:
            NotifierException: When the required `opts` parameters are missing.
        """
        output = {}
        bug_id = opts.get("bz_id", 0)
        short_desc = opts.get("bz_short_desc", "")
        # If bugzilla ticket id is provided, just follow up on the bug
        if not bug_id == 0:
            _logger.info("Bug id provided. Updating %s" % bug_id)
            self._update_bug(bug_id, message)
            output["bz_id"] = bug_id
            return output

        if not short_desc:
            raise NotifierException(
                "Additional parameters are missing! "
                "Please provide either `bz_id` or `bz_short_desc`."
            )

        # If bugzilla ticket id is not provided, try to find the bug using
        # the short description
        bug = self._exact_bug(package, short_desc)
        if bug:
            _logger.info("Found exact bug '%r'. Skipping notify action." % bug.weburl)
            output["bz_id"] = bug.bug_id
            return output

        # If none is found, try to look for any bug previously reported by the-new-hotness
        # that is still open and update that one
        bug = self._inexact_bug(package)
        if bug:
            _logger.info(
                "There is already bug opened for previous version '%r'. "
                "Let's update this one." % bug.weburl
            )
            self._update_bug(bug.bug_id, message, short_desc)
            output["bz_id"] = bug.bug_id
            return output

        # If no bug exists create one
        bug = self._create_bug(package, message, short_desc)
        _logger.info("Filled a new bug %r" % bug.weburl)
        output["bz_id"] = bug.bug_id
        return output

    def _update_bug(self, bug_id: int, message: str, summary: str = "") -> None:
        """
        Updates bug in bugzilla specified by bug id.

        Params:
            bug_id: Id of the bug in bugzilla
            message: Message to add as comment
            summary: Summary of the bug, only needs to be provided if we want
                     to update it.
        """
        update = {
            "comment": {
                "body": message,
                "is_private": False,
            },
            "ids": [bug_id],
        }
        if summary:
            update["summary"] = summary
        _logger.debug("Updating bug %r with %r" % (bug_id, update))
        res = self.bugzilla._proxy.Bug.update(update)
        _logger.debug("Result from bug update: %r" % res)
        _logger.info("Updated bug: %s" % bug_id)

    def _exact_bug(self, package: Package, short_desc: str) -> "bugzilla.Bug":
        """
        Look for exact bug for the specified package.

        Params:
            package: Search for bug for this package
            short_desc: Short description to search for

        Returns:
            `bugzilla.Bug` if the bug is found or None if not.
        """
        query = {
            "component": package.name,
            "bug_status": self.bug_status_open + self.bug_status_closed,
            "short_desc": short_desc,
            "short_desc_type": "substring",
        }

        query.update(self.base_query)
        bugs = self.bugzilla.query(query)
        if bugs:
            return bugs[0]
        return None

    def _inexact_bug(self, package: Package) -> "bugzilla.Bug":
        """
        Search for tickets in bugzilla filled by `self.reporter` and still
        in early states.

        Params:
            package: Search for bug for this package

        Returns:
            `bugzilla.Bug` if the bug is found or None if not.
        """
        # We'll match bugs in the NEW or ASSIGNED state
        # https://github.com/fedora-infra/the-new-hotness/issues/58
        possible_statuses = list(set(self.bug_status_early + [self.new_bug["status"]]))
        possible_statuses.sort()
        query = {
            "component": package.name,
            "bug_status": possible_statuses,
            "creator": self.reporter,
        }

        query.update(self.base_query)
        bugs = self.bugzilla.query(query)
        if bugs:
            return bugs[0]
        return None

    def _create_bug(
        self, package: Package, message: str, short_desc: str
    ) -> "bugzilla.Bug":
        """
        Create a new bug in bugzilla.

        Params:
            package: Create bug for this package
            message: Message to add to bug
            short_desc: Summary of the bug to create

        Returns:
            Created `bugzilla.Bug`.
        """
        bug_dict = {
            "component": package.name,
            "short_desc": short_desc,
            "description": message,
        }
        bug_dict.update(self.new_bug)
        new_bug = self.bugzilla.createbug(**bug_dict)
        _logger.info("Created bug: %s" % new_bug)

        return new_bug
