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
from hotness.exceptions import NotifierException
from hotness.notifiers import Bugzilla


class TestBugzillaInit:
    """
    Test class for `hotness.notifiers.Bugzilla.__init__` method.
    """

    @mock.patch("hotness.notifiers.bugzilla.bugzilla")
    def test_init(self, mock_bugzilla):
        """
        Assert that Bugzilla notifier object is initialized correctly.
        """
        server_url = "https://example.com/"
        reporter = "cain@inquisition.w40k"
        username = "Fabius@Bile.w40k"
        password = "UltraSuperHyperPassword"
        api_key = "some API key"
        product = "Fedora"
        keywords = "Tzeentch, Chaos"
        version = "1.0"
        status = "NEW"
        bugzilla_session = mock.Mock()
        mock_bugzilla.Bugzilla.return_value = bugzilla_session

        notifier = Bugzilla(
            server_url,
            reporter,
            username,
            password,
            api_key,
            product,
            keywords,
            version,
            status,
        )

        mock_bugzilla.Bugzilla.assert_called_with(
            url=server_url, api_key=api_key, cookiefile=None, tokenfile=None
        )

        assert notifier.reporter == reporter
        assert notifier.bugzilla == bugzilla_session
        assert notifier.base_query == {
            "query_format": "advanced",
            "emailreporter1": "1",
            "emailtype1": "exact",
            "email1": username,
            "product": product,
        }
        assert notifier.new_bug == {
            "op_sys": "Unspecified",
            "platform": "Unspecified",
            "bug_severity": "unspecified",
            "product": product,
            "keywords": keywords,
            "version": version,
            "status": status,
        }

    @mock.patch("hotness.notifiers.bugzilla.bugzilla")
    def test_init_no_api_key(self, mock_bugzilla):
        """
        Assert that Bugzilla notifier object is initialized correctly when api_key is not provided.
        """
        server_url = "https://example.com/"
        reporter = "cain@inquisition.w40k"
        username = "Fabius@Bile.w40k"
        password = "UltraSuperHyperPassword"
        api_key = ""
        product = "Fedora"
        keywords = "Tzeentch, Chaos"
        version = "1.0"
        status = "NEW"
        bugzilla_session = mock.Mock()
        mock_bugzilla.Bugzilla.return_value = bugzilla_session

        notifier = Bugzilla(
            server_url,
            reporter,
            username,
            password,
            api_key,
            product,
            keywords,
            version,
            status,
        )

        mock_bugzilla.Bugzilla.assert_called_with(
            url=server_url,
            user=username,
            password=password,
            cookiefile=None,
            tokenfile=None,
        )

        assert notifier.reporter == reporter
        assert notifier.bugzilla == bugzilla_session
        assert notifier.base_query == {
            "query_format": "advanced",
            "emailreporter1": "1",
            "emailtype1": "exact",
            "email1": username,
            "product": product,
        }
        assert notifier.new_bug == {
            "op_sys": "Unspecified",
            "platform": "Unspecified",
            "bug_severity": "unspecified",
            "product": product,
            "keywords": keywords,
            "version": version,
            "status": status,
        }

    def test_init_no_authentication(self):
        """
        Assert that Bugzilla notifier object raises exception during initialization
        if authentication info is not provided.
        """
        server_url = "https://example.com/"
        reporter = "cain@inquisition.w40k"
        username = ""
        password = ""
        api_key = ""
        product = "Fedora"
        keywords = "Tzeentch, Chaos"
        version = "1.0"
        status = "NEW"

        with pytest.raises(NotifierException) as exc:
            Bugzilla(
                server_url,
                reporter,
                username,
                password,
                api_key,
                product,
                keywords,
                version,
                status,
            )

        assert exc.value.message == (
            "Authentication info not provided! Provide either 'username' and 'password' "
            "or API key."
        )


