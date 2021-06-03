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
from hotness.common import RPM

import pytest


class TestRPMCompare:
    """
    Test class for `hotness.common.RPM.compare` method.
    """

    @pytest.mark.parametrize(
        "v1,v2,result",
        [
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
        ],
    )
    def test_compare(self, v1, v2, result):
        """
        Assert that compare works correctly for rpm.
        """
        assert RPM.compare(v1, v2) == result
