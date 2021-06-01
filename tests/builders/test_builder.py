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
import pytest
from unittest import mock

from hotness.builders import Builder


class TestBuilderBuild:
    """
    Test class for `hotness.builders.Builder.build` method.
    """

    def test_build(self):
        """
        Assert that build in abstract class raise NotImplementedError.
        """
        package = mock.Mock()
        builder = Builder()
        opts = {}

        with pytest.raises(NotImplementedError):
            builder.build(package, opts)
