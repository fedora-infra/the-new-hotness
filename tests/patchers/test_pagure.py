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
