# -*- coding: utf-8 -*-
#
# Copyright © 2020  Red Hat, Inc.
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
This module is responsible for loading application configuration.
"""
import logging
import copy

from fedora_messaging.config import conf


_log = logging.getLogger(__name__)

# A dictionary of application defaults
DEFAULTS = dict(
    # PDC URL
    pdc_url="https://pdc.fedoraproject.org",
    # dist-git URL
    dist_git_url="https://src.fedoraproject.org",
    # mdapi URL
    mdapi_url="https://apps.fedoraproject.org/mdapi",
    # Repository id
    repoid="rawhide",
    # Distribution
    distro="Fedora",
    # The time in seconds the-new-hotness should wait for a socket to connect
    # before giving up.
    connect_timeout=15,
    # The time in seconds the-new-hotness should wait for a read from a socket
    # before giving up.
    read_timeout=15,
    # The number of times the-new-hotness should retry a network request
    # that failed for any reason (e.g. read timeout, DNS error, etc)
    requests_retries=3,
    # If true, publish fedmsg messages instead of fedora-messaging messages
    legacy_messaging=False,
    # Bugzilla configuration
    bugzilla=dict(
        enabled=True,
        url="https://partner-bugzilla.redhat.com",
        user=None,
        password=None,
        api_key="",
        product="Fedora",
        version="rawhide",
        keywords="FutureFeature, Triaged",
        bug_status="NEW",
        explanation_url="https://fedoraproject.org/wiki/upstream_release_monitoring",
        reporter="Upstream Release Monitoring",
        short_desc_template="%(name)s-%(latest_upstream)s is available",
        description_template="""
Latest upstream release: %(latest_upstream)s

Current version/release in %(repo_name)s: %(repo_version)s-%(repo_release)s

URL: %(url)s


    Please consult the package updates policy before you
issue an update to a stable branch:
    https://docs.fedoraproject.org/en-US/fesco/Updates_Policy


More information about the service that created this bug can be found at:

    %(explanation_url)s


    Please keep in mind that with any upstream change, there may also be packaging
    changes that need to be made. Specifically, please remember that it is your
    responsibility to review the new version to ensure that the licensing is still
    correct and that no non-free or legally problematic items have been added
    upstream.

Based on the information from anitya: https://release-monitoring.org/project/%(projectid)s/
""",
    ),
    # Koji configuration
    koji=dict(
        server="https://koji.fedoraproject.org/kojihub",
        weburl="https://koji.fedoraproject.org/koji",
        # Kerberos configuration to authenticate with Koji. In development
        # environments, use `kinit <fas-name>@FEDORAPROJECT.ORG` to get a
        # Kerberos ticket and use the default settings below.
        krb_principal="",
        krb_keytab="",
        krb_ccache="",
        krb_proxyuser="",
        krb_sessionopts=dict(timeout=3600, krb_rdns=False),
        git_url="https://src.fedoraproject.org/cgit/rpms/{package}.git",
        user_email=[
            "Upstream Monitor",
            "<upstream-release-monitoring@fedoraproject.org>",
        ],
        opts=dict(scratch=True),
        priority=30,
        target_tag="rawhide",
        # These are errors that we won't scream about.
        passable_errors=[
            # This is the packager's problem, not ours.
            "unclosed macro or bad line continuation"
        ],
    ),
    # Anitya configuration
    anitya=dict(url="https://release-monitoring.org"),
    # Cache configuration
    cache=dict(
        backend="dogpile.cache.dbm",
        expiration_time=300,
        arguments=dict(filename="/var/tmp/the-new-hotness-cache.dbm"),  # nosec
    ),
)


def _load_dict(config_dict: dict, defaults: dict) -> dict:
    """
    Recursively update the defaults config with config_dict values.

    Params:
        config_dict: Configuration dictionary
        defaults: Default configuration dictionary

    Returns:
        Updated configuration dictionary.
    """
    for key in config_dict:
        try:
            if isinstance(defaults[key.lower()], dict):
                defaults[key.lower()] = _load_dict(
                    config_dict[key], defaults[key.lower()]
                )
            else:
                defaults[key.lower()] = config_dict[key]
        except KeyError as e:
            _log.warning(
                "Unrecognized option in configuration file: {}. Skipping.".format(e)
            )
            continue

    return defaults


def load(config_dict: dict) -> dict:
    """
    Load application configuration from a file and merge it with default configuration.

    Params:
        config_dict: Dictionary with configuration

    Returns:
        Merged configuration dictionary.
    """
    config = copy.deepcopy(DEFAULTS)

    consumer_config = config_dict["consumer_config"]

    _log.info("Loading the-new-hotness configuration")
    config = _load_dict(consumer_config, config)

    if (
        config["bugzilla"]["user"] == DEFAULTS["bugzilla"]["user"]
        and config["bugzilla"]["password"] == DEFAULTS["bugzilla"]["password"]
        and config["bugzilla"]["api_key"] == DEFAULTS["bugzilla"]["api_key"]
    ):
        _log.warning(
            "No authentication method configured for bugzilla."
            "The-new-hotness will be unable to do any change in bugzilla."
            "Please check [consumer_config.bugzilla] section in configuration file."
        )

    return config


# Load the configuration
config = load(conf)
