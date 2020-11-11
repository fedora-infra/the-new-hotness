# -*- coding: utf-8 -*-
#
# This file is part of the-new-hotness project.
# Copyright (C) 2017  Red Hat, Inc.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.
"""This provides classes and functions to work with the Fedora build system"""
from __future__ import absolute_import, print_function

from warnings import warn
import hashlib
import logging
import os
import random
import shutil
import string
import subprocess as sp
import tempfile
import threading
import time
import typing
import copy

import koji

from hotness import exceptions


_log = logging.getLogger(__name__)

_koji_session_lock = threading.RLock()


def link(msg):
    """
    This function is copied from `fedmsg_meta_fedora_infrastructure`_. It is
    temporary solution to fedmsg.meta.msg2link method. It should be removed when
    koji will provide their own schema.

    Args:
        msg(`fedora_messaging.message`): Message to parse

    Returns:
        URL link to koji build

    .. _fedmsg_meta_fedora_infrastructure:
       https://github.com/fedora-infra/fedmsg_meta_fedora_infrastructure
    """

    instance = msg.body.get("instance", "primary")
    if instance == "primary":
        base = "http://koji.fedoraproject.org/koji"
    elif instance == "ppc":
        base = "http://ppc.koji.fedoraproject.org/koji"
    elif instance == "s390":
        base = "http://s390.koji.fedoraproject.org/koji"
    elif instance == "arm":
        base = "http://arm.koji.fedoraproject.org/koji"
    else:
        raise NotImplementedError("Unhandled instance")

    # One last little switch-a-roo for stg
    if ".stg." in msg.topic:
        base = "http://koji.stg.fedoraproject.org/koji"

    if "buildsys.tag" in msg.topic and "tag_id" in msg.body:
        return base + "/taginfo?tagID=%i" % (msg.body["tag_id"])
    elif "buildsys.untag" in msg.topic and "tag_id" in msg.body:
        return base + "/taginfo?tagID=%i" % (msg.body["tag_id"])
    elif "buildsys.repo.init" in msg.topic and "tag_id" in msg.body:
        return base + "/taginfo?tagID=%i" % (msg.body["tag_id"])
    elif "buildsys.repo.done" in msg.topic and "tag_id" in msg.body:
        return base + "/taginfo?tagID=%i" % (msg.body["tag_id"])
    elif "buildsys.build.state.change" in msg.topic:
        return base + "/buildinfo?buildID=%i" % (msg.body["build_id"])
    elif "buildsys.task.state.change" in msg.topic:
        return base + "/taskinfo?taskID=%i" % (msg.body["id"])
    elif "buildsys.package.list.change" in msg.topic:
        return None
    elif "buildsys.rpm.sign" in msg.topic:
        if "info" in msg.body:
            idx = msg.body["info"]["build_id"]
        else:
            idx = msg.body["rpm"]["build_id"]
        return base + "/buildinfo?buildID=%i" % idx
    else:
        return base


