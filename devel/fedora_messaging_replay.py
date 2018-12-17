#!/usr/bin/python3
"""
This script can republish any message in datagrepper specified by message id.

See: https://apps.fedoraproject.org/datagrepper
"""

import requests
import argparse
from fedora_messaging import api, message as fm_message

URL_TEMPLATE = "https://apps.fedoraproject.org/datagrepper/id?id={}&is_raw=true"


def parse_arguments():
    """
    Parse arguments and returns parsed msg_id.

    Returns:
        (str) Message id
    """

    parser = argparse.ArgumentParser(description="Replays messages from datagrepper")
    parser.add_argument("msg_id", help="Message of the id to be replayed")

    args = parser.parse_args()

    if not args.msg_id:
        parser.print_help()
        exit(1)

    return args.msg_id


def get_message(msg_id):
    """
    Get JSON representation of message from datagrepper.

    Params:
        msg_id (str): Message id of the message that should be retrieved

    Returns:
        (dict) JSON representation of the message
    """
    url = URL_TEMPLATE.format(msg_id)

    response = requests.get(url, timeout=30)
    message = response.json()

    return message


def publish(message):
    """
    Publish message through fedora-messaging.

    Params:
        message (dict): JSON representation of the message
    """
    msg = fm_message.Message(topic=message["topic"], body=message["msg"])

    api.publish(msg)


if __name__ == "__main__":
    msg_id = parse_arguments()
    message = get_message(msg_id)
    publish(message)
