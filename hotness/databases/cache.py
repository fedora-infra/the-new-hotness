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
from . import Database


class Cache(Database):
    """
    Wrapper for the cache for the-new-hotness.
    It is represented by python dictionary.

    Attributes:
        cache (dict): Dictionary to hold key/value pairs
    """

    def __init__(self) -> None:
        """
        Class constructor.
        """
        super(Cache, self).__init__()
        self.cache = {}

    def insert(self, key: str, value: str) -> dict:
        """
        It insert key/value pair to cache. If key is already in cache
        it will change the value.

        Params:
            key: Key to insert to database
            value: Value for the key to add

        Returns:
            Dictionary containing key/value pairs.
            Example:
            {
              "key": "key", # Key we added/edited in database
              "value": "value", # New value added to the key
              "old_value": "old_value" # Old value for the key, empty if the key is new
            }
        """
        output = {"key": key, "value": value, "old_value": self.cache.get(key, "")}

        self.cache[key] = value

        return output

    def retrieve(self, key: str) -> dict:
        """
        Retrieve value for a key in database. If the key is not available
        it returns empty value represented by "".

        Params:
            key: Key to retrieve from database

        Returns:
            Dictionary containing key/value pairs.
            Example:
            {
              "key": "key", # Key we retrieved from database
              "value": "value" # Retrieved value for the key
            }
        """
        output = {"key": key, "value": self.cache.get(key, "")}

        return output
