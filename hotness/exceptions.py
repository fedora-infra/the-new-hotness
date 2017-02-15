# -*- coding: utf-8 -*-
#
# This file is part of the-new-hotness project.
# Copyright (C) 2017  Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""
This module contains exceptions raised by the-new-hotness.
"""


class HotnessException(Exception):
    """The base exception class for all hotness-related errors"""


class SpecUrlException(HotnessException, ValueError):
    """Raised when a specfile's Source URLs don't work with the-new-hotness"""


class DownloadException(HotnessException, IOError):
    """Raised when a networking-related download error occurs"""
