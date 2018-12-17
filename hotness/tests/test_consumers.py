"""
Unit tests for hotness.consumer
"""
from __future__ import unicode_literals, absolute_import

import unittest
from io import StringIO

import mock
import logging

from hotness import consumers
from fedora_messaging.message import Message

mock_config = {
    "consumer_config": {
        "bugzilla": {},
        "koji": {},
        "mdapi_url": "https://apps.fedoraproject.org/mdapi",
        "cache": {"backend": "dogpile.cache.null"},
        "request_retries": 0,
    }
}


class TestConsumer(unittest.TestCase):
    def setUp(self):
        self.bz = mock.patch("hotness.bz.Bugzilla")
        self.bz.__enter__()
        self.koji = mock.patch("hotness.buildsys.Koji")
        self.koji.__enter__()

        with mock.patch.dict("fedora_messaging.config.conf", mock_config):
            self.consumer = consumers.BugzillaTicketFiler()

    def tearDown(self):
        self.bz.__exit__()
        self.koji.__exit__()

    def test_is_retired_positive(self):
        """ python-sqlite2 was rolled into the stdlib.  retired. """
        response = mock.MagicMock()
        response.status_code = 200
        response.json.return_value = {"count": 0}
        self.consumer.requests_session = mock.MagicMock()
        self.consumer.requests_session.get.return_value = response

        package = "python-sqlite2"
        expected = True
        actual = self.consumer.is_retired(package)
        self.assertEquals(expected, actual)

    def test_is_retired_negative(self):
        """ Ensure that nethack never dies. """
        response = mock.MagicMock()
        response.status_code = 200
        response.json.return_value = {"count": 1}
        self.consumer.requests_session = mock.MagicMock()
        self.consumer.requests_session.get.return_value = response

        package = "nethack"
        expected = False
        actual = self.consumer.is_retired(package)
        self.assertEquals(expected, actual)

    def test_is_monitored_negative(self):
        """ Ensure a `no-monitoring` flag in git yields False internally. """
        response = mock.MagicMock()
        response.status_code = 200
        response.text = "monitoring: no-monitoring"
        self.consumer.requests_session = mock.MagicMock()
        self.consumer.requests_session.get.return_value = response

        self.consumer.is_retired = mock.MagicMock()
        self.consumer.is_retired.return_value = False

        package = "php-pecl-timecop"
        expected = False
        actual = self.consumer.is_monitored(package)
        self.assertEquals(expected, actual)

    def test_is_monitored_nobuild(self):
        """ Ensure a `monitoring` flag in git yields 'nobuild' internally. """
        response = mock.MagicMock()
        response.status_code = 200
        response.text = "monitoring: monitoring"
        self.consumer.requests_session = mock.MagicMock()
        self.consumer.requests_session.get.return_value = response

        self.consumer.is_retired = mock.MagicMock()
        self.consumer.is_retired.return_value = False

        package = "ocaml-cudf"
        expected = "nobuild"
        actual = self.consumer.is_monitored(package)
        self.assertEquals(expected, actual)

    def test_is_monitored_positive(self):
        """ Ensure a `monitoring-with-scratch` flag in git yields True
        internally.
        """
        response = mock.MagicMock()
        response.status_code = 200
        response.text = "monitoring: monitoring-with-scratch"
        self.consumer.requests_session = mock.MagicMock()
        self.consumer.requests_session.get.return_value = response

        self.consumer.is_retired = mock.MagicMock()
        self.consumer.is_retired.return_value = False

        package = "xmlrunner"
        expected = True
        actual = self.consumer.is_monitored(package)
        self.assertEquals(expected, actual)

    def test_is_in_dist_git(self):
        """ Check that HTTP/200 from dist-git returns True in our helper. """
        response = mock.MagicMock()
        response.status_code = 200
        self.consumer.requests_session = mock.MagicMock()
        self.consumer.requests_session.head.return_value = response

        package = "python-requests"
        expected = True
        actual = self.consumer.in_dist_git(package)
        self.assertEquals(expected, actual)

    def test_is_not_in_dist_git(self):
        """ Check that HTTP/404 from dist-git returns False in our helper. """
        response = mock.MagicMock()
        response.status_code = 404
        self.consumer.requests_session = mock.MagicMock()
        self.consumer.requests_session.head.return_value = response

        package = "not-a-real-package"
        expected = False
        actual = self.consumer.in_dist_git(package)
        self.assertEquals(expected, actual)

    @mock.patch("hotness.consumers.BugzillaTicketFiler.handle_anitya_version_update")
    def test_call_anitya_update(self, mock_method):
        """ Assert that `__call__` calls correct method based on message topic. """
        message = Message(topic="anitya.project.version.update")

        self.consumer.__call__(message)

        mock_method.assert_called_with(message)

    @mock.patch("hotness.consumers.BugzillaTicketFiler.handle_anitya_map_new")
    def test_call_anitya_map(self, mock_method):
        """ Assert that `__call__` calls correct method based on message topic. """
        message = Message(topic="anitya.project.map.new")

        self.consumer.__call__(message)

        mock_method.assert_called_with(message)

    @mock.patch("hotness.consumers.BugzillaTicketFiler.handle_buildsys_scratch")
    def test_call_buildsys(self, mock_method):
        """ Assert that `__call__` calls correct method based on message topic. """
        message = Message(topic="buildsys.task.state.change")

        self.consumer.__call__(message)

        mock_method.assert_called_with(message)

    def test_call_pass(self):
        """ Assert that `__call__` pass based on message topic. """
        message = Message(topic="dummy")
        logger = logging.getLogger()
        string_stream_handler = StringIO()

        stream_handler = logging.StreamHandler(string_stream_handler)
        logger.addHandler(stream_handler)
        logger.setLevel(logging.DEBUG)

        self.consumer.__call__(message)

        self.assertTrue(
            "Dropping 'dummy' {}" in string_stream_handler.getvalue().strip()
        )

        logger.removeHandler(stream_handler)
