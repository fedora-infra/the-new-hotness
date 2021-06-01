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
from . import Request


class InsertDataRequest(Request):
    """
    This class represents request, which contain key/value pair to store in database for
    later use.

    Attributes:
        key: Key for the key/value pair.
        value: Value for the key/value pair.
    """

    def __init__(self, key: str, value: str) -> None:
        """
        Class constructor.
        """
        super(InsertDataRequest, self).__init__()
        self.key = key
        self.value = value