class TestBugzillaNotify:
    """
    Test class for `hotness.notifiers.Bugzilla.notify` method.
    """

    @mock.patch("hotness.notifiers.bugzilla.bugzilla")
    def setup(self, mock_bugzilla):
        """
        Create notifier instance for tests.
        """
        server_url = "https://example.com/"
        reporter = "cain@inquisition.w40k"
        username = "Fabius@Bile.w40k"
        password = "UltraSuperHyperPassword"
        api_key = "some API key"
        product = "Fedora"
        keywords = ["Tzeentch", "Chaos"]
        version = "1.0"
        status = "NEW"
        bugzilla_session = mock.Mock()
        mock_bugzilla.Bugzilla.return_value = bugzilla_session

        self.notifier = Bugzilla(
            server_url,
            reporter,
            username,
            password,
            api_key,
            product,
            keywords,
            version,
            status,
        )

        assert self.notifier.bugzilla == bugzilla_session

    def test_notify_follow_up(self):
        """
        Assert that notify will follow up on existing bug when bug id is provided.
        """
        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")

        message = (
            "This is a confidential message requiring Inquisitorial access of level 5."
        )

        opts = {"bz_id": 100}

        output = self.notifier.notify(package, message, opts)

        self.notifier.bugzilla._proxy.Bug.update.assert_called_with(
            {
                "comment": {
                    "body": message,
                    "is_private": False,
                },
                "ids": [opts["bz_id"]],
            }
        )

        expected_output = {"bz_id": 100}

        assert output == expected_output

    def test_notify_bug_exists(self):
        """
        Assert that notify will do nothing if bug id is not provided, but the
        exact bug exists.
        """
        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")

        message = (
            "This is a confidential message requiring Inquisitorial access of level 5."
        )

        opts = {"bz_short_desc": "test-1.0 is available"}

        # Mock bugzilla query output
        mock_bug = mock.Mock()
        mock_bug.bug_id = 100
        mock_bug.weburl = "Bug URL"
        self.notifier.bugzilla.query.return_value = [mock_bug]

        output = self.notifier.notify(package, message, opts)

        # It looks like assert_called_with convert parameter to None when doing update on dict
        # Let's use assert_has_calls instead
        self.notifier.bugzilla.query.assert_has_calls == [
            {
                "component": "test",
                "bug_status": self.notifier.bug_status_open
                + self.notifier.bug_status_closed,
                "short_desc": opts["bz_short_desc"],
                "short_desc_type": "substring",
            }.update(self.notifier.base_query)
        ]

        expected_output = {"bz_id": 100}

        assert output == expected_output

    def test_notify_bug_open_for_previous_version(self):
        """
        Assert that notify will update existing bug if bug id is not provided and the
        bug for previous version is still open.
        """
        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")

        message = (
            "This is a confidential message requiring Inquisitorial access of level 5."
        )

        opts = {"bz_short_desc": "test-1.0 is available"}

        # Mock bugzilla query output
        mock_bug = mock.Mock()
        mock_bug.bug_id = 100
        mock_bug.weburl = "Bug URL"
        self.notifier.bugzilla.query.side_effect = [[], [mock_bug]]

        output = self.notifier.notify(package, message, opts)

        self.notifier.bugzilla.query.assert_has_calls == [
            {
                "component": "test",
                "bug_status": self.notifier.bug_status_open
                + self.notifier.bug_status_closed,
                "short_desc": opts["bz_short_desc"],
                "short_desc_type": "substring",
            }.update(self.notifier.base_query),
            {
                "component": "test",
                "bug_status": self.notifier.bug_status_early
                + [self.notifier.new_bug["status"]],
                "creator": self.notifier.reporter,
            }.update(self.notifier.base_query),
        ]

        self.notifier.bugzilla._proxy.Bug.update.assert_called_with(
            {
                "summary": opts["bz_short_desc"],
                "comment": {
                    "body": message,
                    "is_private": False,
                },
                "ids": [100],
            }
        )

        expected_output = {"bz_id": 100}

        assert output == expected_output

    def test_notify_create_bug(self):
        """
        Assert that notify will create bug if bug id is not provided and the bug doesn't exist.
        """
        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")

        message = (
            "This is a confidential message requiring Inquisitorial access of level 5."
        )

        opts = {"bz_short_desc": "test-1.0 is available"}

        # Mock bugzilla query output
        self.notifier.bugzilla.query.return_value = []

        # Mock bugzilla createbug output
        mock_bug = mock.Mock()
        mock_bug.bug_id = 100
        mock_bug.weburl = "Bug URL"
        self.notifier.bugzilla.createbug.return_value = mock_bug

        output = self.notifier.notify(package, message, opts)

        self.notifier.bugzilla.query.assert_has_calls == [
            {
                "component": "test",
                "bug_status": self.notifier.bug_status_open
                + self.notifier.bug_status_closed,
                "short_desc": opts["bz_short_desc"],
                "short_desc_type": "substring",
            }.update(self.notifier.base_query),
            {
                "component": "test",
                "bug_status": self.notifier.bug_status_early
                + [self.notifier.new_bug["status"]],
                "creator": self.notifier.reporter,
            }.update(self.notifier.base_query),
        ]

        # It looks like assert_called_with convert parameter to None when doing update on dict
        # Let's use assert_has_calls instead
        self.notifier.bugzilla.createbug.assert_has_calls == [
            {
                "component": "test",
                "short_desc": opts["bz_short_desc"],
                "description": message,
            }.update(self.notifier.new_bug)
        ]

        expected_output = {"bz_id": 100}

        assert output == expected_output

    def test_notify_missing_options(self):
        """
        Assert that exception will be raised when notifier options are missing.
        """
        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")

        message = (
            "This is a confidential message requiring Inquisitorial access of level 5."
        )

        opts = {}

        with pytest.raises(NotifierException) as exc:
            self.notifier.notify(package, message, opts)

        assert exc.value.message == (
            "Additional parameters are missing! "
            "Please provide either `bz_id` or `bz_short_desc`."
        )
