import os
import socket
import ConfigParser
from six import StringIO


hostname = socket.gethostname().split('.', 1)[0]


thn_section = 'thn'


class ThnConfigParser(ConfigParser.ConfigParser):
    def read(self, filename):
        try:
            text = open(filename).read()
        except IOError:
            pass
        else:
            section = "[%s]\n" % thn_section
            file = StringIO(section + text)
            self.readfp(file, filename)


def get_pkg_manager():
    release_file = '/etc/os-release'
    config = ThnConfigParser()
    config.read(release_file)
    name = config.get(thn_section, 'ID')
    if name == 'fedora':
        return ["/usr/bin/dnf", "repoquery"]
    else:
        return ["/usr/bin/repoquery"]

description_template = """Latest upstream release: %(latest_upstream)s

Current version/release in %(repo_name)s: %(repo_version)s-%(repo_release)s

URL: %(url)s


Please consult the package updates policy before you
issue an update to a stable branch:
https://fedoraproject.org/wiki/Updates_Policy


More information about the service that created this bug can be found at:

%(explanation_url)s


Please keep in mind that with any upstream change, there may also be packaging
changes that need to be made. Specifically, please remember that it is your
responsibility to review the new version to ensure that the licensing is still
correct and that no non-free or legally problematic items have been added
upstream.

Based on the information from anitya: https://release-monitoring.org/project/%(projectid)s/
"""

config = {
    'hotness.bugzilla.enabled': True,

    'hotness.bugzilla': {
        'user': "phracek@redhat.com",
        'password': "%Oldfield;53",
        'url': 'https://partner-bugzilla.redhat.com',
        'product': 'Fedora',
        'version': 'rawhide',
        'keywords': 'FutureFeature,Triaged',
        'bug_status': 'NEW',
        'explanation_url': 'https://fedoraproject.org/wiki/Upstream_release_monitoring',
        'short_desc_template': "%(name)s-%(latest_upstream)s is available",
        'description_template': description_template,
    },

    'hotness.koji': {
        'server': 'https://koji.fedoraproject.org/kojihub',
        'weburl': 'http://koji.fedoraproject.org/koji',
        'cert': os.path.expanduser('~/.fedora.cert'),
        'ca_cert': os.path.expanduser('~/.fedora-server-ca.cert'),
        'git_url': 'http://pkgs.fedoraproject.org/cgit/{package}.git',
        'userstring': ('Upstream Monitor',
                       '<upstream-release-monitoring@fedoraproject.org>'),
        'opts': {'scratch': True},
        'priority': 30,
        'target_tag': 'rawhide',

        # These are errors that we won't scream about.
        'passable_errors': [
            # This is the packager's problem, not ours.
            'unclosed macro or bad line continuation',
        ],
    },

    'hotness.anitya': {
        'url': 'https://release-monitoring.org',
        #'username': '....',
        #'password': '....',
    },

    'hotness.pkgdb_url': 'https://admin.fedoraproject.org/pkgdb/api',

    'hotness.yumconfig': './yum-config',

    "hotness.cache": {
        "backend": "dogpile.cache.dbm",
        "expiration_time": 300,
        "arguments": {
            "filename": "/var/tmp/the-new-hotness-cache.dbm",
        },
    },

    "hotness.pkg_manager": get_pkg_manager(),

    "endpoints": {
        # You need as many of these as you have worker threads.
        'hotness.%s' % hostname: [
            'tcp://127.0.0.1:3032',
            'tcp://127.0.0.1:3033',
            'tcp://127.0.0.1:3034',
            'tcp://127.0.0.1:3035',
        ],
    },
}
