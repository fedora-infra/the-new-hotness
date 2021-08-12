# -*- coding: utf-8 -*-
#
# This file is part of the-new-hotness project.
# Copyright (C) 2021  Red Hat, Inc.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.
from unittest import mock

from hotness.domain import Package
from hotness.patchers import Pagure


class TestPagureInit:
    """
    Test class for `hotness.notifiers.Bugzilla.__init__` method.
    """

    @mock.patch("hotness.patchers.pagure.Config.load_authentication")
    def test_init(self, packit_load_authentication):
        """
        Assert that Pagure patcher object is initialized correctly.
        """
        dist_git_url = "https://example.com"
        pagure_user_token = "TopSecretInquisitionMaterial"
        fas_user = "sebastian.thor"
        changelog_template = "Inquisitorial archive {}"
        pr_template = "This is a confident information. Check your access before reading."

        packit_load_authentication.return_value = []

        patcher = Pagure(
            dist_git_url,
            pagure_user_token,
            fas_user,
            changelog_template,
            pr_template
        )

        packit_load_authentication.assert_called_with({
            "authentication": {
                "pagure": {
                    "token": pagure_user_token,
                    "instance_url": dist_git_url,
                }
            }
        })

        assert patcher.dist_git_url == dist_git_url
        assert patcher.config.fas_user == fas_user
        assert patcher.config.services == []
        assert patcher.changelog_template == changelog_template
        assert patcher.pr_template == pr_template

class TestPagureSubmitPatch:
    """
    Test class for `hotness.patchers.Pagure.submit_patch` method.
    """

    #@mock.patch("hotness.patchers.pagure.Config.load_authentication")
    #def setup(self, packit_load_authentication):
    def setup(self):
        """
        Create patcher instance for tests.
        """
        dist_git_url = "https://src.stg.fedoraproject.org/"
        pagure_user_token = "GVFVWOG7ZSBDN7E0738V1CSEDBDK47NBF1I4PW0WOL3AKKX743UZCCOVA4Z9LL21"
        fas_user = "zlopez"
        changelog_template = "Update to {version}"
        pr_template = "This is a testing PR for {package} to version {version} with test bugzilla url '{bugzilla_url}'"
#        dist_git_url = "https://example.com"
#        pagure_user_token = "TopSecretInquisitionMaterial"
#        fas_user = "sebastian.thor"
#        changelog_template = "Inquisitorial archive {}"
#        pr_template = "This is a confident information. Check your access before reading."
#
#        packit_load_authentication.return_value = []

        self.patcher = Pagure(
            dist_git_url,
            pagure_user_token,
            fas_user,
            changelog_template,
            pr_template
        )

#        packit_load_authentication.assert_called_with({
#            "authentication": {
#                "pagure": {
#                    "token": pagure_user_token,
#                    "instance_url": dist_git_url,
#                }
#            }
#        })

        assert self.patcher.dist_git_url == dist_git_url
        assert self.patcher.config.fas_user == fas_user
        #assert self.patcher.config.services == []
        assert self.patcher.changelog_template == changelog_template
        assert self.patcher.pr_template == pr_template

    def test_submit_patch(self):
        """
        Assert that submit_patch works correctly.
        """
        # Prepare package
        package = Package(name="python-semver", version="9.00", distro="Fedora")

        opts = {
            "bugzilla_url": "https://bugzilla.redhat.com/show_bug.cgi?id=100",
            "staging": True
        }

        output = self.patcher.submit_patch(package, "", opts)

        assert output["pull_request_url"].startswith(
            "https://src.stg.fedoraproject.org/rpms/python-semver/pull-request/"
        )
