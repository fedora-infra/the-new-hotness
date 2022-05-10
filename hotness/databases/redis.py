# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 Red Hat, Inc.
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
import redis

from . import Database


class Redis(Database):
    """
    Wrapper around redis-py library.
    It establishes connection with Redis database and allows user to
    save and retrieves values from it.

    Attributes:
        redis (`redis.Redis`): Redis object to use for communication with Redis
            database
        expiration_time (int): Expiration time to use on keys (in seconds)
    """

    def __init__(
        self, hostname: str, port: int, password: str, expiration_time: int
    ) -> None:
        """
        Class constructor.

        Params:
            hostname: Hostname of the Redis database
            port: Port of the Redis database
            password: Password to use for connecting to Redis database
            expiration_time: Expiration time to set for keys (in seconds)
        """
        self.redis = redis.Redis(host=hostname, port=port, password=password)

        self.expiration_time = expiration_time

    def insert(self, key: str, value: str) -> dict:
        """
        It inserts key/value pair to redis. If key is already in redis
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
        output = {"key": key, "value": value, "old_value": ""}

        old_value = self.redis.set(key, value, ex=self.expiration_time, get=True)

        if old_value:
            output["old_value"] = str(old_value)

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
        output = {"key": key, "value": ""}

        value = self.redis.get(key)

        if value:
            output["value"] = str(value)

        return output
