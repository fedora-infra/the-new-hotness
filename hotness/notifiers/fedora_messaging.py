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
import logging

from fedora_messaging import api, message as fm_message
from fedora_messaging.exceptions import PublishException, ConnectionException

from hotness.exceptions import NotifierException
from hotness.domain.package import Package
from .notifier import Notifier


_logger = logging.getLogger(__name__)


class FedoraMessaging(Notifier):
    """
    This class is a wrapper for https://github.com/fedora-infra/fedora-messaging publisher.
    It publishes a message to fedora messaging broker using hotness_schema messages.

    Attributes:
        prefix (str): String used as prefix for the topic
    """

    def __init__(self, prefix: str) -> None:
        """
        Class constructor.

        It initializes class attributes.

        Params:
            prefix: Prefix to use for topic
        """
        super(FedoraMessaging, self).__init__()
        self.prefix = prefix

    def notify(self, package: Package, message: str, opts: dict) -> dict:
        """
        This method is inherited from `hotness.notifiers.Notifier`.

        It publishes messages to Fedora messaging broker.

        Params:
            package: Package to create notification for
            message: Topic for the message
            opts: Additional options for fedora message. Example:
                {
                    "body": {} # Body of the message we want to sent. Look at the
                               # hotness_schema for more info
                }

        Returns:
            Dictionary containing message id
            Example:
            {
                "msg_id": "ae68f"
            }

        Raises:
            NotifierException: When the required `opts` parameters are missing or
                               error happens during publishing.
        """
        topic = self.prefix + "." + message
        body = opts.get("body", {})
        output = {}

        if not body:
            raise NotifierException(
                "Additional parameters are missing! Please provide `body` for the message."
            )

        message_class = fm_message.get_class(topic)
        if not message_class:
            raise NotifierException("Unknown topic provided '{}'".format(topic))

        _logger.info("publishing topic %r" % topic)
        try:
            msg = message_class(topic=topic, body=body)
            api.publish(msg)
        except PublishException as e:
            raise NotifierException(
                "Fedora messaging broker rejected message {}:{}".format(msg.id, e)
            )
        except ConnectionException as e:
            raise NotifierException("Error sending the message {}:{}".format(msg.id, e))
        finally:
            output["msg_id"] = msg.id

        return output
