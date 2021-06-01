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


class Patcher:
    """
    Abstract class for patchers used by the-new-hotness to submit a patch.
    This class must be inherited by every external patcher.
    """

    def submit_patch(self, package: Package, patch: str, opts: dict) -> dict:
        """
        Submit patch method that should be implemented by every child class.

        It should submit patch for package to external system and
        return dictionary containing additional info.

        In case of any issue that would prevent submitting the patch, method should
        raise an exception.

        Params:
            package: Package to attach patch for
            patch: Patch to attach
            opts: Optional arguments specific for the external patcher system
        """
        raise NotImplementedError
