"""
Unit tests for hotness.consumer
"""
from __future__ import unicode_literals, absolute_import

import unittest

import mock

import fedmsg.config

from hotness import consumers


class TestConsumer(unittest.TestCase):
    def setUp(self):
        self.bz = mock.patch('hotness.bz.Bugzilla')
        self.bz.__enter__()
        self.koji = mock.patch('hotness.buildsys.Koji')
        self.koji.__enter__()

        test_config = fedmsg.config.load_config()
        test_config["hotness.cache"] = {
            "backend": "dogpile.cache.null",
        }
        test_config['hotness.requests_retries'] = 0

        class MockHub(mock.MagicMock):
            config = test_config

        self.consumer = consumers.BugzillaTicketFiler(MockHub())
        import logging
        logging.basicConfig(level=logging.DEBUG)

    def tearDown(self):
        self.bz.__exit__()
        self.koji.__exit__()

    def test_is_retired_negative(self):
        """ python-sqlite2 was rolled into the stdlib.  retired. """
        response = mock.MagicMock()
        response.status_code = 200
        response.json.return_value = {'count': 0}
        self.consumer.requests_session = mock.MagicMock()
        self.consumer.requests_session.get.return_value = response

        package = 'python-sqlite2'
        expected = True
        actual = self.consumer.is_retired(package)
        self.assertEquals(expected, actual)

    def test_is_retired_positive(self):
        """ Ensure that nethack never dies. """
        response = mock.MagicMock()
        response.status_code = 200
        response.json.return_value = {'count': 1}
        self.consumer.requests_session = mock.MagicMock()
        self.consumer.requests_session.get.return_value = response

        package = 'nethack'
        expected = False
        actual = self.consumer.is_retired(package)
        self.assertEquals(expected, actual)

    def test_is_monitored_negative(self):
        response = mock.MagicMock()
        response.status_code = 200
        response.text = 'monitoring: no-monitoring'
        self.consumer.requests_session = mock.MagicMock()
        self.consumer.requests_session.get.return_value = response

        self.consumer.is_retired = mock.MagicMock()
        self.consumer.is_retired.return_value = False

        package = 'php-pecl-timecop'
        expected = False
        actual = self.consumer.is_monitored(package)
        self.assertEquals(expected, actual)

    def test_is_monitored_nobuild(self):
        response = mock.MagicMock()
        response.status_code = 200
        response.text = 'monitoring: monitoring'
        self.consumer.requests_session = mock.MagicMock()
        self.consumer.requests_session.get.return_value = response

        self.consumer.is_retired = mock.MagicMock()
        self.consumer.is_retired.return_value = False

        package = 'ocaml-cudf'
        expected = 'nobuild'
        actual = self.consumer.is_monitored(package)
        self.assertEquals(expected, actual)

    def test_is_monitored_positive(self):
        response = mock.MagicMock()
        response.status_code = 200
        response.text = 'monitoring: monitoring-with-scratch'
        self.consumer.requests_session = mock.MagicMock()
        self.consumer.requests_session.get.return_value = response

        self.consumer.is_retired = mock.MagicMock()
        self.consumer.is_retired.return_value = False

        package = 'xmlrunner'
        expected = True
        actual = self.consumer.is_monitored(package)
        self.assertEquals(expected, actual)

    def test_is_in_dist_git(self):
        response = mock.MagicMock()
        response.status_code = 200
        self.consumer.requests_session = mock.MagicMock()
        self.consumer.requests_session.head.return_value = response

        package = 'python-requests'
        expected = True
        actual = self.consumer.in_dist_git(package)
        self.assertEquals(expected, actual)

    def test_is_not_in_dist_git(self):
        response = mock.MagicMock()
        response.status_code = 404
        self.consumer.requests_session = mock.MagicMock()
        self.consumer.requests_session.head.return_value = response

        package = 'not-a-real-package'
        expected = False
        actual = self.consumer.in_dist_git(package)
        self.assertEquals(expected, actual)
