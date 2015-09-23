from nose.tools import eq_

import hotness.helpers

class TestHelpers(object):
    def test_upstream_cmp(self):
        cases = [
            ('1',       '2',        -1),
            ('2',       '1',        1),
            ('1',       '1',        0),
            ('1.0',     '1.0',      0),
            ('2.0',     '1.0',      1),
            ('1.0.a',   '1.0',      1),
            ('1.0.a',   '1.1',      -1),
        ]
        for v1, v2, result in cases:
            yield self._check_upstream_cmp, v1, v2, result

    def _check_upstream_cmp(self, v1, v2, result):
        eq_(hotness.helpers.upstream_cmp(v1, v2), result)

    def test_cmp_upstream_repo(self):
        cases = [
            ('1',       ('2',   '1'),      -1),
            ('2',       ('1',   '1'),      1),
            ('1',       ('1',   '1'),      0),
            ('1.0',     ('1.0', '1'),      0),
            ('2.0',     ('1.0', '1'),      1),
            ('1.0.a',   ('1.0', '1'),      1),
            ('1.0.a',   ('1.1', '1'),      -1),
            ('1.1',     ('1.1', '1'),      0),
            ('1.1',     ('1.1', '2'),      0),
        ]
        for upstream_v, repo_vr, result in cases:
            yield self._check_cmp_upstream_repo, upstream_v, repo_vr, result

    def _check_cmp_upstream_repo(self, upstream_v, repo_vr, result):
        eq_(hotness.helpers.cmp_upstream_repo(upstream_v, repo_vr), result)
