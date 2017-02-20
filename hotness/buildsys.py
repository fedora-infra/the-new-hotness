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

from six.moves.urllib.parse import urlparse
import koji

from hotness import exceptions


_log = logging.getLogger(__name__)

_koji_session_lock = threading.RLock()


class Koji(object):
    def __init__(self, consumer, config):
        self.consumer = consumer
        self.config = config
        self.server = config['server']
        self.weburl = config['weburl']

        self.krb_principal = config['krb_principal']
        self.krb_keytab = config['krb_keytab']
        self.krb_ccache = config['krb_ccache']
        self.krb_sessionopts = config['krb_sessionopts']
        self.krb_proxyuser = config['krb_proxyuser']

        self.git_url = config['git_url']
        try:
            self.email_user = config['user_email']
        except KeyError:
            msg = 'userstring is deprecated, please use the "email_user" tuple'
            warn(msg, DeprecationWarning)
            self.email_user = [p.strip() for p in config['userstring'].rsplit('<', 1)]
            self.email_user[1] = '<' + self.email_user[1]
        self.opts = config['opts']
        self.priority = config['priority']
        self.target_tag = config['target_tag']

    def session_maker(self):
        _log.info('Creating a new Koji session to %s', self.server)
        with _koji_session_lock:
            koji_session = koji.ClientSession(self.server, self.krb_sessionopts)
            result = koji_session.krb_login(
                principal=self.krb_principal,
                keytab=self.krb_keytab,
                ccache=self.krb_ccache,
                proxyuser=self.krb_proxyuser
            )
            if not result:
                _log.error('Koji kerberos authentication failed')
            return koji_session

    def url_for(self, task_id):
        return self.weburl + '/taskinfo?taskID=%i' % task_id

    @staticmethod
    def _unique_path(prefix):
        """ Create a unique path fragment.

        This is a copy and paste from /usr/bin/koji.
        """
        suffix = ''.join([
            random.choice(string.ascii_letters) for i in range(8)
        ])
        return '%s/%r.%s' % (prefix, time.time(), suffix)

    def upload_srpm(self, session, source):
        _log.info('Uploading {source} to koji'.format(source=source))
        serverdir = self._unique_path('cli-build')
        session.uploadWrapper(source, serverdir)
        return "%s/%s" % (serverdir, os.path.basename(source))

    def scratch_build(self, session, name, source):
        remote = self.upload_srpm(session, source)
        _log.info('Intiating koji build for %r' % dict(
            name=name, target=self.target_tag, source=remote, opts=self.opts))
        task_id = session.build(
            remote, self.target_tag, self.opts, priority=self.priority)
        _log.info('Scratch build created for {name}: {url}'.format(
            name=name, url=self.url_for(task_id)))
        return task_id

    def run(self, cmd, cwd=None):
        _log.info("Running %r in %r", cmd, cwd)
        p = sp.Popen(cmd, cwd=cwd, stdout=sp.PIPE, stderr=sp.PIPE)
        out, err = p.communicate()
        if out:
            _log.debug(out)
        if err:
            _log.warning(err)
        if p.returncode != 0:
            message = 'cmd:  %s\nreturn code:  %r\nstdout:\n%s\nstderr:\n%s'
            raise Exception(message % (' '.join(cmd), p.returncode, out, err))
        return out

    def handle(self, package, upstream, version, rhbz):
        """ Main API entry point.

        Bumps the version on a package and requests a scratch build.

        Returns the task_id of the scratch build.
        """

        # Clone the package to a tempdir
        tmp = tempfile.mkdtemp(prefix='thn-', dir='/var/tmp')
        try:
            url = self.git_url.format(package=package)
            _log.info("Cloning %r to %r" % (url, tmp))
            self.run(['git', 'clone', url, tmp])

            specfile = tmp + '/' + package + '.spec'

            comment = 'Update to %s (#%d)' % (upstream, rhbz.bug_id)

            # This requires rpmdevtools-8.5 or greater
            cmd = [
                '/usr/bin/rpmdev-bumpspec',
                '--new', upstream,
                '-c', comment,
                '-u', ' '.join(self.email_user),
                specfile,
            ]
            output = self.run(cmd)

            # We compare the old sources to the new ones to make sure we download
            # new sources from bumping the specfile version. Some packages don't
            # use macros in the source URL(s) or even worse, don't set the source
            # to a URL. We want to detect these and notify the packager on the bug
            # we filed about the new version.
            old_sources = dist_git_sources(tmp)
            new_sources = spec_sources(specfile, tmp)
            compare_sources(old_sources, new_sources)

            output = self.run(
                ['rpmbuild', '-D', '_sourcedir .', '-D', '_topdir .', '-bs', specfile], cwd=tmp)

            srpm = os.path.join(tmp, output.strip().split()[-1])
            _log.debug("Got srpm %r" % srpm)

            session = self.session_maker()
            task_id = self.scratch_build(session, package, srpm)

            # Now, craft a patch to attach to the ticket
            self.run(['git', 'config', 'user.name', self.email_user[0]], cwd=tmp)
            self.run(['git', 'config', 'user.email', self.email_user[1]], cwd=tmp)
            self.run(['git', 'commit', '-a', '-m', comment], cwd=tmp)
            filename = self.run(['git', 'format-patch', 'HEAD^'], cwd=tmp)
            filename = filename.strip()

            # Copy the patch out of this doomed dir so bz can find it
            destination = os.path.join('/var/tmp', filename)
            shutil.move(os.path.join(tmp, filename), destination)
            return task_id, destination, '[patch] ' + comment
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
    for sources, checksums in ((old_sources, old_checksums), (new_sources, new_checksums)):
        for file_path in sources:
            with open(file_path, 'rb') as fd:
                h = hashlib.sha256()
                h.update(fd.read())
                checksums.add(h.hexdigest())

    if old_checksums.intersection(new_checksums):
        msg = ("One or more of the new sources for this package are identical to "
               "the old sources. It's likely this package does not use the version "
               "macro in its Source URLs. If possible, please update the specfile "
               "to include the version macro in the Source URLs")
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
    """
    files = []
    try:
        # The output format is:
        # Downloading requests-2.12.4.tar.gz
        # ####################################################################### 100.0%
        # Downloading requests-2.12.4-tests.tar.gz
        # ####################################################################### 100.0%
        output = sp.check_output(['fedpkg', 'sources'], cwd=dist_git_path)
        for line in output.splitlines():
            if line.startswith('Downloading'):
                files.append(os.path.join(dist_git_path, line.split()[-1]))
    except sp.CalledProcessError as e:
        _log.error('{cmd} failed (exit {code}): {msg}'.format(
            cmd=e.cmd, code=e.returncode, msg=e.output))
        raise exceptions.DownloadException(e.output)

    return files


def _validate_spec_urls(specfile_path):
    """
    Validate a specfile's Source URLs.

    Args:
        specfile_path (str): The path to the specfile to parse and validate.

    Raises:
        exceptions.SpecUrlException: If the specfile contains Source URLs that
            are invalid.
    """
    # The output of spectool -l <spec> is in the format:
    # Source0: some-string-we-want-to-be-a-url.tar.gz
    # Source1: some-string-we-want-to-be-a-url.tar.gz
    # ...
    # Patch0: patch-we-expect-to-be-in-dist-git.patch
    # ...
    output = sp.check_output(['spectool', '-l', specfile_path])
    for line in output.splitlines():
        if line.startswith('Source'):
            # Parse to make sure it's a url
            url = line.split(':', 1)[1].strip()
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                msg = ("One or more of the specfile's Sources is not a valid URL "
                       "so we cannot automatically build the new version for you."
                       "Please use a URL in your Source declarations if possible.")
                raise exceptions.SpecUrlException(msg)


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
        exceptions.SpecUrlException: If the specfile contains Source URLs that
            are invalid.
        exceptions.DownloadException: If a networking-related error occurs while
            downloading the specfile sources. This includes hostname resolution,
            non-200 HTTP status codes, SSL errors, etc.
    """
    _validate_spec_urls(specfile_path)
    files = []
    try:
        output = sp.check_output(['spectool', '-g', specfile_path], cwd=target_dir)
        for line in output.splitlines():
            if line.startswith('Getting'):
                files.append(os.path.realpath(os.path.join(target_dir, line.split()[-1])))
    except sp.CalledProcessError as e:
        # spectool passes the cURL exit codes back so see its manpage for the full list
        if e.returncode == 1:
            # Unknown protocol (e.g. not ftp, http, or https)
            msg = ('The specfile contains a Source URL with an unknown protocol; it should'
                   'be "https", "http", or "ftp".')
            raise exceptions.SpecUrlException(msg)
        elif e.returncode in (5, 6):
            msg = "Unable to resolve the hostname for one of the package's Source URLs"
        elif e.returncode == 7:
            # Failed to connect to the host
            msg = "Unable to connect to the host for one of the package's Source URLs"
        elif e.returncode == 22:
            # cURL uses 22 for 400+ HTTP errors; the final line contains the specific code
            msg = ("An HTTP error occurred downloading the package's new Source URLs: " +
                   e.output.splitlines()[-1])
        elif e.returncode == 60:
            msg = ("Unable to validate the TLS certificate for one of the package's"
                   "Source URLs")
        else:
            msg = (u'An unexpected error occurred while downloading the new package sources; '
                   u'please report this as a bug on the-new-hotness issue tracker.')
            _log.error('{cmd} failed (exit {code}): {msg}'.format(
                cmd=e.cmd, code=e.returncode, msg=e.output))
        raise exceptions.DownloadException(msg)

    return files
