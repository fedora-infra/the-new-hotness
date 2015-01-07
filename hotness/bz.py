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


class Bugzilla(object):
    base_query = {
        'query_format': 'advanced',
        'emailreporter1': '1',
        'emailtype1': 'exact',
    }

    bug_status_open = ['NEW', 'ASSIGNED', 'MODIFIED', 'ON_DEV', 'ON_QA',
                       'VERIFIED', 'FAILS_QA', 'RELEASE_PENDING', 'POST']
    bug_status_closed = ['CLOSED']

    new_bug = {
        'op_sys': 'Unspecified',
        'platform': 'Unspecified',
        'bug_severity': 'unspecified',
    }

    def __init__(self, consumer, config):
        self.consumer = consumer
        self.config = config
        self.log = logging.getLogger('fedmsg')
        default = 'https://partner-bugzilla.redhat.com'
        url = self.config.get('url', default)
        username = self.config['user']
        password = self.config['password']
        self.bugzilla = bugzilla.Bugzilla(
            url=url, cookiefile=None, tokenfile=None)
        self.log.info("Logging in to %s" % url)
        self.bugzilla.login(username, password)

        self.base_query['product'] = self.config['product']
        self.base_query['email1'] = self.config['user']

        self.new_bug['product'] = self.config['product']
        if "keywords" in self.config:
            self.new_bug['keywords'] = self.config['keywords']
        self.new_bug['version'] = self.config['version']
        self.new_bug['status'] = self.config['bug_status']

        self.short_desc_template = self.config['short_desc_template']
        self.description_template = self.config['description_template']

    def handle(self, package, upstream, version, release, url):
        """ Main API entry point.  Push updates to bugzilla.

        We could be in one of three states:

        - There is a bug filed for this exact version, we do nothing.
        - There is a bug filed for an intermediate version.  Update it.
        - There is no bug and we need to file one.
        """
        kwargs = copy.copy(self.config)
        kwargs.update(dict(
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
        ))

        bug = self.exact_bug(**kwargs)
        if bug:
            self.log.info("Found exact bug %r" % bug.weburl)
            return False

        bug = self.inexact_bug(**kwargs)
        if bug:
            self.log.info("Found and updating bug %r" % bug.weburl)
            self.update_bug(bug, **kwargs)
            return bug

        bug = self.create_bug(**kwargs)
        self.log.info("Filed new bug %r" % bug.weburl)
        return bug

    def follow_up(self, text, bug):
        update = {
            'comment': {
                'body': text,
                'is_private': False,
            },
            'ids': [bug.bug_id],
        }
        self.log.debug("Following up on bug %r with %r" % (bug.bug_id, update))
        res = self.bugzilla._proxy.Bug.update(update)
        self.log.info("Followed up on bug: %s" % bug.weburl)

    def exact_bug(self, **package):
        short_desc_pattern = '%(name)s-%(upstream)s ' % package
        query = {
            'component': package['name'],
            'bug_status': self.bug_status_open + self.bug_status_closed,
            'short_desc': short_desc_pattern,
            'short_desc_type': 'substring',
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
        query = {
            'component': [package['name']],
            'bug_status': [self.config['bug_status']],
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
        bug_version = short_desc.split(" ")[0][len(package['name']) + 1:]

        self.log.info("Comparing %r, %r" % (bug_version, package['upstream']))
        if bug_version != package['upstream']:
            update = {
                'summary': self.short_desc_template % package,
                'comment': {
                    'body': self.description_template % package,
                    'is_private': False,
                },
                'ids': [bug.bug_id],
            }
            self.log.debug("Updating bug %r with %r" % (bug.bug_id, update))
            res = self.bugzilla._proxy.Bug.update(update)
            self.log.debug("Result from bug update: %r" % res)
            self.log.info("Updated bug: %s" % bug.weburl)
            return True
        else:
            self.log.warn("They are the same, which is odd. %r == %r" % (
                bug_version, package['upstream']))
            return False

    def create_bug(self, **package):
        bug_dict = {
            'component': package['name'],
            'short_desc': self.short_desc_template % package,
            'description': self.description_template % package,
        }
        bug_dict.update(self.new_bug)
        new_bug = self.bugzilla.createbug(**bug_dict)
        change_status = None
        self.log.info("Created bug: %s" % new_bug)

        if new_bug.bug_status != self.config['bug_status']:
            change_status = self.bugzilla._proxy.bugzilla.changeStatus(
                new_bug.bug_id,
                self.config['bug_status'],
                self.config['user'],
                "",
                "",
                False,
                False,
                1,
            )
            self.log.info("Changed bug status %r" % change_status)
        return new_bug
