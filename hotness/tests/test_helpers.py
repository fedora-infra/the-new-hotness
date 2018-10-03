"""
Unit tests for hotness.helpers
"""
from __future__ import unicode_literals, absolute_import

import unittest

from hotness import helpers


class TestHelpers(unittest.TestCase):
    def test_upstream_cmp(self):
        cases = [
            ("1", "2", -1),
            ("2", "1", 1),
            ("1", "1", 0),
            ("1.0", "1.0", 0),
            ("2.0", "1.0", 1),
            ("1.0.a", "1.0", 1),
            ("1.0.a", "1.1", -1),
        ]
        for v1, v2, result in cases:
            self.assertEqual(helpers.upstream_cmp(v1, v2), result)

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
