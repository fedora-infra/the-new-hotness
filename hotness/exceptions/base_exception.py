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


class BaseHotnessException(Exception):
    """
    Class representing base exception in the-new-hotness.
    This exception should be inherited by every other exception
    and defines common methods and attributes expected by `ResponseFailure` object.

    Attributes:
        message: Error message.
        value: Partial output from object that raised the exception, default: None.
    """

    def __init__(
        self,
        message: str,
        value: Optional[Any] = None,
    ) -> None:
        """
        Class constructor.
        """
        self.message = message
        self.value = value
        super(BaseHotnessException, self).__init__(self.message)

    def __str__(self) -> str:
        """
        String representation of error.
        """
        return self.message
