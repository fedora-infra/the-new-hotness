# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc.
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
"""Unit tests for :mod:`hotness.anitya`."""

import unittest

from hotness import anitya


class DetermineBackendTests(unittest.TestCase):
    """Unit tests for :meth:`hotness.anitya.Anitya.determine_backend`."""

    def test_no_backend_found(self):
        self.assertRaises(anitya.AnityaException, anitya.determine_backend,
                          'nonsense-package-name', 'http://example.com/home')

    def test_backend_ruby_prefix(self):
        """Assert packages with the ``rubygem-`` prefix receive the Rubygems backend."""
        backend = anitya.determine_backend('rubygem-myproject', 'http://example.com/home')
        self.assertEqual('Rubygems', backend)

    def test_backend_ruby_homepage(self):
        """Assert packages with a ``rubygems.org`` homepage receive the Rubygems backend."""
        backend = anitya.determine_backend('ishouldhaveaprefix-project', 'http://rubygems.org/home')
        self.assertEqual('Rubygems', backend)
