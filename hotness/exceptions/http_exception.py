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
from . import BaseHotnessException


class HTTPException(BaseHotnessException):
    """
    Class representing HTTP exception. This exception should be returned by any wrapper receiving
    HTTP response when the error code is not 200.

    Attributes:
        error_code: Error code of the response
        message: Error message.
    """

    def __init__(self, error_code: int, message: str):
        """
        Class constructor.
        """
        self.error_code = error_code
        self.message = message
        super(HTTPException, self).__init__(self.message)

    def __str__(self):
        """
        String representation of error.
        """
        return f"Error code: {self.error_code}\n" f"Error message: {self.message}"
