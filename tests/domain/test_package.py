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


class TestPackageInit:
    """
    Test class for `hotness.domain.package.__init__` method.
    """

    def test_init_correct(self):
        """
        Assert that the object is correctly created.
        """
        package = Package(name="name", version="1.0.0-rc1", distro="Fedora")

        assert package.name == "name"
        assert package.version == "1.0.0-rc1"
        assert package.distro == "Fedora"


class TestPackageToDict:
    """
    Test class for `hotness.domain.package.to_dict` method.
    """

    def test_to_dict(self):
        """
        Test object conversion to dict.
        """
        package = Package(name="name", version="1.0.0-rc1", distro="Fedora")

        package_dict = {"name": "name", "version": "1.0.0-rc1", "distro": "Fedora"}

        assert package.to_dict() == package_dict


class TestPackageFromDict:
    """
    Test class for `hotness.domain.package.from_dict` method.
    """

    def test_from_dict(self):
        """
        Test object creation from dict.
        """
        package_dict = {"name": "name", "version": "1.0.0-rc1", "distro": "Fedora"}

        package = Package.from_dict(package_dict)

        assert package.name == "name"
        assert package.version == "1.0.0-rc1"
        assert package.distro == "Fedora"


class TestPackageEq:
    """
    Test class for `hotness.domain.package.__eq__` method.
    """

    def test_compare_identical(self):
        """
        Test the comparison of identical objects.
        """
        package1 = Package(name="name", version="1.0.0", distro="Fedora")

        package2 = Package(name="name", version="1.0.0", distro="Fedora")

        assert package1 == package2

    def test_compare_different(self):
        """
        Test the comparison of different objects.
        """
        package1 = Package(name="name", version="1.0.0", distro="Fedora")

        package2 = Package(name="name", version="1.0.1", distro="Fedora")

        assert not package1 == package2
