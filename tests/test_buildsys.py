# -*- coding: utf-8 -*-

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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.
"""Unit tests for :module:`hotness.buildsys`"""
from __future__ import absolute_import, unicode_literals

import unittest

import mock

from hotness import buildsys


class KojiTests(unittest.TestCase):

    def test_initialization_userstring_str(self):
        """Assert that a string for the 'userstring' config option works"""
        userstring = 'Jeremy <jeremy@example.com>'
        mock_config = mock.MagicMock()
        mock_config.__getitem__.return_value = userstring
        koji = buildsys.Koji(None, mock_config)
        self.assertEqual(userstring, koji.userstring)

    def test_initialization_userstring_tuple(self):
        """Assert that a tuple for the 'userstring' config option works"""
        userstring = ('Jeremy',  '<jeremy@example.com>')
        mock_config = mock.MagicMock()
        mock_config.__getitem__.return_value = userstring
        koji = buildsys.Koji(None, mock_config)
        self.assertEqual('Jeremy <jeremy@example.com>', koji.userstring)


if __name__ == '__main__':
    unittest.main()
