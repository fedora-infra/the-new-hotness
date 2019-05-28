# -*- coding: utf-8 -*-

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
"""Unit tests for :module:`hotness.buildsys`"""
from __future__ import absolute_import, unicode_literals

import os
import shutil
import subprocess
import tempfile
import unittest

import mock

from hotness import buildsys, exceptions


class KojiTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "server": None,
            "weburl": None,
            "krb_principal": None,
            "krb_keytab": None,
            "krb_ccache": None,
            "krb_sessionopts": None,
            "krb_proxyuser": None,
            "git_url": None,
            "user_email": ["Jeremy", "<jeremy@example.com>"],
            "opts": None,
            "priority": None,
            "target_tag": None,
        }

    def test_initialization_userstring_str(self):
        """Assert that a string for the 'userstring' config is parsed to user_email"""
        self.config["userstring"] = "Jeremy <jeremy@example.com>"
        del self.config["user_email"]
        koji = buildsys.Koji(None, self.config)
        self.assertEqual(["Jeremy", "<jeremy@example.com>"], koji.email_user)

    def test_initialization_user_email_tuple(self):
        """Assert that a tuple for the 'user_email' config option works"""
        koji = buildsys.Koji(None, self.config)
        self.assertEqual(["Jeremy", "<jeremy@example.com>"], koji.email_user)


@mock.patch("hotness.buildsys.sp.check_output")
@mock.patch("hotness.buildsys._validate_spec_urls")
class SpecSourcesTests(unittest.TestCase):
    """Tests for the :func:`buildsys.spec_sources` function"""

    def test_multiple_sources(self, mock_validate, mock_check_output):
        mock_check_output.return_value = """
Getting https://github.com/org/proj/archive/0.11.0/proj-0.11.0.tar.gz to ./proj-0.11.0.tar.gz
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   146    0   146    0     0    120      0 --:--:--  0:00:01 --:--:--   120
100   133    0   133    0     0     72      0 --:--:--  0:00:01 --:--:--    72
100 2695k    0 2695k    0     0   211k      0 --:--:--  0:00:12 --:--:--  233k
Getting https://github.com/org/other/archive/1.0/other-1.0.tar.gz to ./other-1.0.tar.gz
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   147    0   147    0     0    145      0 --:--:--  0:00:01 --:--:--   145
100   133    0   133    0     0    108      0 --:--:--  0:00:01 --:--:--   108
100 2695k  100 2695k    0     0  96565      0  0:00:28  0:00:28 --:--:-- 72941
Getting https://example.com/fix-everything.patch to ./fix-everything.patch
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   148    0   148    0     0     95      0 --:--:--  0:00:01 --:--:--    95
100   133    0   133    0     0     75      0 --:--:--  0:00:01 --:--:--  129k
100 2695k  100 2695k    0     0   135k      0  0:00:19  0:00:19 --:--:-- 84347
"""
        expected_sources = [
            "/tmp/dir/proj-0.11.0.tar.gz",
            "/tmp/dir/other-1.0.tar.gz",
            "/tmp/dir/fix-everything.patch",
        ]
        sources = buildsys.spec_sources("/my/specfile.spec", "/tmp/dir/")
        self.assertEqual(expected_sources, sources)
        mock_validate.assert_called_with("/my/specfile.spec")

    def test_no_sources_spec(self, mock_validate, mock_check_output):
        mock_check_output.return_value = ""
        sources = buildsys.spec_sources("/my/specfile.spec", "/tmp/dir/")
        self.assertEqual([], sources)
        mock_validate.assert_called_with("/my/specfile.spec")

    def test_unknown_protocol(self, mock_validate, mock_check_output):
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "mock_cmd")
        self.assertRaises(
            exceptions.SpecUrlException,
            buildsys.spec_sources,
            "/my/specfile.spec",
            "/tmp/dir/",
        )
        mock_validate.assert_called_with("/my/specfile.spec")

    def test_host_unresolvable(self, mock_validate, mock_check_output):
        for err in (5, 6):
            mock_check_output.side_effect = subprocess.CalledProcessError(
                err, "mock_cmd"
            )
            with self.assertRaises(exceptions.DownloadException) as cm:
                buildsys.spec_sources("/my/specfile.spec", "/tmp/dir/")
                self.assertTrue("Unable to resolve the hostname" in cm.exception.msg)
        mock_validate.assert_called_with("/my/specfile.spec")

    def test_unable_to_connect(self, mock_validate, mock_check_output):
        mock_check_output.side_effect = subprocess.CalledProcessError(7, "mock_cmd")
        with self.assertRaises(exceptions.DownloadException) as cm:
            buildsys.spec_sources("/my/specfile.spec", "/tmp/dir/")
            self.assertTrue("Unable to connect to the host" in cm.exception.msg)
            mock_validate.assert_called_with("/my/specfile.spec")

    def test_not_http_200(self, mock_validate, mock_check_output):
        mock_check_output.side_effect = subprocess.CalledProcessError(
            22, "mock_cmd", output="404"
        )
        with self.assertRaises(exceptions.DownloadException) as cm:
            buildsys.spec_sources("/my/specfile.spec", "/tmp/dir/")
            self.assertTrue("An HTTP error occurred" in cm.exception.msg)
        mock_validate.assert_called_with("/my/specfile.spec")

    def test_bad_peer_cert(self, mock_validate, mock_check_output):
        mock_check_output.side_effect = subprocess.CalledProcessError(60, "mock_cmd")
        with self.assertRaises(exceptions.DownloadException) as cm:
            buildsys.spec_sources("/my/specfile.spec", "/tmp/dir/")
            self.assertTrue(
                "Unable to validate the TLS certificate" in cm.exception.msg
            )
        mock_validate.assert_called_with("/my/specfile.spec")

    def test_unhandled_error(self, mock_validate, mock_check_output):
        mock_check_output.side_effect = subprocess.CalledProcessError(42, "mock_cmd")
        with self.assertRaises(exceptions.DownloadException) as cm:
            buildsys.spec_sources("/my/specfile.spec", "/tmp/dir/")
            self.assertTrue("An unexpected error occurred" in cm.exception.msg)
        mock_validate.assert_called_with("/my/specfile.spec")


