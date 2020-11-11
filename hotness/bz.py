# -*- coding: utf-8 -*-
# This file is part of the-new-hotness.
#
# the-new-hotness is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# the-new-hotness is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with the-new-hotness.  If not, see <http://www.gnu.org/licenses/>.
""" Code for interacting with bugzilla.

Authors:    Ralph Bean <rbean@redhat.com>

"""

import copy
import logging

import bugzilla
import os

from requests.exceptions import HTTPError


_log = logging.getLogger(__name__)


class Bugzilla(object):
    base_query = {
        "query_format": "advanced",
        "emailreporter1": "1",
        "emailtype1": "exact",
    }
    bug_status_early = ["NEW", "ASSIGNED"]
    bug_status_open = bug_status_early + [
        "MODIFIED",
        "ON_DEV",
        "ON_QA",
        "VERIFIED",
        "FAILS_QA",
        "RELEASE_PENDING",
        "POST",
    ]
    bug_status_closed = ["CLOSED"]

    new_bug = {
        "op_sys": "Unspecified",
        "platform": "Unspecified",
        "bug_severity": "unspecified",
    }

    def __init__(self, consumer, config):
        self.consumer = consumer
        self.config = config
        url = self.config["url"]
        self.username = self.config["user"]
        self.reporter = self.config["reporter"]
        password = self.config["password"]
        api_key = self.config["api_key"]
        _log.info("Using BZ URL %s" % url)

        if api_key:
            self.bugzilla = bugzilla.Bugzilla(
                url=url, api_key=api_key, cookiefile=None, tokenfile=None
            )
        elif self.username and password:
            self.bugzilla = bugzilla.Bugzilla(
                url=url,
                user=self.username,
                password=password,
                cookiefile=None,
                tokenfile=None,
            )
        else:
            self.bugzilla = bugzilla.Bugzilla(url=url, cookiefile=None, tokenfile=None)

        self.bugzilla.bug_autorefresh = True

        self.base_query["product"] = self.config["product"]
        self.base_query["email1"] = self.config["user"]

        self.new_bug["product"] = self.config["product"]
        if "keywords" in self.config:
            self.new_bug["keywords"] = self.config["keywords"]
        self.new_bug["version"] = self.config["version"]
        self.new_bug["status"] = self.config["bug_status"]

        self.short_desc_template = self.config["short_desc_template"]
        self.description_template = self.config["description_template"]

    def handle(self, projectid, package, upstream, version, release, url):
        """Main API entry point.  Push updates to bugzilla.

        We could be in one of three states:

        - There is a bug filed for this exact version, we do nothing.
        - There is a bug filed for an intermediate version.  Update it.
        - There is no bug and we need to file one.
        """
        kwargs = copy.copy(self.config)
        kwargs.update(
            dict(
                projectid=projectid,
                package=package,
                name=package,
                version=version,
                release=release,
                repo_name=self.consumer.repoid,
                repo_version=version,
                repo_release=release,
                upstream=upstream,
                latest_upstream=upstream,
                url=url,
            )
        )

        bug = self.exact_bug(**kwargs)
        if bug:
            _log.info("Found exact bug %r" % bug.weburl)
            return False

        bug = self.inexact_bug(**kwargs)
        if bug:
            _log.info("Found and updating bug %r" % bug.weburl)
            self.update_bug(bug, **kwargs)
            return bug

        bug = self.create_bug(**kwargs)
        _log.info("Filed new bug %r" % bug.weburl)
        return bug

    def follow_up(self, text, bug):
        update = {"comment": {"body": text, "is_private": False}, "ids": [bug.bug_id]}
        _log.debug("Following up on bug %r with %r" % (bug.bug_id, update))
        try:
            self.bugzilla._proxy.Bug.update(update)
        except HTTPError as e:
            _log.error(
                "Can't follow up on bug {}, HTTP error encountered: {}".format(
                    bug.bug_id, str(e)
                )
            )
        _log.info("Followed up on bug: %s" % bug.weburl)

    def _attach_file(self, filename, description, bug, **kwargs):
        if os.path.exists(filename) and os.path.getsize(filename) != 0:
            _log.debug("Attaching file to bug %r" % bug.bug_id)
            self.bugzilla.attachfile(bug.bug_id, filename, description, **kwargs)
            _log.info("Attached file to bug: %s" % bug.weburl)

    def attach_patch(self, filename, description, bug):
        self._attach_file(filename, description, bug, is_patch=True)

    def review_request_bugs(self, name):
        """ Return the review request bugs for a package. """
        short_desc_pattern = " %s " % name
        query = {
            "component": "Package Review",
            "bug_status": self.bug_status_open,
            "short_desc": short_desc_pattern,
            "short_desc_type": "substring",
            "product": self.config["product"],
            "query_format": "advanced",
        }
        bugs = self.bugzilla.query(query)
        bugs = bugs or []
        for bug in bugs:
            yield bug

    def exact_bug(self, **package):
        """ Return a particular upstream release ticket for a package. """
        short_desc_pattern = "%(name)s-%(upstream)s " % package
        query = {
            "component": package["name"],
            "bug_status": self.bug_status_open + self.bug_status_closed,
            "short_desc": short_desc_pattern,
            "short_desc_type": "substring",
        }

        query.update(self.base_query)
        bugs = self.bugzilla.query(query)
        bugs = bugs or []
        for bug in bugs:
            # The short_desc_pattern contains a space at the end, which is
            # currently not recognized by bugzilla. Therefore this test is
            # required:
            if bug.short_desc.startswith(short_desc_pattern):
                return bug

    def inexact_bug(self, **package):
        """ Return any upstream release ticket for a package. """
        # We'll match bugs in the NEW or ASSIGNED state
        # https://github.com/fedora-infra/the-new-hotness/issues/58
        possible_statuses = list(
            set(self.bug_status_early + [self.config["bug_status"]])
        )
        possible_statuses.sort()
        query = {
            "component": package["name"],
            "bug_status": possible_statuses,
            "creator": self.reporter,
        }

        query.update(self.base_query)
        bugs = self.bugzilla.query(query)
        if bugs:
            return bugs[0]
        return False

    def update_bug(self, bug, **package):
        short_desc = bug.short_desc

        # short_desc should be '<name>-<version> <some text>'
        # To extract the version get everything before the first space
        # with split and then remove the name and '-' via slicing
        bug_version = short_desc.split(" ")[0][len(package["name"]) + 1 :]

        _log.info("Comparing %r, %r" % (bug_version, package["upstream"]))
        if bug_version != package["upstream"]:
            update = {
                "summary": self.short_desc_template % package,
                "comment": {
                    "body": self.description_template % package,
                    "is_private": False,
                },
                "ids": [bug.bug_id],
            }
            _log.debug("Updating bug %r with %r" % (bug.bug_id, update))
            res = self.bugzilla._proxy.Bug.update(update)
            _log.debug("Result from bug update: %r" % res)
            _log.info("Updated bug: %s" % bug.weburl)
            return True
        else:
            _log.warn(
                "They are the same, which is odd. %r == %r"
                % (bug_version, package["upstream"])
            )
            return False

    def create_bug(self, **package):
        bug_dict = {
            "component": package["name"],
            "short_desc": self.short_desc_template % package,
            "description": self.description_template % package,
        }
        bug_dict.update(self.new_bug)
        new_bug = self.bugzilla.createbug(**bug_dict)
        change_status = None
        _log.info("Created bug: %s" % new_bug)

        if new_bug.bug_status != self.config["bug_status"]:
            change_status = self.bugzilla._proxy.bugzilla.changeStatus(
                new_bug.bug_id,
                self.config["bug_status"],
                self.config["user"],
                "",
                "",
                False,
                False,
                1,
            )
            _log.info("Changed bug status %r" % change_status)
        return new_bug
