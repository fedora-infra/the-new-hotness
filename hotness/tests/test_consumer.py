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
