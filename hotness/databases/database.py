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
class Database:
    """
    Abstract class for databases used by the-new-hotness to store key/value pairs.
    This class must be inherited by every external database.
    """

    def insert(self, key: str, value: str) -> dict:
        """
        Insert method that should be implemented by every child class.

        It should insert key/value pair to database using the external system and
        return dictionary containing any related info.

        In case of any issue that would prevent inserting the data, method should
        raise an exception.
        """
        raise NotImplementedError

    def retrieve(self, key: str) -> dict:
        """
        Retrieve method that should be implemented by every child class.

        It should retrieve value for key from database using the external system and
        return dictionary containing any related info.

        In case of any issue that would prevent retrieving the data, method should
        raise an exception.
        """
        raise NotImplementedError
