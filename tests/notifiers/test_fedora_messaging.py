# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Red Hat, Inc.
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
import pytest
from unittest import mock

from fedora_messaging.testing import mock_sends
from fedora_messaging.exceptions import PublishException, ConnectionException
from hotness_schema.messages import UpdateDrop

from hotness.domain import Package
from hotness.exceptions import NotifierException
from hotness.notifiers import FedoraMessaging


class TestFedoraMessagingInit:
    """
    Test class for `hotness.notifiers.FedoraMessaging.__init__` method.
    """

    def test_init(self):
        """
        Assert that FedoraMessaging notifier object is initialized correctly.
        """
        prefix = "hotness"

        notifier = FedoraMessaging(prefix)

        assert notifier.prefix == prefix


class TestFedoraMessagingNotify:
    """
    Test class for `hotness.notifiers.FedoraMessaging.notify` method.
    """

    def setup(self):
        """
        Create notifier instance for tests.
        """
        prefix = "hotness"

        self.notifier = FedoraMessaging(prefix)

    def test_notify(self):
        """
        Assert that message is sent correctly.
        """
        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")

        topic = "update.drop"
        body = {"trigger": {"msg": {}, "topic": "topic"}, "reason": "Heresy"}

        opts = {"body": body}

        with mock_sends(UpdateDrop):
            output = self.notifier.notify(package, topic, opts)

            assert list(output.keys()) == ["msg_id"]

    def test_notify_missing_opts(self):
        """
        Assert that NotifierException is raised when opts are missing.
        """
        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")

        topic = "update.drop"

        with pytest.raises(NotifierException) as exc:
            self.notifier.notify(package, topic, {})

        assert exc.value.message == (
            "Additional parameters are missing! "
            "Please provide `body` for the message."
        )

    @mock.patch("hotness.notifiers.fedora_messaging.fm_message.get_class")
    def test_notify_unknown_topic(self, mock_fm_get_class):
        """
        Assert that NotifierException is raised when topic is not found.
        """
        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")

        topic = "foobar"

        body = {"trigger": {"msg": "msg", "topic": "topic"}, "reason": "Heresy"}

        mock_fm_get_class.return_value = ""

        opts = {"body": body}

        with pytest.raises(NotifierException) as exc:
            self.notifier.notify(package, topic, opts)

        assert exc.value.message == ("Unknown topic provided 'hotness.foobar'")

    @mock.patch("hotness.notifiers.fedora_messaging.api.publish")
    def test_notify_publish_exception(self, mock_fm_publish):
        """
        Assert that NotifierException is raised when publish exception occurs.
        """
        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")

        topic = "update.drop"
        body = {"trigger": {"msg": "msg", "topic": "topic"}, "reason": "Heresy"}

        mock_fm_publish.side_effect = PublishException()

        opts = {"body": body}

        with pytest.raises(NotifierException) as exc:
            self.notifier.notify(package, topic, opts)

        assert exc.value.message.startswith("Fedora messaging broker rejected message")

    @mock.patch("hotness.notifiers.fedora_messaging.api.publish")
    def test_notify_connection_exception(self, mock_fm_publish):
        """
        Assert that NotifierException is raised when connection error occurs.
        """
        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")

        topic = "update.drop"
        body = {"trigger": {"msg": "msg", "topic": "topic"}, "reason": "Heresy"}

        mock_fm_publish.side_effect = ConnectionException()

        opts = {"body": body}

        with pytest.raises(NotifierException) as exc:
            self.notifier.notify(package, topic, opts)

        assert exc.value.message.startswith("Error sending the message")
