"""
Unit tests for hotness.helpers
"""
from __future__ import unicode_literals, absolute_import

import unittest

from hotness import helpers


class TestHelpers(unittest.TestCase):
    def test_rpm_cmp(self):
        cases = [
            ("rc1", "pre1", 1),
            ("beta1", "pre1", -1),
            ("beta1", "alpha1", 1),
            ("rc1", "rc2", -1),
            ("rc3", "rc2", 1),
            ("rc3", "rc3", 0),
            ("rc1", "rc", 1),
            ("rc", "rc1", -1),
            ("rc", "rc", 0),
        ]
        for v1, v2, result in cases:
            self.assertEqual(helpers.rpm_cmp(v1, v2), result)

    def test_rpm_max(self):
        cases = [
            (["rc1", "rc2", "rc3"], "rc3"),
            (["pre6", "pre5", "pre4"], "pre6"),
            (["beta8", "beta9", "beta7"], "beta9"),
            (["alpha1", "alpha2", "alpha3"], "alpha3"),
            (["dev6", "dev5", "dev4"], "dev6"),
        ]
        for versions, result in cases:
            self.assertEqual(helpers.rpm_max(versions), result)

    def test_upstream_cmp(self):
        cases = [
            ("1", "2", -1),
            ("2", "1", 1),
            ("1", "1", 0),
            ("1.0", "1.0", 0),
            ("2.0", "1.0", 1),
            ("1.0.a", "1.0", 1),
            ("1.0.a", "1.1", -1),
            ("2.0.rc1", "2.0.pre1", 1),
            ("2.0.beta1", "2.0.pre1", -1),
            ("2.0.beta1", "2.0.alpha1", 1),
            ("1.0.rc1", "1.0.rc2", -1),
            ("1.0.rc3", "1.0.rc2", 1),
            ("2.0.0.rc3", "2.0.0.rc3", 0),
            ("2.0.0.rc1", "2.0.0.rc", 1),
            ("2.0.0.rc", "2.0.0.rc1", -1),
            ("2.0.0.rc", "2.0.0.rc", 0),
            ("3.0.0rc1", "3.0.0", -1),
            ("3.0.0", "3.0.0rc1", 1),
        ]
        for v1, v2, result in cases:
            self.assertEqual(helpers.upstream_cmp(v1, v2), result)

    def test_split_rc(self):
        cases = [
            ("1.0.0.rc1", ("1.0.0", "rc", "1")),
            ("2.3.pre4", ("2.3", "pre", "4")),
            ("4.56.beta7", ("4.56", "beta", "7")),
            ("7.8.90-alpha1", ("7.8.90", "alpha", "1")),
            ("23.4-dev5", ("23.4", "dev", "5")),
            ("1.0.0", ("1.0.0", "", "")),
            ("1.8.23-20100128-r1100", ("1.8.23-20100128-r1100", "", "")),
        ]
        for version, result in cases:
            self.assertEqual(helpers.split_rc(version), result)

    def test_get_rc(self):
        cases = [
            ("0.1.rc2", ("rc", "2")),
            ("0.3.pre4", ("pre", "4")),
            ("0.5.beta6", ("beta", "6")),
            ("0.7.alpha7", ("alpha", "7")),
            ("0.8.dev9", ("dev", "9")),
            ("1.0.rc1", ("", "")),
        ]
        for version, result in cases:
            self.assertEqual(helpers.get_rc(version), result)

    def test_upstream_max(self):
        cases = [
            (["1.0.0", "2.0.0", "3.0.0"], "3.0.0"),
            (["3.0", "2.0", "3.0"], "3.0"),
            (["1.0.0.rc1", "1.0.0.rc2", "1.0.0.rc3"], "1.0.0.rc3"),
            (["1.0.rc1", "1.0.rc2", "1.0"], "1.0"),
        ]
        for versions, result in cases:
            self.assertEqual(helpers.upstream_max(versions), result)

    def test_cmp_upstream_repo(self):
        cases = [
            ("1", ("2", "1"), -1),
            ("2", ("1", "1"), 1),
            ("1", ("1", "1"), 0),
            ("1.0", ("1.0", "1"), 0),
            ("2.0", ("1.0", "1"), 1),
            ("1.0.a", ("1.0", "1"), 1),
            ("1.0.a", ("1.1", "1"), -1),
            ("1.1", ("1.1", "1"), 0),
            ("1.1", ("1.1", "2"), 0),
        ]
        for upstream_v, repo_vr, result in cases:
            self.assertEqual(helpers.cmp_upstream_repo(upstream_v, repo_vr), result)

    def test_filter_dict(self):
        test_dict = {"a": 1, "b": 2, "c": 3, "d": 4}
        self.assertEqual(helpers.filter_dict(test_dict, ["b", "d"]), {"b": 2, "d": 4})
