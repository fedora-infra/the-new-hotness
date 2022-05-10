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
import mock

from hotness.databases import Redis


class TestRedisInit:
    """
    Test class for `hotness.databases.Redis.__init__` method.
    """

    @mock.patch("hotness.databases.redis.redis")
    def test_init(self, mock_redis):
        """
        Assert that database object is correctly initialized.
        """
        # Preparation
        hostname = "hostname"
        port = 1234
        password = "password"
        expiration_time = 86400
        redis_mock_instance = mock.Mock()
        mock_redis.Redis.return_value = redis_mock_instance

        # Test
        database = Redis(
            hostname=hostname,
            port=port,
            password=password,
            expiration_time=expiration_time,
        )

        # Asserts
        mock_redis.Redis.assert_called_with(host=hostname, port=port, password=password)

        assert database.redis == redis_mock_instance
        assert database.expiration_time == expiration_time


class TestRedisInsert:
    """
    Test class for `hotness.databases.Redis.insert` method.
    """

    def setup(self):
        """
        Create database instance for tests.
        """
        with mock.patch("hotness.databases.redis.redis") as mock_redis:
            redis_mock_instance = mock.Mock()
            mock_redis.Redis.return_value = redis_mock_instance

            self.database = Redis(
                hostname="", port=1234, password="", expiration_time=86400
            )

    def test_insert(self):
        """
        Assert that insert works correctly.
        """
        # Preparation
        key = "key"
        value = "value"

        self.database.redis.set.return_value = None

        # Test
        output = self.database.insert(key, value)

        # Asserts
        assert output == {"key": key, "value": value, "old_value": ""}
        self.database.redis.set.assert_called_with(
            key, value, ex=self.database.expiration_time, get=True
        )

    def test_insert_key_already_exists(self):
        """
        Assert that insert changes the value if key is already present.
        """
        # Preparation
        key = "key"
        old_value = "old_value"
        value = "value"

        self.database.redis.set.return_value = old_value

        # Test
        output = self.database.insert(key, value)

        # Asserts
        assert output == {"key": key, "value": value, "old_value": old_value}
        self.database.redis.set.assert_called_with(
            key, value, ex=self.database.expiration_time, get=True
        )


class TestRedisRetrieve:
    """
    Test class for `hotness.databases.Redis.retrieve` method.
    """

    def setup(self):
        """
        Create database instance for tests.
        """
        with mock.patch("hotness.databases.redis.redis") as mock_redis:
            redis_mock_instance = mock.Mock()
            mock_redis.Redis.return_value = redis_mock_instance

            self.database = Redis(
                hostname="", port=1234, password="", expiration_time=86400
            )

    def test_retrieve(self):
        """
        Assert that retrieve works correctly.
        """
        # Preparation
        key = "key"
        value = "value"

        self.database.redis.get.return_value = value

        # Test
        output = self.database.retrieve(key)

        # Asserts
        assert output == {"key": key, "value": value}
        self.database.redis.get.assert_called_with(key)

    def test_retrieve_key_is_missing(self):
        """
        Assert that retrieve returns empty value, if key is not found in database.
        """
        # Preparation
        key = "key"

        self.database.redis.get.return_value = None

        # Test
        output = self.database.retrieve(key)

        # Asserts
        assert output == {"key": key, "value": ""}
        self.database.redis.get.assert_called_with(key)
