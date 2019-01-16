"""
Unit tests for hotness.bz
"""
import unittest
import mock

from hotness import bz


class TestBugzilla(unittest.TestCase):
    """
    Test class for `hotness.bz` class.
    """

    @mock.patch("hotness.consumers.BugzillaTicketFiler")
    @mock.patch("hotness.bz.bugzilla.Bugzilla.__init__", return_value=None)
    def test_init_with_api_key(self, __init__, mock_consumer):
        """Test the `__init__` method when the config contains an api_key."""
        mock_config = {
            "url": "https://example.com/bz",
            "user": None,
            "password": None,
            "api_key": "api_key",
            "product": "product",
            "version": "version",
            "bug_status": "status",
            "short_desc_template": "short_desc_template",
            "description_template": "description_template",
        }

        bz.Bugzilla(mock_consumer, mock_config)

        __init__.assert_called_once_with(
            url="https://example.com/bz",
            api_key="api_key",
            cookiefile=None,
            tokenfile=None,
        )

    @mock.patch("hotness.consumers.BugzillaTicketFiler")
    @mock.patch("hotness.bz.bugzilla.Bugzilla.__init__", return_value=None)
    def test__connect_with_creds_and_api_key(self, __init__, mock_consumer):
        """Test the __init__ method when the config contains credentials and an api_key."""
        mock_config = {
            "url": "https://example.com/bz",
            "user": "user",
            "password": "password",
            "api_key": "api_key",
            "product": "product",
            "version": "version",
            "bug_status": "status",
            "short_desc_template": "short_desc_template",
            "description_template": "description_template",
        }

        bz.Bugzilla(mock_consumer, mock_config)

        # Using an API key should cause the credentials to be ignored.
        __init__.assert_called_once_with(
            url="https://example.com/bz",
            api_key="api_key",
            cookiefile=None,
            tokenfile=None,
        )
