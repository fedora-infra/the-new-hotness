# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Red Hat, Inc.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
import hashlib
import logging
import os
import random
import string
import subprocess as sp
from tempfile import TemporaryDirectory
import threading
import time
import typing

import koji

from . import Builder
from hotness.domain.package import Package
from hotness.exceptions import DownloadException, BuilderException


_logger = logging.getLogger(__name__)

# Thread lock for koji session
_koji_session_lock = threading.RLock()


class Koji(Builder):
    """
    Wrapper class around koji (https://koji.fedoraproject.org/koji/) builder.
    It starts the scratch builds for the-new-hotness in Fedora.

    Attributes:
       server_url: URL of the Koji server
       web_url: Web interface URL for Koji
       krb_principal: Principal for Kerberos domain
       krb_keytab: Kerberos keytab
       krb_ccache: Kerberos CCache
       krb_proxyuser: Kerberos proxy user
       krb_sessionopts: Additional Kerberos session options
       git_url: URL of dist git where to look for the package repository
       user_email: Tuple containing user name and e-mail
       opts: Any additional opts for koji
       priority: Priority of builds submitted by this wrapper
       target_tag: Tag under which builds will be submitted
    """

    def __init__(
        self,
        server_url: str,
        web_url: str,
        kerberos_args: dict,
        git_url: str,
        user_email: tuple,
        opts: dict,
        priority: int,
        target_tag: str,
    ) -> None:
        """
        Class constructor.
        """
        super(Koji, self).__init__()
        self.server_url = server_url
        self.web_url = web_url
        self.krb_principal = kerberos_args["krb_principal"]
        self.krb_keytab = kerberos_args["krb_keytab"]
        self.krb_ccache = kerberos_args["krb_ccache"]
        self.krb_proxyuser = kerberos_args["krb_proxyuser"]
        self.krb_sessionopts = kerberos_args["krb_sessionopts"]
        self.git_url = git_url
        self.user_email = user_email
        self.opts = opts
        self.priority = priority
        self.target_tag = target_tag

    def build(self, package: Package, opts: dict) -> dict:
        """
        Clones the package dist git repository, bumps version, downloads sources,
        starts scratch build and prepares patch.

        Params:
            package: Package to build
            opts: Contains bugzilla issue to reference in build description and commit message
            Example:
            {
                "bz_id": 100
            }

        Returns:
            Dictionary containing output from builder.
            Example:
            {
                "build_id": 1000, # Build id of the started build
                "patch": "", # String containing the patch created by version bump
                "patch_filename": "", # Name of the patch file
                "message": "", # Any info we want to share in notifier later
            }
        """
        output = {"build_id": 0, "patch": "", "patch_filename": "", "message": ""}
        # Get bugzilla id from opts
        bz_id = opts["bz_id"]
        # Write file to temporary directory
        # and stop bandit from complaining about a hardcoded temporary directory
        # because it's needed for OpenShift
        with TemporaryDirectory(prefix="thn-", dir="/var/tmp") as tmp:  # nosec
            dist_git_url = self.git_url.format(package=package.name)
            _logger.info("Cloning %r to %r" % (dist_git_url, tmp))
            try:
                sp.check_output(["git", "clone", dist_git_url, tmp], stderr=sp.STDOUT)
            except sp.CalledProcessError as exc:
                std_out = ""
                std_err = ""
                if exc.stdout:
                    std_out = exc.stdout.decode()
                if exc.stderr:
                    std_err = exc.stderr.decode()
                raise BuilderException(str(exc), std_out=std_out, std_err=std_err)

            specfile = os.path.join(tmp, package.name + ".spec")

            comment = "Update to %s (#%d)" % (package.version, bz_id)

            # This requires rpmdevtools-8.5 or greater
            cmd = [
                "/usr/bin/rpmdev-bumpspec",
                "--new",
                package.version,
                "-c",
                comment,
                "-u",
                " ".join(self.user_email),
                specfile,
            ]
            try:
                sp.check_output(cmd, stderr=sp.STDOUT)
            except sp.CalledProcessError as exc:
                std_out = ""
                std_err = ""
                if exc.stdout:
                    std_out = exc.stdout.decode()
                if exc.stderr:
                    std_err = exc.stderr.decode()
                raise BuilderException(str(exc), std_out=std_out, std_err=std_err)

            # We compare the old sources to the new ones to make sure we download
            # new sources from bumping the specfile version. Some packages don't
            # use macros in the source URL(s). We want to detect these and notify
            # the packager on the bug we filed about the new version.
            old_sources = self._dist_git_sources(tmp)
            new_sources = self._spec_sources(specfile, tmp)
            output["message"] = self._compare_sources(old_sources, new_sources)

            try:
                cmd_output = sp.check_output(
                    [
                        "rpmbuild",
                        "-D",
                        "_sourcedir .",
                        "-D",
                        "_topdir .",
                        "-bs",
                        specfile,
                    ],
                    cwd=tmp,
                    stderr=sp.STDOUT,
                )
            except sp.CalledProcessError as exc:
                std_out = ""
                std_err = ""
                if exc.stdout:
                    std_out = exc.stdout.decode()
                if exc.stderr:
                    std_err = exc.stderr.decode()
                raise BuilderException(
                    str(exc), value=output, std_out=std_out, std_err=std_err
                )

            srpm = os.path.join(tmp, cmd_output.decode("utf-8").strip().split()[-1])
            _logger.debug("Got srpm %r" % srpm)

            session = self._session_maker()
            if not session:
                raise BuilderException("Can't authenticate with Koji!")
            output["build_id"] = self._scratch_build(session, package.name, srpm)

            # Now, craft a patch to attach to the ticket
            try:
                sp.check_output(
                    ["git", "config", "user.name", self.user_email[0]],
                    cwd=tmp,
                    stderr=sp.STDOUT,
                )
                sp.check_output(
                    ["git", "config", "user.email", self.user_email[1]],
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
            except sp.CalledProcessError as exc:
                std_out = ""
                std_err = ""
                if exc.stdout:
                    std_out = exc.stdout.decode()
                if exc.stderr:
                    std_err = exc.stderr.decode()
                raise BuilderException(
                    str(exc), value=output, std_out=std_out, std_err=std_err
                )

            output["patch_filename"] = filename

            # Copy the content of file to output
            patch = os.path.join(tmp, filename)
            with open(patch) as f:
                output["patch"] = f.read()

            return output

    def _dist_git_sources(self, dist_git_path: str) -> list:
        """
        Retrieve sources from dist-git.

        Example:
            >>> dist_git_sources('/path/to/repo')
            ['/path/to/repo/source0.tar.gz', '/path/to/repo/source1.tar.gz']

        Params:
            dist_git_path: The filesystem path to the dist-git repository

        Returns:
            A list of absolute paths to source files downloaded

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

    def _spec_sources(self, specfile_path: str, target_dir: str) -> list:
        """
        Retrieve a specfile's sources and store them in the given target directory.

        Example:
            >>> spec_sources('/path/to/specfile', '/tmp/dir')
            ['/tmp/dir/source0.tar.gz', '/tmp/dir/source1.tar.gz']

        Params:
            specfile_path: The filesystem path to the specfile
            target_dir: The directory is where the file(s) will be saved.

        Returns:
            A list of absolute paths to source files downloaded

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
            elif e.returncode in (5, 6):
                msg = "Unable to resolve the hostname for one of the package's Source URLs"
            elif e.returncode == 7:
                # Failed to connect to the host
                msg = (
                    "Unable to connect to the host for one of the package's Source URLs"
                )
            elif e.returncode == 22:
                # cURL uses 22 for 400+ HTTP errors; the final line contains the specific code
                msg = (
                    "An HTTP error occurred downloading the package's new Source URLs: "
                    + e.output.decode().splitlines()[-1]
                )
            elif e.returncode == 60:
                msg = (
                    "Unable to validate the TLS certificate for one of the package's "
                    "Source URLs"
                )
            else:
                msg = (
                    "An unexpected error occurred while downloading the new package sources; "
                    "please report this as a bug on the-new-hotness issue tracker.\n"
                    "Error output:\n"
                    "{}".format(e.stderr)
                )
                _logger.error(
                    "{cmd} failed (exit {code}): {msg}".format(
                        cmd=e.cmd, code=e.returncode, msg=e.output.decode()
                    )
                )
            raise DownloadException(msg)

        return files

    def _compare_sources(self, old_sources: list, new_sources: list) -> str:
        """
        Compare two sets of files via checksum and raise an exception if both sets
        contain the same file.

        Params:
            old_sources: A list of filesystem paths to source tarballs.
            new_sources: A list of filesystem paths to source tarballs.

        Returns:
            String containing information message, it is returned when identical files
            are found, otherwise it's empty.
        """
        old_checksums = set()
        new_checksums = set()
        source_checksum = {}
        for sources, checksums in ((old_sources, old_checksums),):
            for file_path in sources:
                with open(file_path, "rb") as fd:
                    h = hashlib.sha512()
                    h.update(fd.read())
                    checksum = h.hexdigest()
                    checksums.add(checksum)
                    if checksum not in source_checksum:
                        source_checksum[checksum] = {
                            "old_sources": [],
                            "new_sources": [],
                        }
                    source_checksum[checksum]["old_sources"].append(
                        os.path.basename(file_path)
                    )

        for sources, checksums in ((new_sources, new_checksums),):
            for file_path in sources:
                with open(file_path, "rb") as fd:
                    h = hashlib.sha512()
                    h.update(fd.read())
                    checksum = h.hexdigest()
                    checksums.add(checksum)
                    if checksum not in source_checksum:
                        source_checksum[checksum] = {
                            "old_sources": [],
                            "new_sources": [],
                        }
                    source_checksum[checksum]["new_sources"].append(
                        os.path.basename(file_path)
                    )

        intersection_checksums = old_checksums.intersection(new_checksums)
        if intersection_checksums:
            files_string = ""
            for checksum in intersection_checksums:
                source_dict = source_checksum[checksum]
                old_sources = source_dict["old_sources"]
                new_sources = source_dict["new_sources"]
                files_string = (
                    files_string
                    + f"Old: {old_sources} -> New: {new_sources} ({checksum})\n"
                )
            return (
                "One or more of the new sources for this package are identical to "
                "the old sources. This is most likely caused either by identical source files "
                "between releases, for example service files, or the specfile does not use "
                "version macro in its source URLs. If this is the second case, then please "
                "update the specfile to use version macro in its source URLs.\n"
                "Here is the list of the files with SHA512 checksums:\n"
                f"{files_string}"
            )

        return ""

    def _session_maker(self) -> typing.Optional[koji.ClientSession]:
        """
        Creates a new koji session for the build.

        Returns:
            New koji session or None if authentication fails.
        """
        _logger.info("Creating a new Koji session to %s", self.server_url)
        with _koji_session_lock:
            koji_session = koji.ClientSession(self.server_url, self.krb_sessionopts)
            result = koji_session.krb_login(
                principal=self.krb_principal,
                keytab=self.krb_keytab,
                ccache=self.krb_ccache,
                proxyuser=self.krb_proxyuser,
            )
            if not result:
                _logger.error("Koji kerberos authentication failed")
                return None

            return koji_session

    def _scratch_build(
        self, session: koji.ClientSession, name: str, source: str
    ) -> int:
        """
        Uploads source RPM and starts scratch build of package in Koji.

        Params:
            session: Koji session to use for starting build.
            name: Name of the package to build
            source: Path to SRPM.

        Returns:
            Build id.
        """
        _logger.info("Uploading {source} to koji".format(source=source))
        suffix = "".join([random.choice(string.ascii_letters) for i in range(8)])
        serverdir = "%s/%r.%s" % ("cli-build", time.time(), suffix)
        session.uploadWrapper(source, serverdir)

        remote = "%s/%s" % (serverdir, os.path.basename(source))
        _logger.info(
            "Intiating koji build for %r"
            % dict(name=name, target=self.target_tag, source=remote, opts=self.opts)
        )
        task_id = session.build(
            remote, self.target_tag, self.opts, priority=self.priority
        )
        _logger.info(
            "Scratch build created for {name}: {url}".format(
                name=name, url=self.web_url + "/taskinfo?taskID={}".format(task_id)
            )
        )

        return task_id
