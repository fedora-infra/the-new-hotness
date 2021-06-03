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
from typing import Any, Optional

from hotness.responses.response import Response


class ResponseSuccess(Response):
    """
    Class that represents successful response returned from use case.
    It has type SUCCESS and bool method returns true.

    Attributes:
        value: Value returned from the use case.
    """

    SUCCESS = "Success"

    def __init__(self, value: Optional[Any]) -> None:
        """
        Class constructor.
        """
        self.type = self.SUCCESS
        self.result = value

    def __bool__(self) -> bool:
        """
        Boolean representation of response.
        """
        return True

    @property
    def value(self) -> Any:
        """
        Returns the value represented by this response.

        Returns:
            Any value obtained from the use case.
        """
        return self.result
