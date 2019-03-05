# -*- coding: utf-8 -*-
#
# Copyright © 2014-2019  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
"""
Base class for Anitya tests.
"""
import unittest
import os
import json
import functools

import vcr
from fedora_messaging.message import Message

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures/"))


def create_message(topic, name):
    """
    Decorator for creating message from fixture. It takes topic and name of the file
    and returns message as argument of the decorated function.

    Args:
        topic (str): Message topic
        name (str): Name of the file to load

    Returns:
        Decorated function with new parameter containing message
    """

    def _create_message(func):
        """
        Inner decorator for function. It takes topic and name from outer decorator and
        creates message from json file "FIX_TEXTURES/topic/name.json".

        Args:
            func: Function to decorate

        Returns:
            Decorated function with new parameter containing message
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            fixture = os.path.join(FIXTURES_DIR, topic, name + ".json")
            with open(fixture, "r") as fp:
                body = json.load(fp)

            message = Message(topic=topic, body=body)
            kwargs["message"] = message

            return func(*args, **kwargs)

        return wrapper

    return _create_message


class HotnessTestCase(unittest.TestCase):
    """This is the base test case class for the-new-hotness tests."""

    def setUp(self):
        """Set a basic test environment.

        This simply starts recording a VCR on start-up and stops on tearDown.
        """
        cwd = os.path.dirname(os.path.realpath(__file__))
        my_vcr = vcr.VCR(
            cassette_library_dir=os.path.join(cwd, "request-data/"), record_mode="once"
        )
        self.vcr = my_vcr.use_cassette(self.id())
        self.vcr.__enter__()
        self.addCleanup(self.vcr.__exit__, None, None, None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