def subtitle(msg):
    """
    This function is copied from `fedmsg_meta_fedora_infrastructure`_. It is
    temporary solution to fedmsg.meta.msg2subtitle method. It should be removed when
    koji will provide their own schema.

    Args:
        msg(`fedora_messaging.message`): Message to parse

    Returns:
        Text related to koji build

    .. _fedmsg_meta_fedora_infrastructure:
       https://github.com/fedora-infra/fedmsg_meta_fedora_infrastructure
    """
    inst = msg.body.get("instance", "primary")
    if inst == "primary":
        inst = ""
    else:
        inst = " (%s)" % inst

    if "buildsys.tag" in msg.topic:
        tmpl = (
            "{owner}'s {name}-{version}-{release} tagged " "into {tag} by {user}{inst}"
        )
        return tmpl.format(inst=inst, **msg.body)
    elif "buildsys.untag" in msg.topic:
        tmpl = (
            "{owner}'s {name}-{version}-{release} untagged "
            "from {tag} by {user}{inst}"
        )
        return tmpl.format(inst=inst, **msg.body)
    elif "buildsys.repo.init" in msg.topic:
        tmpl = "Repo initialized:  {tag}{inst}"
        return tmpl.format(inst=inst, tag=msg.body.get("tag", "unknown"))
    elif "buildsys.repo.done" in msg.topic:
        tmpl = "Repo done:  {tag}{inst}"
        return tmpl.format(inst=inst, tag=msg.body.get("tag", "unknown"))
    elif "buildsys.package.list.change" in msg.topic:
        tmpl = "Package list change for {package}:  '{tag}'{inst}"
        return tmpl.format(inst=inst, **msg.body)
    elif "buildsys.rpm.sign" in msg.topic:
        tmpl = (
            "Koji build "
            "{name}-{version}-{release}.{arch}.rpm "
            "signed with sigkey '{sigkey}'"
        )
        if "info" in msg.body:
            kwargs = copy.copy(msg.body["info"])
        else:
            kwargs = copy.copy(msg.body["rpm"])
            kwargs["sigkey"] = msg.body["sigkey"]
        return tmpl.format(**kwargs)
    elif "buildsys.build.state.change" in msg.topic:
        templates = [
            ("{owner}'s {name}-{version}-{release} " "started building{inst}"),
            ("{owner}'s {name}-{version}-{release} " "completed{inst}"),
            ("{owner}'s {name}-{version}-{release} " "was deleted{inst}"),
            ("{owner}'s {name}-{version}-{release} " "failed to build{inst}"),
            ("{owner}'s {name}-{version}-{release} " "was cancelled{inst}"),
        ]
        tmpl = templates[msg.body["new"]]

        # If there was no owner of the build, chop off the prefix.
        if not msg.body["owner"]:
            tmpl = tmpl[len("{owner}'s ") :]

        return tmpl.format(inst=inst, **msg.body)
    elif "buildsys.task.state.change" in msg.topic:
        templates = {
            "OPEN": ("{owner}'s scratch build of {srpm}{target} started{inst}"),
            "FAILED": ("{owner}'s scratch build of {srpm}{target} failed{inst}"),
            "CLOSED": ("{owner}'s scratch build of {srpm}{target} completed{inst}"),
            "CANCELED": (
                "{owner}'s scratch build of {srpm}{target} " "was cancelled{inst}"
            ),
        }
        target = ""
        if msg.body.get("info", {}).get("request"):
            targets = set()
            for item in msg.body["info"]["request"]:
                if not isinstance(item, (dict, list)) and not item.endswith(".rpm"):
                    targets.add(item)
            if targets:
                target = " for %s" % (list_to_series(targets))
        default = "{owner}'s scratch build of {srpm}{target} changed{inst}"
        tmpl = templates.get(msg.body["new"], default)

        # If there was no owner of the build, chop off the prefix.
        if not msg.body["owner"]:
            tmpl = tmpl[len("{owner}'s ") :]

        return tmpl.format(inst=inst, target=target, **msg.body)


def list_to_series(items, N=3, oxford_comma=True):
    """Convert a list of things into a comma-separated string.
    >>> list_to_series(['a', 'b', 'c', 'd'])
    'a, b, and 2 others'
    >>> list_to_series(['a', 'b', 'c', 'd'], N=4, oxford_comma=False)
    'a, b, c and d'

    Help function for subtitle function.
    """

    if not items:
        return "(nothing)"

    # uniqify items + sort them to have predictable (==testable) ordering
    items = list(sorted(set(items)))

    if len(items) == 1:
        return items[0]

    if len(items) > N:
        items[N - 1 :] = ["%i others" % (len(items) - N + 1)]

    first = ", ".join(items[:-1])

    conjunction = " and "
    if oxford_comma and len(items) > 2:
        conjunction = "," + conjunction

    return first + conjunction + items[-1]


