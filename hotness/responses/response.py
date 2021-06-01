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
from typing import Any


class Response:
    """
    Abstract class for response object. Defines shared methods
    for both Success and Failure response.
    """

    def __bool__(self) -> bool:
        """
        This method is used for checking if the response is failure or success.
        Needs to be implemented by every child class.

        Returns:
           True if success, False if failure.
        """
        raise NotImplementedError

    @property
    def value(self) -> Any:
        """
        This property should contain the value of the response, either error or data.
        Needs to be implemented by every child.

        Returns:
            Any value that represents the response from use case.
        """
        raise NotImplementedError
