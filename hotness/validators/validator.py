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
from hotness.domain.package import Package


class Validator:
    """
    Abstract class for validators used by the-new-hotness to validate the package.
    This class must be inherited by every external validator.
    """

    def validate(self, package: Package) -> dict:
        """
        Validation method that should be implemented by every child class.

        Params:
            package: Package to validate.

        Returns:
            Output of validation in form of dictionary.
        """
        raise NotImplementedError