class Koji(object):
    def __init__(self, consumer, config):
        self.consumer = consumer
        self.server = config["server"]
        self.weburl = config["weburl"]

        self.krb_principal = config["krb_principal"]
        self.krb_keytab = config["krb_keytab"]
        self.krb_ccache = config["krb_ccache"]
        self.krb_sessionopts = config["krb_sessionopts"]
        self.krb_proxyuser = config["krb_proxyuser"]

        self.git_url = config["git_url"]
        try:
            self.email_user = config["user_email"]
        except KeyError:
            msg = 'userstring is deprecated, please use the "email_user" tuple'
            warn(msg, DeprecationWarning)
            self.email_user = [p.strip() for p in config["userstring"].rsplit("<", 1)]
            self.email_user[1] = "<" + self.email_user[1]
        self.opts = dict(config["opts"])
        self.priority = config["priority"]
        self.target_tag = config["target_tag"]

    def session_maker(self):
        _log.info("Creating a new Koji session to %s", self.server)
        with _koji_session_lock:
            koji_session = koji.ClientSession(self.server, self.krb_sessionopts)
            result = koji_session.krb_login(
                principal=self.krb_principal,
                keytab=self.krb_keytab,
                ccache=self.krb_ccache,
                proxyuser=self.krb_proxyuser,
            )
            if not result:
                _log.error("Koji kerberos authentication failed")
            return koji_session

    def url_for(self, task_id):
        return self.weburl + "/taskinfo?taskID=%i" % task_id

    @staticmethod
    def _unique_path(prefix):
        """Create a unique path fragment.

        This is a copy and paste from /usr/bin/koji.
        """
        suffix = "".join([random.choice(string.ascii_letters) for i in range(8)])
        return "%s/%r.%s" % (prefix, time.time(), suffix)

    def upload_srpm(self, session, source):
        _log.info("Uploading {source} to koji".format(source=source))
        serverdir = self._unique_path("cli-build")
        session.uploadWrapper(source, serverdir)
        return "%s/%s" % (serverdir, os.path.basename(source))

    def scratch_build(self, session, name, source):
        remote = self.upload_srpm(session, source)
        _log.info(
            "Intiating koji build for %r"
            % dict(name=name, target=self.target_tag, source=remote, opts=self.opts)
        )
        task_id = session.build(
            remote, self.target_tag, self.opts, priority=self.priority
        )
        _log.info(
            "Scratch build created for {name}: {url}".format(
                name=name, url=self.url_for(task_id)
            )
        )
        return task_id

    def handle(
        self, package: str, upstream: str, version: str, rhbz
    ) -> typing.Tuple[int, str, str]:
        """Main API entry point.

        Bumps the version of a package and requests a scratch build.

        Args:
            package (str): The package name.
            upstream (str): The new upstream version.
            version (str): Unused, exists for API compatibility at the moment.
            rhbz (bugzilla.bug.Bug): The bugzilla Bug object with a ``bug_id`` attribute.

        Returns:
            tuple: A tuple of (koji task ID, patch path, BZ attachment name).
        """

        # Clone the package to a tempdir
        # and stop bandit from complaining about a hardcoded temporary directory
        tmp = tempfile.mkdtemp(prefix="thn-", dir="/var/tmp")  # nosec
        try:
            url = self.git_url.format(package=package)
            _log.info("Cloning %r to %r" % (url, tmp))
            sp.check_output(["git", "clone", url, tmp], stderr=sp.STDOUT)

            specfile = tmp + "/" + package + ".spec"

            comment = "Update to %s (#%d)" % (upstream, rhbz.bug_id)

            # This requires rpmdevtools-8.5 or greater
            cmd = [
                "/usr/bin/rpmdev-bumpspec",
                "--new",
                upstream,
                "-c",
                comment,
                "-u",
                " ".join(self.email_user),
                specfile,
            ]
            sp.check_output(cmd, stderr=sp.STDOUT)

            # We compare the old sources to the new ones to make sure we download
            # new sources from bumping the specfile version. Some packages don't
            # use macros in the source URL(s). We want to detect these and notify
            # the packager on the bug we filed about the new version.
            old_sources = dist_git_sources(tmp)
            new_sources = spec_sources(specfile, tmp)
            try:
                compare_sources(old_sources, new_sources)
            except exceptions.HotnessException as e:
                # since identical source files between releases are very common,
                # we will just notify packager and continue.
                self.consumer.bugzilla.follow_up(str(e), rhbz)

            output = sp.check_output(
                ["rpmbuild", "-D", "_sourcedir .", "-D", "_topdir .", "-bs", specfile],
                cwd=tmp,
                stderr=sp.STDOUT,
            )

            srpm = os.path.join(tmp, output.decode("utf-8").strip().split()[-1])
            _log.debug("Got srpm %r" % srpm)

            session = self.session_maker()
            task_id = self.scratch_build(session, package, srpm)

            # Now, craft a patch to attach to the ticket
            sp.check_output(
                ["git", "config", "user.name", self.email_user[0]],
                cwd=tmp,
                stderr=sp.STDOUT,
            )
            sp.check_output(
                ["git", "config", "user.email", self.email_user[1]],
                cwd=tmp,
                stderr=sp.STDOUT,
            )
            sp.check_output(
                ["git", "commit", "-a", "-m", comment], cwd=tmp, stderr=sp.STDOUT
            )
            filename = sp.check_output(
                ["git", "format-patch", "HEAD^"], cwd=tmp, stderr=sp.STDOUT
            )
            filename = filename.decode("utf-8").strip()

            # Copy the patch out of this doomed dir so bz can find it
            destination = os.path.join("/var/tmp", filename)  # nosec
            shutil.move(os.path.join(tmp, filename), destination)
            return task_id, destination, "[patch] " + comment
        finally:
            _log.debug("Removing %r" % tmp)
            shutil.rmtree(tmp, ignore_errors=True)


