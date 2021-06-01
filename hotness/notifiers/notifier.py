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


class Notifier:
    """
    Abstract class for notifiers used by the-new-hotness to sent a notification.
    This class must be inherited by every external notifier.
    """

    def notify(self, package: Package, message: str, opts: dict) -> dict:
        """
        Notify method that should be implemented by every child class.

        It should sent notification using the external system and
        return dictionary containing any related info.

        In case of any issue that would prevent sending a notification, method should
        raise an exception.

        Params:
           package: Package to notify about.
           message: Message to sent.
           opts: Additional options for specific notifier.

        Returns:
           Dictionary containing output of the operation.
        """
        raise NotImplementedError
