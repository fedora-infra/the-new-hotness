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
from . import PackageRequest


class NotifyRequest(PackageRequest):
    """
    This class represents request, which will be sent to use cases sending notifications,
    like notifiers.

    Attributes:
        package: Package sent with request.
        message: Message to sent.
        opts: Additional options for specific notifier.
    """

    def __init__(self, package: Package, message: str, opts: dict) -> None:
        """
        Class constructor.
        """
        super(NotifyRequest, self).__init__(package)
        self.message = message
        self.opts = opts
