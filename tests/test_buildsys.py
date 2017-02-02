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

from hotness import buildsys


class KojiTests(unittest.TestCase):

    def setUp(self):
        self.config = {
            'server': None,
            'weburl': None,
            'krb_principal': None,
            'krb_keytab': None,
            'krb_ccache': None,
            'krb_sessionopts': None,
            'krb_proxyuser': None,
            'git_url': None,
            'user_email': ['Jeremy', '<jeremy@example.com>'],
            'opts': None,
            'priority': None,
            'target_tag': None,
        }

    def test_initialization_userstring_str(self):
        """Assert that a string for the 'userstring' config is parsed to user_email"""
        self.config['userstring'] = 'Jeremy <jeremy@example.com>'
        del self.config['user_email']
        koji = buildsys.Koji(None, self.config)
        self.assertEqual(['Jeremy', '<jeremy@example.com>'], koji.email_user)

    def test_initialization_user_email_tuple(self):
        """Assert that a tuple for the 'user_email' config option works"""
        koji = buildsys.Koji(None, self.config)
        self.assertEqual(['Jeremy', '<jeremy@example.com>'], koji.email_user)


if __name__ == '__main__':
    unittest.main()
