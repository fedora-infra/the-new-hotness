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

from hotness.databases import Database


class TestDatabaseInsert:
    """
    Test class for `hotness.databases.Database.insert` method.
    """

    def test_insert(self):
        """
        Assert that insert in abstract class raise NotImplementedError.
        """
        key = "key"
        value = "value"
        database = Database()

        with pytest.raises(NotImplementedError):
            database.insert(key, value)


class TestDatabaseRetrieve:
    """
    Test class for `hotness.databases.Database.retrieve` method.
    """

    def test_retrieve(self):
        """
        Assert that retrieve in abstract class raise NotImplementedError.
        """
        key = "key"
        database = Database()

        with pytest.raises(NotImplementedError):
            database.retrieve(key)
