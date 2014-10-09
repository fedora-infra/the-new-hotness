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
""" Fedmsg consumers that listen to `anitya <http://release-monitoring.org>`_.

Authors:    Ralph Bean <rbean@redhat.com>

"""

import copy
import socket

import bugzilla

import fedmsg
import fedmsg.consumers

import hotness.cache
import hotness.helpers
import hotness.repository


class BugzillaTicketFiler(fedmsg.consumers.FedmsgConsumer):

    # This is the real production topic
    # topic = 'org.release-monitoring.prod.anitya.project.version.update'

    # For development, I am using this so I can test with this command:
    # $ fedmsg-dg-replay --msg-id 2014-77ff95ff-3373-4926-bf23-bf0754b0925c
    topic = 'org.fedoraproject.dev.anitya.project.version.update'

    config_key = 'hotness.bugzilla.enabled'

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

    def __init__(self, hub):
        super(BugzillaTicketFiler, self).__init__(hub)

        if not self._initialized:
            return

        # This is just convenient.
        self.config = self.hub.config

        # First, initialize fedmsg and bugzilla in this thread's context.
        hostname = socket.gethostname().split('.', 1)[0]
        fedmsg.init(name='hotness.%s' % hostname)

        self.bz_config = self.config['hotness.bugzilla']
        default = 'https://partner-bugzilla.redhat.com'
        url = self.bz_config.get('url', default)
        username = self.bz_config['user']
        password = self.bz_config['password']
        self.bugzilla = bugzilla.Bugzilla(url=url)
        self.log.info("Logging in to %s" % url)
        self.bugzilla.login(username, password)

        self.base_query['product'] = self.bz_config['product']
        self.base_query['email1'] = self.bz_config['user']

        self.new_bug['product'] = self.bz_config['product']
        if "keywords" in self.bz_config:
            self.new_bug['keywords'] = self.bz_config['keywords']
        self.new_bug['version'] = self.bz_config['version']
        self.new_bug['status'] = self.bz_config['bug_status']

        self.short_desc_template = self.bz_config['short_desc_template']
        self.description_template = self.bz_config['description_template']

        # Also, set up our global cache object.
        self.log.info("Configuring cache.")
        with hotness.cache.cache_lock:
            if not hasattr(hotness.cache.cache, 'backend'):
                hotness.cache.cache.configure(**self.config['hotness.cache'])

        self.repoid = self.config.get('hotness.repoid')
        self.log.info("Using hotness.repoid=%r" % self.repoid)
        self.distro = self.config.get('hotness.distro', 'Fedora')
        self.log.info("Using hotness.distro=%r" % self.distro)

        self.log.info("That new hotness ticket filer is all initialized")

    def publish(self, topic, msg):
        self.log.info("publishing topic %r" % topic)
        fedmsg.publish(modname='hotness', topic=topic, msg=msg)

    def consume(self, msg):
        topic, msg = msg['topic'], msg['body']
        self.log.info("Received %r" % msg.get('msg_id', None))

        # What is this thing called in our distro?
        mappings = dict([
            (p['distro'], p['package_name']) for p in msg['msg']['packages']
        ])
        if self.distro not in mappings:
            self.log.info("No Fedora for %r" % msg['msg']['project']['name'])
            return

        package = mappings['Fedora']
        url = msg['msg']['project']['homepage']

        # Is it new to us?
        version, release = hotness.repository.get_version(package, self.repoid)
        upstream = msg['msg']['upstream_version']
        self.log.info("Comparing upstream %s against repo %s-%s" % (
            upstream, version, release))
        diff = hotness.helpers.cmp_upstream_repo(upstream, (version, release))

        if diff == 1:
            self.log.info("OK, %s is newer than %s-%s" % (
                upstream, version, release))
            self.handle_bugzilla(package, upstream, version, release, url, msg)
        else:
            self.publish("noop", msg=dict(
                anitya=msg, current_version=current_version
            ))

    def handle_bugzilla(self, package, upstream, version, release, url, msg):
        """ Push updates to bugzilla.

        We could be in one of three states:

        - There is a bug filed for this exact version, we do nothing.
        - There is a bug filed for an intermediate version.  Update it.
        - There is no bug and we need to file one.
        """
        kwargs = copy.copy(self.bz_config)
        kwargs.update(dict(
            package=package,
            name=package,
            version=version,
            release=release,

            repo_name=self.repoid,
            repo_version=version,
            repo_release=release,

            upstream=upstream,
            latest_upstream=upstream,

            url=url,
        ))

        bug = self.exact_bug(**kwargs)
        if bug:
            self.log.info("Found exact bug %r" % bug.weburl)
            return

        bug = self.inexact_bug(**kwargs)
        if bug:
            self.log.info("Found and updating bug %r" % bug.weburl)
            self.update_bug(bug, **kwargs)
            return

        bug, change_status = self.create_bug(**kwargs)
        self.log.info("Filed new bug %r" % bug.weburl)

    # @hotness.cache.cache.cache_on_arguments()
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

    # @hotness.cache.cache.cache_on_arguments()
    def inexact_bug(self, **package):
        # TODO - write on the whiteboard to try and figure this out...
        query = {
            'component': [package['name']],
            'bug_status': [self.bz_config['bug_status']],
        }

        query.update(self.base_query)
        bugs = self.bugzilla.query(query)
        if bugs:
            return bugs[0]

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
        else:
            self.log.warn("Nope %r == %r" % (bug_version, package['upstream']))

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

        if new_bug.bug_status != self.bz_config['bug_status']:
            change_status = self.bugzilla._proxy.bugzilla.changeStatus(
                new_bug.bug_id,
                self.bz_config['bug_status'],
                self.bz_config['user'],
                "",
                "",
                False,
                False,
                1,
            )
            self.log.info("Changed bug status %r" % change_status)
        return (new_bug, change_status)
