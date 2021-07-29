# -*- coding: utf-8 -*-
#
# Copyright © 2021  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
"""
Tests for the `hotness.config` module.
"""
import unittest

from hotness import config as hotness_config

full_config = {
    "consumer_config": {
        "pdc_url": "https://pdc.stg.fedoraproject.org",
        "dist_git_url": "https://src.stg.fedoraproject.org",
        "mdapi_url": "https://apps.fedoraproject.org/mdapi_test",
        "repoid": "",
        "distro": "",
        "hotness_issue_tracker": "https://github.com/fedora-infra/the-new-hotness/issues",
        "connect_timeout": 30,
        "read_timeout": 30,
        "requests_retries": 1,
        "bugzilla": {
            "enabled": False,
            "url": "https://partner-bugzilla.redhat.com_test",
            "user": "",
            "password": "",
            "api_key": "",
            "product": "",
            "version": "",
            "keywords": "",
            "bug_status": "",
            "explanation_url": "https://fedoraproject.org/wiki/upstream_release_monitoring_test",
            "reporter": "",
            "short_desc_template": "",
            "description_template": "",
        },
        "koji": {
            "server": "https://koji.fedoraproject.org/kojihub_test",
            "weburl": "https://koji.fedoraproject.org/koji_test",
            "krb_principal": "krb_principal",
            "krb_keytab": "krb_keytab",
            "krb_ccache": "krb_ccache",
            "krb_proxyuser": "krb_proxyuser",
            "krb_sessionopts": {"timeout": 600, "krb_rdns": True},
            "git_url": "https://src.stg.fedoraproject.org/cgit/rpms/{package}.git",
            "user_email": [],
            "opts": {"scratch": False},
            "priority": 60,
            "target_tag": "",
        },
    }
}

empty_config = {"consumer_config": {}}

empty_dict_config = {"consumer_config": {"bugzilla": {}}}

bad_config = {"consumer_config": {"example_key": "value"}}


class TestLoad(unittest.TestCase):
    """
    Class for testing the `hotness.config.load` function.
    """

    maxDiff = None

    def test_load_full_config(self):
        """
        Assert that config will be changed when correct dictionary is provided.
        """
        config = hotness_config.load(full_config)
        self.assertEqual(config, full_config["consumer_config"])

    def test_load_empty_config(self):
        """
        Assert that default values will be used when empty dictionary is provided.
        """
        config = hotness_config.load(empty_config)
        self.assertEqual(config, hotness_config.DEFAULTS)

    def test_load_empty_inner_dict(self):
        """
        Assert that default values will be used when empty inner dictionary is provided.
        """
        config = hotness_config.load(empty_dict_config)
        self.assertEqual(config, hotness_config.DEFAULTS)

    def test_load_bad_config(self):
        """
        Assert that unrecognized value will be skipped.
        """
        config = hotness_config.load(bad_config)
        self.assertEqual(config, hotness_config.DEFAULTS)
