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


class Package:
    """
    Internal representation of package object.

    Attributes:
        name (str): Name of the package
        version (str): Latest version of the package
        distro (str): Distribution assigned
    """

    def __init__(self, name: str, version: str, distro: str) -> None:
        """
        Class constructor
        """
        self.name = name
        self.version = version
        self.distro = distro

    def to_dict(self) -> dict:
        """
        Convert object to dictionary.

        Return:
            Dictionary created from package object.
        """
        return {"name": self.name, "version": self.version, "distro": self.distro}

    @classmethod
    def from_dict(cls, package_dict: dict) -> object:
        """
        Convert dictionary to object.

        Params:
            package_dict: Dictionary to create package from.

        Return:
            Package object.
        """
        package = Package(
            name=package_dict["name"],
            version=package_dict["version"],
            distro=package_dict["distro"],
        )
        return package

    def __eq__(self, other: object) -> bool:
        """
        Compare method for package object.

        Params:
            other: object to compare with

        Return:
            Compare result.
        """
        return self.to_dict() == other.to_dict()
