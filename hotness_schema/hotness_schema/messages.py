# Copyright (C) 2018  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""The schema for the-new-hotness messages."""

from fedora_messaging import message


class UpdateDrop(message.Message):
    """
    Message sent by the-new-hotness to "hotness.update.drop" topic when update
    is dropped.
    """

    topic = "org.fedoraproject.prod.hotness.update.drop"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/hotness.update.drop.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Schema for the-new-hotness",
        "type": "object",
        "required": ["reason", "trigger"],
        "properties": {
            "reason": {"type": "string"},
            "trigger": {
                "type": "object",
                "properties": {
                    "msg": {
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "object",
                                "properties": {"name": {"type": "string"}},
                                "required": ["name"],
                            }
                        },
                        "required": ["project"],
                    }
                },
                "required": ["msg"],
            },
        },
    }

    def __str__(self):
        """
        Return a complete human-readable representation of the message.

        Returns:
            (str): Summary of the message.
        """
        return self.summary

    @property
    def summary(self):
        """
        Return a short summary of the message.

        Returns:
            (str): Short description of the message.
        """
        if self.reason == "anitya":
            return (
                "the-new-hotness saw an update for '{}', ".format(self.project)
                + "but release-monitoring.org doesn't know what that project is called "
                + "in Fedora land"
            )
        elif self.reason == "rawhide":
            return (
                "the-new-hotness saw an update for '{}', ".format(self.project)
                + "but no rawhide version of the package could be found yet"
            )
        elif self.reason == "pkgdb":
            return (
                "the-new-hotness saw an update for '{}', ".format(self.project)
                + "but pkgdb says the maintainers are not interested in bugs being filed"
            )
        elif self.reason == "bugzilla":
            return (
                "the-new-hotness saw an update for '{}', ".format(self.project)
                + "but the bugzilla issue couldn't be updated"
            )
        else:
            return "the-new-hotness saw an update for '{}', ".format(
                self.project
            ) + "but it got dropped for reason: '{}'".format(self.reason)

    @property
    def project(self):
        """
        Return a name of the project.

        Returns:
             (str): Name of the project.
        """
        return self.body["trigger"]["msg"]["project"]

    @property
    def reason(self):
        """
        Return a reason for this drop.

        Returns:
            (str): Reason for drop.
        """
        return self.body["reason"]


class UpdateBugFile(message.Message):
    """
    Message sent by the-new-hotness to "hotness.update.bug.file" topic when
    bugzilla issue is filled.
    """

    topic = "org.fedoraproject.prod.hotness.update.bug.file"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/hotness.update.bug.file.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Schema for the-new-hotness",
        "type": "object",
        "required": ["bug", "trigger"],
        "properties": {
            "bug": {
                "type": "object",
                "required": ["bug_id"],
                "properties": {"bug_id": {"type": "number"}},
            },
            "trigger": {"type": "object"},
            "package": {"type": "string"},
        },
    }

    def __str__(self):
        """
        Return a complete human-readable representation of the message.

        Returns:
            (str): Summary of the message.
        """
        return self.summary

    @property
    def summary(self):
        """
        Return a short summary of the message.

        Returns:
            (str): Short description of the message.
        """
        return "the-new-hotness filed a bug on '{}'".format(self.package)

    @property
    def package(self):
        """
        Return package name.

        Returns:
            (str): Package name.
        """
        return self.body["package"]
