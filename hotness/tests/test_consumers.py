"""
Unit tests for hotness.consumer
"""
from __future__ import unicode_literals, absolute_import

import mock
from xmlrpc.client import Fault

from hotness import consumers
from fedora_messaging.message import Message
from fedora_messaging.exceptions import Nack

from hotness.tests.test_base import create_message, HotnessTestCase

mock_config = {
    "consumer_config": {
        "bugzilla": {},
        "koji": {},
        "mdapi_url": "https://apps.fedoraproject.org/mdapi",
        "cache": {"backend": "dogpile.cache.null"},
        "request_retries": 0,
        "legacy_messaging": False,
    }
}


class TestConsumer(HotnessTestCase):
    """
    Test class for `hotness.consumers`.
    """

    def setUp(self):
        super(TestConsumer, self).setUp()
        self.bz = mock.patch("hotness.bz.Bugzilla")
        self.bz.__enter__()
        self.koji = mock.patch("hotness.buildsys.Koji")
        self.koji.__enter__()

        with mock.patch.dict("fedora_messaging.config.conf", mock_config):
            self.consumer = consumers.BugzillaTicketFiler()

    def tearDown(self):
        super(TestConsumer, self).tearDown()
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

    @mock.patch("hotness.consumers._log")
    def test_call_pass(self, mock_log):
        """ Assert that `__call__` pass based on message topic. """
        message = Message(topic="dummy")

        self.consumer.__call__(message)

        self.assertIn("Dropping 'dummy' {}", mock_log.debug.call_args_list[1][0][0])

    @create_message("anitya.project.version.update", "no_mapping")
    @mock.patch("hotness.consumers._log")
    @mock.patch("hotness.consumers.BugzillaTicketFiler.publish")
    def test_handle_anitya_version_update_no_mapping(
        self, mock_publish, mock_log, message
    ):
        """
        Assert that message is correctly handled, when no mapping is set.
        """
        self.consumer.handle_anitya_version_update(message)

        self.assertIn(
            "No 'Fedora' mapping for 'pg-semver'. Dropping.",
            mock_log.info.call_args_list[1][0][0],
        )

    @create_message("anitya.project.version.update", "no_fedora_mapping")
    @mock.patch("hotness.consumers._log")
    @mock.patch("hotness.consumers.BugzillaTicketFiler.publish")
    def test_handle_anitya_version_update_no_fedora_mapping(
        self, mock_publish, mock_log, message
    ):
        """
        Assert that message is correctly handled, when Fedora mapping is not set.
        """
        self.consumer.handle_anitya_version_update(message)

        self.assertIn(
            "No 'Fedora' mapping for 'xbps'. Dropping.",
            mock_log.info.call_args_list[1][0][0],
        )

    @create_message("anitya.project.version.update", "fedora_mapping")
    @mock.patch("hotness.consumers._log")
    @mock.patch(
        "hotness.consumers.BugzillaTicketFiler.is_monitored", return_value="nobuild"
    )
    @mock.patch("hotness.helpers.cmp_upstream_repo", return_value=0)
    def test_handle_anitya_version_update_fedora_mapping_old(
        self, mock_cmp_upstream_repo, mock_monitored, mock_log, message
    ):
        """
        Assert that message is correctly handled, when Fedora mapping is set,
        but the version is older.
        """
        self.consumer.handle_anitya_version_update(message)

        self.assertIn(
            "Comparing upstream 1.0.4 against repo 1.2.3-2.fc30",
            mock_log.info.call_args_list[1][0][0],
        )

        # Only two messages in info log level
        self.assertEqual(2, len(mock_log.info.call_args_list))

    @create_message("anitya.project.version.update", "fedora_mapping")
    @mock.patch("hotness.consumers._log")
    @mock.patch("hotness.consumers.BugzillaTicketFiler.is_monitored", return_value=None)
    @mock.patch("hotness.helpers.cmp_upstream_repo", return_value=1)
    @mock.patch("hotness.consumers.BugzillaTicketFiler.publish")
    def test_handle_anitya_version_update_fedora_mapping_newer_not_monitored(
        self, mock_publish, mock_cmp_upstream_repo, mock_monitored, mock_log, message
    ):
        """
        Assert that message is correctly handled, when Fedora mapping is set,
        but the version is newer.
        """
        self.consumer.handle_anitya_version_update(message)

        self.assertIn(
            "Comparing upstream 1.0.4 against repo 1.2.3-2.fc30",
            mock_log.info.call_args_list[1][0][0],
        )

        self.assertIn(
            "repo says not to monitor 'flatpak'. Dropping.",
            mock_log.info.call_args_list[3][0][0],
        )

    @create_message("anitya.project.version.update", "fedora_mapping")
    @mock.patch("hotness.consumers.BugzillaTicketFiler.publish")
    @mock.patch("hotness.consumers.BugzillaTicketFiler.is_monitored", return_value=True)
    @mock.patch("hotness.helpers.cmp_upstream_repo", return_value=1)
    def test_handle_anitya_version_update_bugzilla_error(
        self, mock_cmp_upstream_repo, mock_monitored, mock_publish, message
    ):
        """
        Assert that Nack exception is thrown when bugzilla error happens.
        """
        with mock.patch.object(self.consumer, "bugzilla") as mock_bugzilla:
            mock_bugzilla.handle = mock.Mock(side_effect=Fault(51, "Error"))
            self.assertRaises(Nack, self.consumer.handle_anitya_version_update, message)

    @create_message("anitya.project.map.new", "version")
    @mock.patch("hotness.consumers._log")
    @mock.patch("hotness.consumers.BugzillaTicketFiler._handle_anitya_update")
    def test_handle_anitya_map_new_version(self, mock_handle_update, mock_log, message):
        """
        Assert that message is correctly handled, when new mapping is added.
        """
        self.consumer.handle_anitya_map_new(message)

        self.assertIn(
            "Newly mapped 'pg-semver' to 'pg-semver' bears version '0.17.0'",
            mock_log.info.call_args_list[0][0][0],
        )

        mock_handle_update.assert_called_with("0.17.0", "pg-semver", message)

    @create_message("anitya.project.map.new", "no_version")
    @mock.patch("hotness.consumers._log")
    @mock.patch("hotness.anitya.Anitya")
    def test_handle_anitya_map_new_no_version(self, mock_anitya, mock_log, message):
        """
        Assert that message is correctly handled, when new mapping is added without
        version.
        """
        self.consumer.handle_anitya_map_new(message)

        self.assertIn(
            "Newly mapped 'gdtools' to 'R-gdtools' bears version None",
            mock_log.info.call_args_list[0][0][0],
        )

        self.assertIn(
            "Forcing an anitya upstream check.", mock_log.info.call_args_list[1][0][0]
        )

        mock_anitya.assert_called_once_with("https://release-monitoring.org")

    @create_message("anitya.project.map.new", "no_fedora_mapping")
    @mock.patch("hotness.consumers._log")
    def test_handle_anitya_map_new_no_fedora_mapping(self, mock_log, message):
        """
        Assert that message is correctly handled, when new mapping is added for other
        distribution than Fedora.
        """
        self.consumer.handle_anitya_map_new(message)

        self.assertIn(
            "New mapping on Arch, not for Fedora. Dropping",
            mock_log.info.call_args_list[0][0][0],
        )

    @create_message("buildsys.task.state.change", "build")
    @mock.patch("hotness.consumers._log")
    def test_handle_buildsys_scratch_dict_empty(self, mock_log, message):
        """
        Assert that message is correctly handled, when buildsys is received
        and scratch_build dictionary is empty.
        """
        self.consumer.handle_buildsys_scratch(message)

        self.assertIn(
            "Ignoring [90100954] as it's not one of our 0 outstanding builds",
            mock_log.debug.call_args_list[0][0][0],
        )

    @create_message("buildsys.task.state.change", "build")
    @mock.patch("hotness.consumers._log")
    def test_handle_buildsys_scratch_build_not_done(self, mock_log, message):
        """
        Assert that message is correctly handled, when buildsys is received
        and state is not in states that are considered as done.
        """
        mock_dict = {90100954: {"bz": "Dummy"}}

        with mock.patch.dict(
            self.consumer.scratch_builds, mock_dict
        ), mock.patch.object(self.consumer, "bugzilla") as mock_bugzilla:
            self.consumer.handle_buildsys_scratch(message)

        self.assertIn(
            "Handling koji scratch msg '{}'".format(message.id),
            mock_log.info.call_args_list[0][0][0],
        )

        mock_bugzilla.follow_up.assert_not_called()

    @create_message("buildsys.task.state.change", "build_completed")
    @mock.patch("hotness.consumers._log")
    @mock.patch("hotness.consumers.BugzillaTicketFiler.in_dist_git", return_value=False)
    def test_handle_buildsys_scratch_build_completed(
        self, mock_in_dist_git, mock_log, message
    ):
        """
        Assert that message is correctly handled, when buildsys is received
        and state is completed.
        """
        mock_dict = {90100954: {"bz": "Dummy"}}

        with mock.patch.dict(
            self.consumer.scratch_builds, mock_dict
        ), mock.patch.object(self.consumer, "bugzilla") as mock_bugzilla:
            mock_bugzilla.review_request_bugs = mock.Mock(return_value=[])
            self.consumer.handle_buildsys_scratch(message)

        self.assertIn(
            "Handling koji scratch msg '{}'".format(message.id),
            mock_log.info.call_args_list[0][0][0],
        )

        mock_bugzilla.follow_up.assert_called_once_with(
            "koschei's scratch build of globus-callout-4.0-1.fc29.src.rpm "
            "for f29 completed http://koji.fedoraproject.org/koji/taskinfo?taskID=90100954",
            "Dummy",
        )

        mock_bugzilla.review_request_bugs.assert_called_once_with("globus-callout")

        mock_in_dist_git.called_once_with("globus-callout-4.0-1.fc29.src.rpm")
