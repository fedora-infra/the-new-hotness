"""
Unit tests for hotness.helpers
"""
from __future__ import unicode_literals, absolute_import

import unittest
import mock

import fedmsg.config

from hotness import consumers


class TestConsumer(unittest.TestCase):
    def setUp(self):
        test_config = fedmsg.config.load_config()
        test_config["hotness.cache"] = {
            "backend": "dogpile.cache.memory",
            "expiration_time": 0,
        }

        class MockHub(mock.MagicMock):
            config = test_config

        import logging
        logging.basicConfig(level=logging.DEBUG)

        self.consumer = consumers.BugzillaTicketFiler(MockHub())

    def test_is_retired_negative(self):
        """ python-sqlite2 was rolled into the stdlib.  retired. """
        package = 'python-sqlite2'
        expected = True
        actual = self.consumer.is_retired(package)
        self.assertEquals(expected, actual)

    def test_is_retired_positive(self):
        """ Ensure that nethack never dies. """
        package = 'nethack'
        expected = False
        actual = self.consumer.is_retired(package)
        self.assertEquals(expected, actual)

    def test_is_monitored_negative(self):
        package = 'php-pecl-timecop'
        expected = False
        actual = self.consumer.is_monitored(package)
        self.assertEquals(expected, actual)

    def test_is_monitored_nobuild(self):
        package = 'ocaml-cudf'
        expected = 'nobuild'
        actual = self.consumer.is_monitored(package)
        self.assertEquals(expected, actual)

    def test_is_monitored_positive(self):
        package = 'xmlrunner'
        expected = True
        actual = self.consumer.is_monitored(package)
        self.assertEquals(expected, actual)

    def test_is_in_pkgdb(self):
        package = 'python-requests'
        expected = True
        actual = self.consumer.in_pkgdb(package)
        self.assertEquals(expected, actual)

    def test_is_not_in_pkgdb(self):
        package = 'not-a-real-package'
        expected = False
        actual = self.consumer.in_pkgdb(package)
        self.assertEquals(expected, actual)
