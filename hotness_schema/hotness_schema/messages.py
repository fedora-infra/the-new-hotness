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
                "properties": {"msg": {"type": "object"}, "topic": {"type": "string"}},
                "required": ["msg", "topic"],
            },
        },
    }

    @property
    def summary(self):
        """
        Return a short summary of the message.

        Returns:
            (str): Short description of the message.
        """
        if self.reason == "anitya":
            return (
                "the-new-hotness saw an update for '{}', ".format(
                    ", ".join(self.packages)
                )
                + "but release-monitoring.org doesn't know what that project is called "
                + "in Fedora land"
            )
        elif self.reason == "rawhide":
            return (
                "the-new-hotness saw an update for '{}', ".format(
                    ", ".join(self.packages)
                )
                + "but no rawhide version of the package could be found yet"
            )
        elif self.reason == "pkgdb":
            return (
                "the-new-hotness saw an update for '{}', ".format(
                    ", ".join(self.packages)
                )
                + "but pkgdb says the maintainers are not interested in bugs being filed"
            )
        elif self.reason == "bugzilla":
            return (
                "the-new-hotness saw an update for '{}', ".format(
                    ", ".join(self.packages)
                )
                + "but the bugzilla issue couldn't be updated"
            )
        else:
            return "the-new-hotness saw an update for '{}', ".format(
                ", ".join(self.packages)
            ) + "but it got dropped for reason: '{}'".format(self.reason)

    @property
    def packages(self):
        """
        List of packages affected by the action that generated this message.
        In this case we only return list with one item.

        Returns:
            list(str): A list of affected package names or empty list.
        """
        if self.reason == "anitya":
            # Return name of the project instead of list of Fedora packages
            # if we don't know how the package is called in Fedora land
            original = self.body["trigger"]["msg"]
            project_name = ""
            if "project" in original:
                project_name = original["project"]["name"]

            if "message" in original and "project" in original["message"]:
                project_name = original["message"]["project"]["name"]

            return [project_name]

        if "package_listing" in self.body["trigger"]["msg"]:
            original = self.body["trigger"]["msg"]
            return [original["package_listing"]["package"]["name"]]

        if "buildsys.build" in self.body["trigger"]["topic"]:
            return [self.body["trigger"]["msg"]["name"]]

        if "package" in self.body["trigger"]["msg"]:
            original = self.body["trigger"]["msg"]
            return [original["package"]["name"]]

        return []

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
            "trigger": {
                "type": "object",
                "properties": {"msg": {"type": "object"}, "topic": {"type": "string"}},
                "required": ["msg", "topic"],
            },
            "package": {"type": "string"},
        },
    }

    @property
    def summary(self):
        """
        Return a short summary of the message.

        Returns:
            (str): Short description of the message.
        """
        return "the-new-hotness filed a bug on '{}'".format(", ".join(self.packages))

    @property
    def packages(self):
        """
        List of packages affected by the action that generated this message.

        Returns:
            list(str): A list of affected package names.
        """
        original = self.body["trigger"]["msg"]
        if self.body["trigger"]["topic"].endswith(".project.map.new"):
            packages = [original["message"]["new"]]
        else:
            packages = [
                pkg["package_name"]
                for pkg in original["message"]["packages"]
                if pkg["distro"] == "Fedora"
            ]

        return packages
