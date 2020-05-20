"""
Unit tests for hotness.bz
"""
import unittest
import mock

from requests.exceptions import HTTPError

from hotness import bz


class TestBugzilla(unittest.TestCase):
    """
    Test class for `hotness.bz` class.
    """

    @mock.patch("hotness.consumers.BugzillaTicketFiler")
    @mock.patch("hotness.bz.bugzilla.Bugzilla.__init__", return_value=None)
    def setUp(self, mock_init, mock_consumer):
        """
        Setup test case.
        """
        mock_config = {
            "url": "https://example.com/bz",
            "user": None,
            "password": None,
            "api_key": "api_key",
            "product": "product",
            "version": "version",
            "bug_status": "status",
            "reporter": "Upstream release monitoring",
            "short_desc_template": "short_desc_template",
            "description_template": "description_template",
        }

        self.bugzilla = bz.Bugzilla(mock_consumer, mock_config)

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
            "reporter": "Upstream release monitoring",
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
            "reporter": "Upstream release monitoring",
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

    @mock.patch("hotness.bz.bugzilla.Bugzilla.query")
    def test_inexact_bug(self, mock_query):
        """
        Assert that query is called with correct parameters.
        """
        exp = {
            "query_format": "advanced",
            "emailreporter1": "1",
            "emailtype1": "exact",
            "component": "test",
            "bug_status": ["ASSIGNED", "NEW", "status"],
            "creator": "Upstream release monitoring",
            "product": "product",
            "email1": None,
        }

        self.bugzilla.inexact_bug(name="test")

        mock_query.assert_called_once_with(exp)

    @mock.patch("hotness.bz._log")
    def test_follow_up_HTTPError(self, mock_log):
        """
        Assert that HTTPError is handled gracefully when occurs in follow up.
        """
        mock_bug = mock.MagicMock()
        mock_bug.bug_id = 0
        self.bugzilla.bugzilla._proxy = mock.PropertyMock()
        self.bugzilla.bugzilla._proxy.Bug.update.side_effect = HTTPError

        self.bugzilla.follow_up("text", mock_bug)

        self.assertIn(
            "Can't follow up on bug 0, HTTP error encountered: ",
            mock_log.error.call_args_list[0][0][0],
        )
