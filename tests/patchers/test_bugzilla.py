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
import os

import pytest
from unittest import mock

from hotness.domain import Package
from hotness.exceptions import PatcherException
from hotness.patchers import Bugzilla


class TestBugzillaInit:
    """
    Test class for `hotness.notifiers.Bugzilla.__init__` method.
    """

    @mock.patch("hotness.patchers.bugzilla.bugzilla")
    def test_init(self, mock_bugzilla):
        """
        Assert that Bugzilla patcher object is initialized correctly.
        """
        server_url = "https://example.com/"
        username = "Fabius@Bile.w40k"
        password = "UltraSuperHyperPassword"
        api_key = "some API key"
        bugzilla_session = mock.Mock()
        mock_bugzilla.Bugzilla.return_value = bugzilla_session

        notifier = Bugzilla(server_url, username, password, api_key)

        mock_bugzilla.Bugzilla.assert_called_with(
            url=server_url, api_key=api_key, cookiefile=None, tokenfile=None
        )

        assert notifier.bugzilla == bugzilla_session

    @mock.patch("hotness.patchers.bugzilla.bugzilla")
    def test_init_no_api_key(self, mock_bugzilla):
        """
        Assert that Bugzilla patcher object is initialized correctly when api_key is not provided.
        """
        server_url = "https://example.com/"
        username = "Fabius@Bile.w40k"
        password = "UltraSuperHyperPassword"
        api_key = ""
        bugzilla_session = mock.Mock()
        mock_bugzilla.Bugzilla.return_value = bugzilla_session

        notifier = Bugzilla(
            server_url,
            username,
            password,
            api_key,
        )

        mock_bugzilla.Bugzilla.assert_called_with(
            url=server_url,
            user=username,
            password=password,
            cookiefile=None,
            tokenfile=None,
        )
        assert notifier.bugzilla == bugzilla_session

    def test_init_no_authentication(self):
        """
        Assert that Bugzilla patcher object raises exception during initialization
        if authentication info is not provided.
        """
        server_url = "https://example.com/"
        username = ""
        password = ""
        api_key = ""

        with pytest.raises(PatcherException) as exc:
            Bugzilla(
                server_url,
                username,
                password,
                api_key,
            )

        assert exc.value.message == (
            "Authentication info not provided! Provide either 'username' and 'password' "
            "or API key."
        )


class TestBugzillaSubmitPatch:
    """
    Test class for `hotness.patchers.Bugzilla.submit_patch` method.
    """

    @mock.patch("hotness.patchers.bugzilla.bugzilla")
    def setup(self, mock_bugzilla):
        """
        Create patcher instance for tests.
        """
        server_url = "https://example.com/"
        username = "Fabius@Bile.w40k"
        password = "UltraSuperHyperPassword"
        api_key = "some API key"
        bugzilla_session = mock.Mock()
        mock_bugzilla.Bugzilla.return_value = bugzilla_session

        self.patcher = Bugzilla(
            server_url,
            username,
            password,
            api_key,
        )

        assert self.patcher.bugzilla == bugzilla_session

    @mock.patch("hotness.patchers.bugzilla.TemporaryDirectory")
    def test_submit_patch(self, mock_temp_dir, tmpdir):
        """
        Assert that submit_patch works correctly.
        """
        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        patch = "Fix everything"

        opts = {"bz_id": 100, "patch_filename": "patch"}

        mock_temp_dir.return_value.__enter__.return_value = tmpdir
        filepath = os.path.join(tmpdir, "patch")

        output = self.patcher.submit_patch(package, patch, opts)

        self.patcher.bugzilla.attachfile.assert_called_with(
            100, filepath, "Update to 1.0 (#100)", is_patch=True
        )

        assert output == {
            "bz_id": 100,
        }

    @pytest.mark.parametrize("opts", [{"bz_id": 100}, {"patch_filename": "patch"}, {}])
    def test_submit_patch_missing_opts(self, opts):
        """
        Assert that PatcherException is raised when the opts are missing.
        """
        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        patch = "Fix everything"

        with pytest.raises(PatcherException) as exc:
            self.patcher.submit_patch(package, patch, opts)

        assert exc.value.message == (
            "Additional parameters are missing! "
            "Please provide `bz_id` and `patch_filename`."
        )
