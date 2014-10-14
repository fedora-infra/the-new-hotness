#!/usr/bin/env python

import os
import random
import shutil
import string
import subprocess as sp
import tempfile
import time

import koji
import sh

import logging
logging.basicConfig()
log = logging.getLogger('root')

# TODO -- make all of these things configurable from file.
server = 'https://koji.fedoraproject.org/kojihub'
cert = os.path.expanduser('~/.fedora.cert')
ca_cert = os.path.expanduser('~/.fedora-server-ca.cert')
git_url = 'http://pkgs.fedoraproject.org/cgit/{package}.git'
userstring = 'Release Monitoring <release-monitoring@fedoraproject.org>'
opts = {'scratch': True}
priority = 30
target_tag = 'rawhide'


def session_maker(cert, ca_cert):
    koji_session = koji.ClientSession(server, {'timeout': 3600})
    koji_session.ssl_login(cert, ca_cert, ca_cert)
    return koji_session


def _unique_path(prefix):
    """ Create a unique path fragment.

    This is a copy and paste from /usr/bin/koji.
    """
    suffix = ''.join([random.choice(string.ascii_letters) for i in range(8)])
    return '%s/%r.%s' % (prefix, time.time(), suffix)


def upload_srpm(session, source):
    log.info('Uploading {source} to koji'.format(source=source))
    serverdir = _unique_path('cli-build')
    session.uploadWrapper(source, serverdir)
    return "%s/%s" % (serverdir, os.path.basename(source))


def scratch_build(session, name, source):
    remote = upload_srpm(session, source)
    log.info('Intiating koji build for {name}:\n\tsource={source}\
             \n\ttarget={target}\n\topts={opts}'.format(
                 name=name, target=target_tag, source=remote, opts=opts))
    task_id = session.build(remote, target_tag, opts, priority=priority)
    log.info('Submitted koji scratch build for {name}, task_id={task_id}'\
             .format(name=name, task_id=task_id))
    return task_id


def run(cmd, cwd=None):
    log.info("Running %r in %r" % (' '.join(cmd), cwd))
    p = sp.Popen(cmd, cwd=cwd, stdout=sp.PIPE, stderr=sp.PIPE)
    out, err = p.communicate()
    if out:
        log.debug(out)
    if err:
        log.error(err)
    if p.returncode != 0:
        log.error('return code %s', p.returncode)
        raise Exception
    return out


def bump_and_build(package, upstream, version, rhbz):

    # Clone the package to a tempdir
    tmp = tempfile.mkdtemp(prefix='thn-', dir='/var/tmp')
    try:
        url = git_url.format(package=package)
        log.info("Cloning %r to %r" % (url, tmp))
        sh.git.clone(url, tmp)

        specfile = tmp + '/' + package + '.spec'

        # This requires the latest rpmdevtools from git
        # https://fedorahosted.org/rpmdevtools/
        cmd = [
            '/usr/bin/rpmdev-bumpspec',
            '--new', upstream,
            '-c', '"Latest upstream, %s for #%s"' % (upstream, rhbz),
            '-u', '"%s"' % userstring,
            specfile,
        ]
        output = run(cmd)
        output = run(['spectool', '-g', specfile], cwd=tmp)
        output = run(['fedpkg', 'srpm'], cwd=tmp)

        srpm = output.strip().split()[-1]
        log.debug("Got srpm %r" % srpm)

        session = session_maker(cert, ca_cert)
        task_id = scratch_build(session, package, srpm)
        return task_id
    finally:
        log.debug("Removing %r" % tmp)
        shutil.rmtree(tmp)
        pass


if __name__ == '__main__':
    # These values would all get provided by the the-new-hotness consumer.
    package = 'bitlyclip'
    upstream = '0.1.2'
    version = '0.1.1'
    rhbz = '138194'

    # It would then kick off a build and remember the task_id.
    # When it receives a future fedmsg message about that task_id, it could
    # report on the ticket if it succeeded or failed.
    task_id = bump_and_build(package, upstream, version, rhbz)
    print "Done - got task_id", task_id
