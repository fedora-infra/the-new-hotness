# -*- coding: utf-8 -*-

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
import logging
import os
import random
import shutil
import string
import subprocess as sp
import tempfile
import time

import koji

from rebasehelper.application import Application
from rebasehelper.cli import CLI


_log = logging.getLogger(__name__)


class Koji(object):
    def __init__(self, consumer, config):
        self.consumer = consumer
        self.config = config
        self.server = config['server']
        self.weburl = config['weburl']
        self.cert = config['cert']
        self.ca_cert = config['ca_cert']
        self.git_url = config['git_url']
        try:
            self.email_user = config['user_email']
        except KeyError:
            msg = 'userstring is deprecated, please use the "email_user" tuple'
            warn(msg, DeprecationWarning)
            self.email_user = config['userstring'].rsplit('<', 1)
            self.email_user[1] = '<' + self.email_user[1]
        self.opts = config['opts']
        self.priority = config['priority']
        self.target_tag = config['target_tag']

    def session_maker(self):
        koji_session = koji.ClientSession(self.server, {'timeout': 3600})
        koji_session.ssl_login(self.cert, self.ca_cert, self.ca_cert)
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
        _log.info('Done: task_id={task_id}'.format(task_id=task_id))
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

            # First, get all patches and other sources from dist-git
            output = self.run(['fedpkg', 'sources'], cwd=tmp)
            # fedpkg sources output looks like "Downloading SOURCE\n#######"
            oldfile = output.strip().split()[1]
            _log.debug("fedpkg grabbed %r", oldfile)

            # Then go and get the *new* tarball from upstream.
            # For these to work, it requires that rpmmacros be redefined to
            # find source files in the tmp directory.  See:  http://da.gd/1MWt
            output = self.run(['spectool', '-g', specfile], cwd=tmp)
            newfile = output.strip().split()[-1]
            _log.debug("spectool grabbed %r", oldfile)

            # Now, handle an edge case before we proceed with building.
            # Sometimes, the specfiles have versions hardcoded in them such
            # that bumping the Version field and running spectool actually
            # pulls down another copy of the old tarball, not the new one.
            # https://github.com/fedora-infra/the-new-hotness/issues/29
            # So, check that the sha sums of the tarballs are different.
            oldsum = self.run(['sha256sum', os.path.join(tmp, oldfile)])
            newsum = self.run(['sha256sum', os.path.join(tmp, newfile)])
            oldsum, newsum = oldsum.split()[0], newsum.split()[0]
            if oldsum == newsum:
                raise ValueError(
                    "spectool was unable to grab new sources\n\n"
                    "old source: {oldfile}\nold sha256: {oldsum}\n\n"
                    "new source: {newfile}\nnew sha256: {newsum}\n".format(
                        oldfile=oldfile, oldsum=oldsum,
                        newfile=newfile, newsum=newsum))

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
            shutil.rmtree(tmp)
            pass

    def _run_rh(self, package, args, tmp_dir):
        """
        Execute rebase-helper with given arguments.

        Returns exit code and data from rebase-helper.
        """
        if package:
            url = self.git_url.format(package=package)
            _log.info("Cloning %r to %r" % (url, tmp_dir))
            sh.git.clone(url, tmp_dir)

        cwd = os.getcwd()
        os.chdir(tmp_dir)
        try:
            cli = CLI(args)
            rh_app = Application(cli, *Application.setup(cli))
            rh_app.set_upstream_monitoring()
            _log.info("Running rebase-helper with arguments '%s'" % ' '.join(args))
            result_rh = rh_app.run()
            rh_stuff = rh_app.get_rebasehelper_data()
        finally:
            os.chdir(cwd)

        result_rh = int(result_rh) if result_rh else 0
        _log.info("rebase-helper finished with exit code %d" % result_rh)
        _log.debug(rh_stuff)
        return result_rh, rh_stuff

    def rebase(self, package, upstream, tmp_dir):
        """
        Rebase the package using rebase-helper.

        Returns exit code and data from rebase-helper.
        """
        args = [
            '--non-interactive',
            '--builds-nowait',
            '--buildtool', 'koji',
            upstream
        ]
        return self._run_rh(package, args, tmp_dir)

    def check_rebase(self, upstream, old_task_id, new_task_id, tmp_dir):
        """
        Check and compare rawhide and rebased version builds
        using rebase-helper.

        Returns exit code and data from rebase-helper.
        """
        args = [
            '--non-interactive',
            '--builds-nowait',
            '--buildtool', 'koji',
            '--build-tasks', '%s,%s' % (old_task_id, new_task_id),
            upstream
        ]
        return self._run_rh(None, args, tmp_dir)
