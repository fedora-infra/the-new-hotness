#!/usr/bin/env python

import logging
import os
import random
import shutil
import string
import subprocess as sp
import tempfile
import time

import koji
import sh


class Koji(object):
    def __init__(self, consumer, config):
        self.consumer = consumer
        self.config = config
        self.log = logging.getLogger('fedmsg')
        self.server = config['server']
        self.weburl = config['weburl']
        self.cert = config['cert']
        self.ca_cert = config['ca_cert']
        self.git_url = config['git_url']
        self.userstring = config['userstring']
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
        self.log.info('Uploading {source} to koji'.format(source=source))
        serverdir = self._unique_path('cli-build')
        session.uploadWrapper(source, serverdir)
        return "%s/%s" % (serverdir, os.path.basename(source))

    def scratch_build(self, session, name, source):
        remote = self.upload_srpm(session, source)
        self.log.info('Intiating koji build for %r' % dict(
            name=name, target=self.target_tag, source=remote, opts=self.opts))
        task_id = session.build(
            remote, self.target_tag, self.opts, priority=self.priority)
        self.log.info('Done: task_id={task_id}'.format(task_id=task_id))
        return task_id

    def run(self, cmd, cwd=None):
        self.log.info("Running %r in %r", cmd, cwd)
        p = sp.Popen(cmd, cwd=cwd, stdout=sp.PIPE, stderr=sp.PIPE)
        out, err = p.communicate()
        if out:
            self.log.debug(out)
        if err:
            self.log.warning(err)
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
            self.log.info("Cloning %r to %r" % (url, tmp))
            sh.git.clone(url, tmp)

            specfile = tmp + '/' + package + '.spec'

            comment = 'Update to %s (#%d)' % (upstream, rhbz.bug_id)

            # This requires rpmdevtools-8.5 or greater
            cmd = [
                '/usr/bin/rpmdev-bumpspec',
                '--new', upstream,
                '-c', comment,
                '-u', self.userstring,
                specfile,
            ]
            output = self.run(cmd)

            # First, get all patches and other sources from dist-git
            output = self.run(['fedpkg', 'sources'], cwd=tmp)
            # fedpkg sources output looks like "Downloading SOURCE\n#######"
            oldfile = output.strip().split()[1]
            self.log.debug("fedpkg grabbed %r", oldfile)

            # Then go and get the *new* tarball from upstream.
            # For these to work, it requires that rpmmacros be redefined to
            # find source files in the tmp directory.  See:  http://da.gd/1MWt
            output = self.run(['spectool', '-g', specfile], cwd=tmp)
            newfile = output.strip().split()[-1]
            self.log.debug("spectool grabbed %r", oldfile)

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

            output = self.run(['rpmbuild', '-bs', specfile], cwd=tmp)

            srpm = os.path.join(tmp, output.strip().split()[-1])
            self.log.debug("Got srpm %r" % srpm)

            session = self.session_maker()
            task_id = self.scratch_build(session, package, srpm)

            # Now, craft a patch to attach to the ticket
            output = self.run(['git', 'commit', '-a',
                               '-m', comment,
                               '--author', self.userstring], cwd=tmp)
            filename = self.run(['git', 'format-patch', 'HEAD^'], cwd=tmp)
            filename = filename.strip()

            # Copy the patch out of this doomed dir so bz can find it
            destination = os.path.join('/var/tmp', filename)
            shutil.move(os.path.join(tmp, filename), destination)

            return task_id, destination, '[patch] ' + comment
        finally:
            self.log.debug("Removing %r" % tmp)
            shutil.rmtree(tmp)
            pass
