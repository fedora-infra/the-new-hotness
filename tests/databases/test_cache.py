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
from hotness.databases import Cache


class TestCacheInit:
    """
    Test class for `hotness.databases.Cache.__init__` method.
    """

    def test_init(self):
        """
        Assert that database object is correctly initialized.
        """
        database = Cache()

        assert database.cache == {}


class TestCacheInsert:
    """
    Test class for `hotness.databases.Cache.insert` method.
    """

    def setup(self):
        """
        Create database instance for tests.
        """
        self.database = Cache()

    def test_insert(self):
        """
        Assert that insert works correctly.
        """
        key = "key"
        value = "value"

        output = self.database.insert(key, value)

        assert output == {"key": key, "value": value, "old_value": ""}
        assert self.database.cache == {key: value}

    def test_insert_key_already_exists(self):
        """
        Assert that insert changes the value if key is already present.
        """
        key = "key"
        old_value = "old_value"
        value = "value"

        self.database.cache = {key: old_value}

        output = self.database.insert(key, value)

        assert output == {"key": key, "value": value, "old_value": old_value}
        assert self.database.cache == {key: value}


class TestCacheRetrieve:
    """
    Test class for `hotness.databases.Cache.retrieve` method.
    """

    def setup(self):
        """
        Create database instance for tests.
        """
        self.database = Cache()

    def test_retrieve(self):
        """
        Assert that retrieve works correctly.
        """
        key = "key"
        value = "value"

        self.database.cache = {key: value}

        output = self.database.retrieve(key)

        assert output == {"key": key, "value": value}

    def test_retrieve_key_is_missing(self):
        """
        Assert that retrieve returns empty value, if key is not found in cache.
        """
        key = "key"

        output = self.database.retrieve(key)

        assert output == {"key": key, "value": ""}