def compare_sources(old_sources, new_sources):
    """
    Compare two sets of files via checksum and raise an exception if both sets
    contain the same file.

    Args:
        old_sources (list): A list of filesystem paths to source tarballs.
        new_sources (list): A list of filesystem paths to source tarballs.

    Raises:
        exceptions.SpecUrlException: If the old and new sources share a file
    """
    old_checksums = set()
    new_checksums = set()
    for sources, checksums in (
        (old_sources, old_checksums),
        (new_sources, new_checksums),
    ):
        for file_path in sources:
            with open(file_path, "rb") as fd:
                h = hashlib.sha256()
                h.update(fd.read())
                checksums.add(h.hexdigest())

    if old_checksums.intersection(new_checksums):
        msg = (
            "One or more of the new sources for this package are identical to "
            "the old sources. This is most likely caused either by identical source files "
            "between releases, for example service files, or the specfile does not use "
            "version macro in its source URLs. If this is the second case, then please "
            "update the specfile to use version macro in its source URLs.\n"
        )
        raise exceptions.SpecUrlException(msg)

    return old_checksums, new_checksums


def dist_git_sources(dist_git_path):
    """
    Retrieve sources from dist-git.

    Example:
        >>> dist_git_sources('/path/to/repo')
        ['/path/to/repo/source0.tar.gz', '/path/to/repo/source1.tar.gz']

    Args:
        dist_git_path (str): The filesystem path to the dist-git repository

    Returns:
        list: A list of absolute paths to source files downloaded

    Raises:
        subprocess.CalledProcessError: When downloading the sources fails.
    """
    files = []
    # The output format is:
    # Downloading requests-2.12.4.tar.gz
    # ####################################################################### 100.0%
    # Downloading requests-2.12.4-tests.tar.gz
    # ####################################################################### 100.0%
    output = sp.check_output(
        ["fedpkg", "--user", "hotness", "sources"], cwd=dist_git_path
    )
    for line in output.decode("utf-8").splitlines():
        if line.startswith("Downloading"):
            files.append(os.path.join(dist_git_path, line.split()[-1]))

    return files


def spec_sources(specfile_path, target_dir):
    """
    Retrieve a specfile's sources and store them in the given target directory.

    Example:
        >>> spec_sources('/path/to/specfile', '/tmp/dir')
        ['/tmp/dir/source0.tar.gz', '/tmp/dir/source1.tar.gz']

    Args:
        specfile_path (str): The filesystem path to the specfile
        target_dir (str): The directory is where the file(s) will be saved.

    Returns:
        list: A list of absolute paths to source files downloaded

    Raises:
        exceptions.DownloadException: If a networking-related error occurs while
            downloading the specfile sources. This includes hostname resolution,
            non-200 HTTP status codes, SSL errors, etc.
    """
    files = []
    try:
        output = sp.check_output(["spectool", "-g", specfile_path], cwd=target_dir)
        for line in output.decode("utf-8").splitlines():
            if line.startswith("Getting"):
                files.append(
                    os.path.realpath(os.path.join(target_dir, line.split()[-1]))
                )
    except sp.CalledProcessError as e:
        # spectool passes the cURL exit codes back so see its manpage for the full list
        if e.returncode == 1:
            # Unknown protocol (e.g. not ftp, http, or https)
            msg = (
                "The specfile contains a Source URL with an unknown protocol; it should"
                'be "https", "http", or "ftp".'
            )
            raise exceptions.SpecUrlException(msg)
        elif e.returncode in (5, 6):
            msg = "Unable to resolve the hostname for one of the package's Source URLs"
        elif e.returncode == 7:
            # Failed to connect to the host
            msg = "Unable to connect to the host for one of the package's Source URLs"
        elif e.returncode == 22:
            # cURL uses 22 for 400+ HTTP errors; the final line contains the specific code
            msg = (
                "An HTTP error occurred downloading the package's new Source URLs: "
                + e.output.decode().splitlines()[-1]
            )
        elif e.returncode == 60:
            msg = (
                "Unable to validate the TLS certificate for one of the package's"
                "Source URLs"
            )
        else:
            msg = (
                "An unexpected error occurred while downloading the new package sources; "
                "please report this as a bug on the-new-hotness issue tracker."
            )
            _log.error(
                "{cmd} failed (exit {code}): {msg}".format(
                    cmd=e.cmd, code=e.returncode, msg=e.output.decode()
                )
            )
        raise exceptions.DownloadException(msg)

    return files
