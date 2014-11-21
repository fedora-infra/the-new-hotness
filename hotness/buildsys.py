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
        self.log.info("Running %r in %r" % (' '.join(cmd), cwd))
        p = sp.Popen(cmd, cwd=cwd, stdout=sp.PIPE, stderr=sp.PIPE)
        out, err = p.communicate()
        if out:
            self.log.debug(out)
        if err:
            self.log.warning(err)
        if p.returncode != 0:
            self.log.error('return code %s', p.returncode)
            raise Exception
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

            # This requires rpmdevtools-8.5 or greater
            cmd = [
                '/usr/bin/rpmdev-bumpspec',
                '--new', upstream,
                '-c', '"Latest upstream, %s for #%s"' % (upstream, rhbz),
                '-u', '"%s"' % self.userstring,
                specfile,
            ]
            output = self.run(cmd)

            # First, get all patches and other sources from dist-git
            output = self.run(['fedpkg', 'sources'], cwd=tmp)

            # Then go and get the *new* tarball from upstream.
            # For these to work, it requires that rpmmacros be redefined to
            # find source files in the tmp directory.  See:  http://da.gd/1MWt
            output = self.run(['spectool', '-g', specfile], cwd=tmp)
            output = self.run(['rpmbuild', '-bs', specfile], cwd=tmp)

            srpm = os.path.join(tmp, output.strip().split()[-1])
            self.log.debug("Got srpm %r" % srpm)

            session = self.session_maker()
            task_id = self.scratch_build(session, package, srpm)
            return task_id
        finally:
            self.log.debug("Removing %r" % tmp)
            shutil.rmtree(tmp)
            pass
