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
from unittest import mock

from hotness.requests import NotifyRequest


class TestNotifyRequestInit:
    """
    Test class for `hotness.requests.NotifyRequest.__init__`.
    """

    def test_init(self):
        """
        Assert that request object is correctly created.
        """
        package = mock.Mock()
        opts = {}

        request = NotifyRequest(package=package, message="message", opts=opts)

        assert request.package == package
        assert request.message == "message"
        assert request.opts == {}