class CompareSourcesTests(unittest.TestCase):
    """Tests for the :func:`buildsys.compare_sources` function"""

    def setUp(self):
        self.old_source_dir = tempfile.mkdtemp()
        self.new_source_dir = tempfile.mkdtemp()
        self.old_source = os.path.join(self.old_source_dir, "old_source")
        self.old_sum = (
            "cba06b5736faf67e54b07b561eae94395e774c517a7d910a54369e1263ccfbd4"
        )
        self.new_sum = (
            "11507a0e2f5e69d5dfa40a62a1bd7b6ee57e6bcd85c67c9b8431b36fff21c437"
        )
        self.new_source = os.path.join(self.new_source_dir, "new_source")

        with open(self.old_source, "wb") as fd:
            fd.write(b"old")
        with open(self.new_source, "wb") as fd:
            fd.write(b"new")

    def tearDown(self):
        for d in (self.old_source_dir, self.new_source_dir):
            shutil.rmtree(self.old_source_dir, ignore_errors=True)

    def test_different_file(self):
        old, new = buildsys.compare_sources([self.old_source], [self.new_source])
        expected_old = set()
        expected_old.add(self.old_sum)
        expected_new = set()
        expected_new.add(self.new_sum)
        self.assertEqual(expected_old, old)
        self.assertEqual(expected_new, new)

    def test_shared_file(self):
        with open(self.new_source, "wb") as fd:
            fd.write(b"old")
        self.assertRaises(
            exceptions.SpecUrlException,
            buildsys.compare_sources,
            [self.old_source],
            [self.new_source],
        )


class DistGitSourcesTests(unittest.TestCase):
    """Tests for the :func:`buildsys.dist_git_sources` function"""

    @mock.patch("hotness.buildsys.sp.check_output")
    def test_multiple_sources(self, mock_check_output):
        """Assert multiple source downloads output are parsed neatly"""
        mock_check_output.return_value = b"""
Downloading requests-2.12.4.tar.gz
####################################################################### 100.0%
Downloading requests-2.12.4-tests.tar.gz
####################################################################### 100.0%
"""
        sources = buildsys.dist_git_sources("/my/repo")
        mock_check_output.assert_called_once_with(
            ["fedpkg", "--user", "hotness", "sources"], cwd="/my/repo"
        )
        self.assertEqual(
            [
                "/my/repo/requests-2.12.4.tar.gz",
                "/my/repo/requests-2.12.4-tests.tar.gz",
            ],
            sources,
        )

    @mock.patch("hotness.buildsys.sp.check_output")
    def test_single_source(self, mock_check_output):
        """Assert single source downloads output are parsed neatly"""
        mock_check_output.return_value = b"""
Downloading requests-2.13.0.tar.gz
####################################################################### 100.0%
"""
        sources = buildsys.dist_git_sources("/my/repo")
        mock_check_output.assert_called_once_with(
            ["fedpkg", "--user", "hotness", "sources"], cwd="/my/repo"
        )
        self.assertEqual(["/my/repo/requests-2.13.0.tar.gz"], sources)


class ValidateSpecUrlsTests(unittest.TestCase):
    """Tests for the :func:`buildsys.compare_sources` function"""

    @mock.patch("hotness.buildsys.sp.check_output")
    def test_valid_url(self, mock_check_output):
        mock_check_output.return_value = """
Source0: https://github.com/kennethreitz/requests/archive/v2.13.0/requests-v2.13.0.tar.gz
Patch0: python-requests-system-cert-bundle.patch
"""
        buildsys._validate_spec_urls("/my/package.spec")
        mock_check_output.assert_called_once_with(
            ["spectool", "-l", "/my/package.spec"]
        )

    @mock.patch("hotness.buildsys.sp.check_output")
    def test_invalid_url(self, mock_check_output):
        mock_check_output.return_value = """
Source0: requests-v2.13.0.tar.gz
Patch0: python-requests-system-cert-bundle.patch
"""
        self.assertRaises(
            exceptions.SpecUrlException,
            buildsys._validate_spec_urls,
            "/my/package.spec",
        )
        mock_check_output.assert_called_once_with(
            ["spectool", "-l", "/my/package.spec"]
        )

    @mock.patch("hotness.buildsys.sp.check_output")
    def test_no_scheme(self, mock_check_output):
        mock_check_output.return_value = """
Source0: example.com/requests-v2.13.0.tar.gz
Patch0: python-requests-system-cert-bundle.patch
"""
        self.assertRaises(
            exceptions.SpecUrlException,
            buildsys._validate_spec_urls,
            "/my/package.spec",
        )
        mock_check_output.assert_called_once_with(
            ["spectool", "-l", "/my/package.spec"]
        )

    @mock.patch("hotness.buildsys.sp.check_output")
    def test_no_host(self, mock_check_output):
        mock_check_output.return_value = """
Source0: https:///requests-v2.13.0.tar.gz
Patch0: python-requests-system-cert-bundle.patch
"""
        self.assertRaises(
            exceptions.SpecUrlException,
            buildsys._validate_spec_urls,
            "/my/package.spec",
        )
        mock_check_output.assert_called_once_with(
            ["spectool", "-l", "/my/package.spec"]
        )


if __name__ == "__main__":
    unittest.main()
