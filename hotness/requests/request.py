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
class Request:
    """
    Parent class for requests. Defines error management methods for requests.
    Every request class inherits this class and adds error during validation of
    attributes. Attributes are validated during initialization phase.

    Attributes:
        errors (list): List of errors, every entry is dict containing parameter
                       and error related to this parameter.
    """

    def __init__(self) -> None:
        """
        Class contructor.
        """
        self.errors = []

    def add_error(self, parameter: str, error: str) -> None:
        """
        Adds error to `self.errors`.

        Params:
            parameter: Parameter for which the error is added.
            error: Error encountered during validation of parameter.
        """
        self.errors.append({"parameter": parameter, "error": error})

    def __bool__(self) -> bool:
        """
        Validates the request and returns appropriate response.

        Returns:
            True if `self.errors` is empty, False otherwise.
        """
        return self.errors == []
