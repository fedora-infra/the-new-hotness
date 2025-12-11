# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Red Hat, Inc.
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

"""Unit tests for the fix for issue #605 - handling when git repo is already up to date."""

import os
from unittest import mock
import pytest

from hotness.builders.koji import Koji
from hotness.domain.package import Package


class TestKojiFix605:
    """Test the fix for issue #605."""

    def setup_method(self, method):
        self.builder = Koji(
            server_url="server_url",
            web_url="web_url",
            kerberos_args={
                "krb_principal": "krb_principal",
                "krb_keytab": "krb_keytab",
                "krb_ccache": "krb_ccache",
                "krb_proxyuser": "krb_proxyuser",
                "krb_sessionopts": "krb_sessionopts",
            },
            git_url="git_url",
            user_email=("user_name", "user_email"),
            opts={"opts": "opts"},
            priority=1,
            target_tag="target_tag",
        )

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_already_up_to_date(self, mock_temp_dir, mock_check_output, tmpdir):
        """
        Test that build is skipped when repo is already up to date (git status is clean).
        This tests the fix for issue #605.
        """
        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        # Mock responses including an empty git status (no changes to commit)
        mock_check_output.side_effect = [
            "git clone",           # git clone command
            "rpmdev-bumpspec",     # rpmdev-bumpspec command 
            "git config",          # git config user.name
            "git config",          # git config user.email
            b"",                   # git status --porcelain (empty = no changes)
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        output = self.builder.build(package, opts)

        # Verify that we get the expected output when skipping build
        assert output == {
            "build_id": 0,
            "patch": "",
            "patch_filename": "",
            "message": "Package is already up to date in the repository",
        }

    @mock.patch("hotness.builders.koji.sp.check_output") 
    @mock.patch("hotness.builders.koji.koji")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_with_changes(self, mock_temp_dir, mock_koji, mock_check_output, tmpdir):
        """
        Test that build continues normally when there are changes to commit.
        """
        # Create temporary files
        file = os.path.join(tmpdir, "Lectitio_Divinitatus")
        with open(file, "w") as f:
            f.write("The Emperor is God")

        # Mock patch file
        filename = "patch"
        file = os.path.join(tmpdir, filename)
        with open(file, "w") as f:
            f.write("This is a patch")
            
        mock_session = mock.Mock()
        mock_session.build.return_value = 1000
        mock_session.gssapi_login.return_value = True
        mock_koji.ClientSession.return_value = mock_session
        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        # Mock responses including a non-empty git status (there are changes)
        mock_check_output.side_effect = [
            "git clone",                           # git clone command
            "rpmdev-bumpspec",                     # rpmdev-bumpspec command
            "git config",                          # git config user.name  
            "git config",                          # git config user.email
            b" M test.spec\n",                     # git status --porcelain (has changes)
            "git commit",                          # git commit command
            filename.encode(),                     # git format-patch command
            b"Downloading Lectitio_Divinitatus",   # fedpkg sources
            b"Downloaded: Lectitio_Divinitatus",   # spectool command
            b"Wrote: foobar.srpm",                 # rpmbuild command
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        output = self.builder.build(package, opts)

        # Verify that build continues normally
        assert output["build_id"] == 1000
        assert output["patch"] == "This is a patch"
        assert output["patch_filename"] == filename
        # message field may contain source comparison info, just check it exists
        assert "message" in output

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_git_status_fails(self, mock_temp_dir, mock_check_output, tmpdir):
        """
        Test that build continues normally if git status command fails.
        """
        from subprocess import CalledProcessError
        
        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        # Mock git status to raise an exception, then normal flow should continue
        mock_check_output.side_effect = [
            "git clone",                                        # git clone command
            "rpmdev-bumpspec",                                  # rpmdev-bumpspec command 
            "git config",                                       # git config user.name
            "git config",                                       # git config user.email
            CalledProcessError(1, "git status"),               # git status fails
            CalledProcessError(1, "git commit"),               # git commit fails (normal test flow)
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        # Should raise BuilderException due to git commit failure
        from hotness.exceptions import BuilderException
        with pytest.raises(BuilderException):
            self.builder.build(package, opts)
