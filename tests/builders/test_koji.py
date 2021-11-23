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
import os
import pytest
from subprocess import CalledProcessError
from unittest import mock

from hotness.domain import Package
from hotness.exceptions import DownloadException, BuilderException
from hotness.builders import Koji


class TestKojiInit:
    """
    Test class for `hotness.builders.Koji.__init__` method.
    """

    def test_init(self):
        """
        Assert that Koji builder object is initialized correctly.
        """
        server_url = "https://example.com/koji"
        web_url = "https://example.com/kojihub"
        kerberos_args = {
            "krb_principal": "High Priest of Terra",
            "krb_keytab": "Tab with keys",
            "krb_ccache": "Clear cache",
            "krb_proxyuser": "Roboute Guiliman",
            "krb_sessionopts": {
                "timeout": 3600,
                "krb_rdns": False,
            },
        }
        git_url = "https://src.example.com/"
        user_email = ("Emperor of Mankind", "emperor@ter.ra")
        opts = {}
        priority = 30
        target_tag = "rawhide"

        builder = Koji(
            server_url,
            web_url,
            kerberos_args,
            git_url,
            user_email,
            opts,
            priority,
            target_tag,
        )

        assert builder.server_url == server_url
        assert builder.web_url == web_url
        assert builder.krb_principal == kerberos_args["krb_principal"]
        assert builder.krb_keytab == kerberos_args["krb_keytab"]
        assert builder.krb_ccache == kerberos_args["krb_ccache"]
        assert builder.krb_proxyuser == kerberos_args["krb_proxyuser"]
        assert builder.krb_sessionopts == kerberos_args["krb_sessionopts"]
        assert builder.git_url == git_url
        assert builder.user_email == user_email
        assert builder.opts == opts
        assert builder.priority == priority
        assert builder.target_tag == target_tag


class TestKojiBuild:
    """
    Test class for `hotness.builders.Koji.build` method.
    """

    def setup(self):
        """
        Create builder instance for tests.
        """
        server_url = "https://example.com/koji"
        web_url = "https://example.com/kojihub"
        kerberos_args = {
            "krb_principal": "High Priest of Terra",
            "krb_keytab": "Tab with keys",
            "krb_ccache": "Clear cache",
            "krb_proxyuser": "Roboute Guiliman",
            "krb_sessionopts": {
                "timeout": 3600,
                "krb_rdns": False,
            },
        }
        git_url = "https://src.example.com/"
        user_email = ("Emperor of Mankind", "emperor@ter.ra")
        opts = {}
        priority = 30
        target_tag = "rawhide"

        self.builder = Koji(
            server_url,
            web_url,
            kerberos_args,
            git_url,
            user_email,
            opts,
            priority,
            target_tag,
        )

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.koji")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build(self, mock_temp_dir, mock_koji, mock_check_output, tmpdir):
        """
        Assert that correct output is returned when build starts without issue.
        """
        # Create temporary file
        file = os.path.join(tmpdir, "Lectitio_Divinitatus")
        with open(file, "w") as f:
            f.write("The Emperor is God")
        file = os.path.join(tmpdir, "Codex_Astartes")
        with open(file, "w") as f:
            f.write("Adeptus Astartes")

        # Mock patch file
        filename = "patch"
        file = os.path.join(tmpdir, filename)
        with open(file, "w") as f:
            f.write("This is a patch")
        mock_session = mock.Mock()
        mock_session.build.return_value = 1000
        mock_session.krb_login.return_value = True
        mock_koji.ClientSession.return_value = mock_session
        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        mock_check_output.side_effect = [
            "git clone",
            "rpmdev-bumpspec",
            b"Downloading Lectitio_Divinitatus",
            b"Getting Codex_Astartes",
            b"rpmbuild foobar.srpm",
            "git config",
            "git config",
            "git commit",
            filename.encode(),
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        output = self.builder.build(package, opts)

        assert output == {
            "build_id": 1000,
            "patch": "This is a patch",
            "patch_filename": filename,
            "message": "",
        }

        mock_temp_dir.assert_called_with(prefix="thn-", dir="/var/tmp")
        mock_koji.ClientSession.assert_called_with(
            self.builder.server_url, self.builder.krb_sessionopts
        )
        mock_session.krb_login.assert_called_with(
            principal=self.builder.krb_principal,
            keytab=self.builder.krb_keytab,
            ccache=self.builder.krb_ccache,
            proxyuser=self.builder.krb_proxyuser,
        )
        mock_session.uploadWrapper.assert_called_once()
        mock_session.build.assert_called_once()

        mock_check_output.assert_has_calls(
            [
                mock.call(
                    ["git", "clone", self.builder.git_url, tmpdir], stderr=mock.ANY
                ),
                mock.call(
                    [
                        "/usr/bin/rpmdev-bumpspec",
                        "--new",
                        "1.0",
                        "-c",
                        "Update to 1.0 (#100)",
                        "-u",
                        self.builder.user_email[0] + " " + self.builder.user_email[1],
                        tmpdir + "/test.spec",
                    ],
                    stderr=mock.ANY,
                ),
                mock.call(["fedpkg", "--user", "hotness", "sources"], cwd=tmpdir),
                mock.call(
                    [
                        "spectool",
                        "-g",
                        str(tmpdir + "/test.spec"),
                    ],
                    cwd=tmpdir,
                ),
                mock.call(
                    [
                        "rpmbuild",
                        "-D",
                        "_sourcedir .",
                        "-D",
                        "_topdir .",
                        "-bs",
                        tmpdir + "/test.spec",
                    ],
                    cwd=tmpdir,
                    stderr=mock.ANY,
                ),
                mock.call(
                    ["git", "config", "user.name", self.builder.user_email[0]],
                    cwd=tmpdir,
                    stderr=mock.ANY,
                ),
                mock.call(
                    ["git", "config", "user.email", self.builder.user_email[1]],
                    cwd=tmpdir,
                    stderr=mock.ANY,
                ),
                mock.call(
                    ["git", "commit", "-a", "-m", "Update to 1.0 (#100)"],
                    cwd=tmpdir,
                    stderr=mock.ANY,
                ),
                mock.call(
                    ["git", "format-patch", "HEAD^"], cwd=tmpdir, stderr=mock.ANY
                ),
            ]
        )

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.koji")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_identical_sources(
        self, mock_temp_dir, mock_koji, mock_check_output, tmpdir
    ):
        """
        Assert that correct output is returned when sources from current package
        and new build are identical.
        """
        # Create temporary file
        file = os.path.join(tmpdir, "Lectitio_Divinitatus")
        with open(file, "w") as f:
            f.write("The Emperor is God")

        # Mock patch file
        file = os.path.join(tmpdir, "patch")
        with open(file, "w") as f:
            f.write("This is a patch")
        mock_session = mock.Mock()
        mock_session.build.return_value = 1000
        mock_session.krb_login.return_value = True
        mock_koji.ClientSession.return_value = mock_session
        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        mock_check_output.side_effect = [
            "git clone",
            "rpmdev-bumpspec",
            (b"Fake line\n" b"Downloading Lectitio_Divinitatus"),
            b"Getting Lectitio_Divinitatus",
            b"rpmbuild foobar.srpm",
            "git config",
            "git config",
            "git commit",
            file.encode(),
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        output = self.builder.build(package, opts)

        assert output == {
            "build_id": 1000,
            "patch": "This is a patch",
            "patch_filename": file,
            "message": (
                "One or more of the new sources for this package are identical to "
                "the old sources. This is most likely caused either by identical source files "
                "between releases, for example service files, or the specfile does not use "
                "version macro in its source URLs. If this is the second case, then please "
                "update the specfile to use version macro in its source URLs.\n"
                "Here is the list of the files with SHA512 checksums:\n"
                "Old: ['Lectitio_Divinitatus'] -> New: ['Lectitio_Divinitatus'] "
                "(96140cc21155a13c9bfa03377410ac63e3f7e6aef22cc3bf09c4efbfad1c7ced"
                "45e150e391c23271dfe49df71c60f1547fbe70ed47d5bc515ff00271309939f7)\n"
            ),
        }

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.koji")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_identical_new_sources(
        self, mock_temp_dir, mock_koji, mock_check_output, tmpdir
    ):
        """
        Assert that correct output is returned when sources from current package
        and new build are identical.
        """
        # Create temporary file
        file = os.path.join(tmpdir, "Lectitio_Divinitatus")
        with open(file, "w") as f:
            f.write("The Emperor is God")

        # Mock patch file
        file = os.path.join(tmpdir, "patch")
        with open(file, "w") as f:
            f.write("This is a patch")
        mock_session = mock.Mock()
        mock_session.build.return_value = 1000
        mock_session.krb_login.return_value = True
        mock_koji.ClientSession.return_value = mock_session
        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        mock_check_output.side_effect = [
            "git clone",
            "rpmdev-bumpspec",
            (b"Fake line\n" b"Downloading Lectitio_Divinitatus\n"),
            b"Getting Lectitio_Divinitatus\nGetting Lectitio_Divinitatus\n",
            b"rpmbuild foobar.srpm",
            "git config",
            "git config",
            "git commit",
            file.encode(),
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        output = self.builder.build(package, opts)

        assert output == {
            "build_id": 1000,
            "patch": "This is a patch",
            "patch_filename": file,
            "message": (
                "One or more of the new sources for this package are identical to "
                "the old sources. This is most likely caused either by identical source files "
                "between releases, for example service files, or the specfile does not use "
                "version macro in its source URLs. If this is the second case, then please "
                "update the specfile to use version macro in its source URLs.\n"
                "Here is the list of the files with SHA512 checksums:\n"
                "Old: ['Lectitio_Divinitatus'] -> New: ['Lectitio_Divinitatus', "
                "'Lectitio_Divinitatus'] (96140cc21155a13c9bfa03377410ac63e3"
                "f7e6aef22cc3bf09c4efbfad1c7ced45e150e391c23271dfe49df71c60f"
                "1547fbe70ed47d5bc515ff00271309939f7)\n"
            ),
        }

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.koji")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_session_missing(
        self, mock_temp_dir, mock_koji, mock_check_output, tmpdir
    ):
        """
        Assert that build fails when we can't obtain a koji session.
        """
        # Create temporary file
        file = os.path.join(tmpdir, "Lectitio_Divinitatus")
        with open(file, "w") as f:
            f.write("The Emperor is God")

        mock_session = mock.Mock()
        mock_session.krb_login.return_value = None
        mock_koji.ClientSession.return_value = mock_session
        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        mock_check_output.side_effect = [
            "git clone",
            "rpmdev-bumpspec",
            b"Downloading Lectitio_Divinitatus",
            b"Getting Lectitio_Divinitatus",
            b"rpmbuild foobar.srpm",
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        with pytest.raises(BuilderException) as exc:
            self.builder.build(package, opts)

        assert exc.value.message == ("Can't authenticate with Koji!")

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.koji")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_download_error_1(
        self, mock_temp_dir, mock_koji, mock_check_output, tmpdir
    ):
        """
        Assert that build fails when spectool throws error 1.
        """
        # Create temporary file
        file = os.path.join(tmpdir, "Lectitio_Divinitatus")
        with open(file, "w") as f:
            f.write("The Emperor is God")

        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        mock_check_output.side_effect = [
            "git clone",
            "rpmdev-bumpspec",
            b"Downloading Lectitio_Divinitatus",
            CalledProcessError(1, None),
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        with pytest.raises(DownloadException) as exc:
            self.builder.build(package, opts)

        assert exc.value.message == (
            "The specfile contains a Source URL with an unknown protocol; it should"
            'be "https", "http", or "ftp".'
        )

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.koji")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_download_error_5(
        self, mock_temp_dir, mock_koji, mock_check_output, tmpdir
    ):
        """
        Assert that build fails when spectool throws error 5.
        """
        # Create temporary file
        file = os.path.join(tmpdir, "Lectitio_Divinitatus")
        with open(file, "w") as f:
            f.write("The Emperor is God")

        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        mock_check_output.side_effect = [
            "git clone",
            "rpmdev-bumpspec",
            b"Downloading Lectitio_Divinitatus",
            CalledProcessError(5, None),
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        with pytest.raises(DownloadException) as exc:
            self.builder.build(package, opts)

        assert exc.value.message == (
            "Unable to resolve the hostname for one of the package's Source URLs"
        )

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.koji")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_download_error_7(
        self, mock_temp_dir, mock_koji, mock_check_output, tmpdir
    ):
        """
        Assert that build fails when spectool throws error 7.
        """
        # Create temporary file
        file = os.path.join(tmpdir, "Lectitio_Divinitatus")
        with open(file, "w") as f:
            f.write("The Emperor is God")

        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        mock_check_output.side_effect = [
            "git clone",
            "rpmdev-bumpspec",
            b"Downloading Lectitio_Divinitatus",
            CalledProcessError(7, None),
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        with pytest.raises(DownloadException) as exc:
            self.builder.build(package, opts)

        assert exc.value.message == (
            "Unable to connect to the host for one of the package's Source URLs"
        )

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.koji")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_download_error_22(
        self, mock_temp_dir, mock_koji, mock_check_output, tmpdir
    ):
        """
        Assert that build fails when spectool throws error 22.
        """
        # Create temporary file
        file = os.path.join(tmpdir, "Lectitio_Divinitatus")
        with open(file, "w") as f:
            f.write("The Emperor is God")

        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        mock_check_output.side_effect = [
            "git clone",
            "rpmdev-bumpspec",
            b"Downloading Lectitio_Divinitatus",
            CalledProcessError(22, None, output=(b"URL1\nURL2")),
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        with pytest.raises(DownloadException) as exc:
            self.builder.build(package, opts)

        assert exc.value.message == (
            "An HTTP error occurred downloading the package's new Source URLs: URL2"
        )

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.koji")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_download_error_60(
        self, mock_temp_dir, mock_koji, mock_check_output, tmpdir
    ):
        """
        Assert that build fails when spectool throws error 60.
        """
        # Create temporary file
        file = os.path.join(tmpdir, "Lectitio_Divinitatus")
        with open(file, "w") as f:
            f.write("The Emperor is God")

        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        mock_check_output.side_effect = [
            "git clone",
            "rpmdev-bumpspec",
            b"Downloading Lectitio_Divinitatus",
            CalledProcessError(60, None),
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        with pytest.raises(DownloadException) as exc:
            self.builder.build(package, opts)

        assert exc.value.message == (
            "Unable to validate the TLS certificate for one of the package's "
            "Source URLs"
        )

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.koji")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_download_unexpected_error(
        self, mock_temp_dir, mock_koji, mock_check_output, tmpdir
    ):
        """
        Assert that build fails when spectool throws unexpected error.
        """
        # Create temporary file
        file = os.path.join(tmpdir, "Lectitio_Divinitatus")
        with open(file, "w") as f:
            f.write("The Emperor is God")

        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        mock_check_output.side_effect = [
            "git clone",
            "rpmdev-bumpspec",
            b"Downloading Lectitio_Divinitatus",
            CalledProcessError(100, "spectool -g", output=b"Some output"),
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        with pytest.raises(DownloadException) as exc:
            self.builder.build(package, opts)

        assert exc.value.message == (
            "An unexpected error occurred while downloading the new package sources; "
            "please report this as a bug on the-new-hotness issue tracker.\n"
            "Error output:\n"
            "None"
        )

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_git_clone_error(self, mock_temp_dir, mock_check_output, tmpdir):
        """
        Assert that build fails with BuilderException when git clone raises error.
        """
        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        mock_check_output.side_effect = [
            CalledProcessError(
                1, "git clone", output=b"Some output", stderr=b"Failed miserably"
            ),
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        with pytest.raises(BuilderException) as exc:
            self.builder.build(package, opts)

        assert (
            exc.value.message == "Command 'git clone' returned non-zero exit status 1."
        )
        assert exc.value.value == {}
        assert exc.value.std_out == "Some output"
        assert exc.value.std_err == "Failed miserably"

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_rpmdev_bumpspec_error(
        self, mock_temp_dir, mock_check_output, tmpdir
    ):
        """
        Assert that build fails with BuilderException when rpmdev-bumpspec raises error.
        """
        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        mock_check_output.side_effect = [
            "git clone",
            CalledProcessError(
                1, "rpmdev-bumpspec", output=b"Some output", stderr=b"Failed miserably"
            ),
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        with pytest.raises(BuilderException) as exc:
            self.builder.build(package, opts)

        assert (
            exc.value.message
            == "Command 'rpmdev-bumpspec' returned non-zero exit status 1."
        )
        assert exc.value.value == {}
        assert exc.value.std_out == "Some output"
        assert exc.value.std_err == "Failed miserably"

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_rpmbuild_error(self, mock_temp_dir, mock_check_output, tmpdir):
        """
        Assert that build fails with BuilderException when rpmbuild raises error.
        """
        # Create temporary file
        file = os.path.join(tmpdir, "Lectitio_Divinitatus")
        with open(file, "w") as f:
            f.write("The Emperor is God")

        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        mock_check_output.side_effect = [
            "git clone",
            "rpmdev-bumpspec",
            (b"Fake line\n" b"Downloading Lectitio_Divinitatus\n"),
            b"Getting Lectitio_Divinitatus\n",
            CalledProcessError(
                1, "rpmdevbuild", output=b"Some output", stderr=b"Failed miserably"
            ),
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        with pytest.raises(BuilderException) as exc:
            self.builder.build(package, opts)

        assert (
            exc.value.message
            == "Command 'rpmdevbuild' returned non-zero exit status 1."
        )
        assert exc.value.value["message"] != ""
        assert exc.value.std_out == "Some output"
        assert exc.value.std_err == "Failed miserably"

    @mock.patch("hotness.builders.koji.sp.check_output")
    @mock.patch("hotness.builders.koji.koji")
    @mock.patch("hotness.builders.koji.TemporaryDirectory")
    def test_build_git_commit_error(
        self, mock_temp_dir, mock_koji, mock_check_output, tmpdir
    ):
        """
        Assert that build fails with BuilderException when git commit raises error.
        """
        # Create temporary file
        file = os.path.join(tmpdir, "Lectitio_Divinitatus")
        with open(file, "w") as f:
            f.write("The Emperor is God")

        mock_session = mock.Mock()
        mock_session.build.return_value = 1000
        mock_session.krb_login.return_value = True
        mock_koji.ClientSession.return_value = mock_session
        mock_temp_dir.return_value.__enter__.return_value = tmpdir

        mock_check_output.side_effect = [
            "git clone",
            "rpmdev-bumpspec",
            (b"Fake line\n" b"Downloading Lectitio_Divinitatus\n"),
            b"Getting Lectitio_Divinitatus\n",
            b"rpmbuild foobar.srpm",
            "git config",
            "git config",
            CalledProcessError(
                1, "git commit", output=b"Some output", stderr=b"Failed miserably"
            ),
            file.encode(),
        ]

        # Prepare package
        package = Package(name="test", version="1.0", distro="Fedora")
        opts = {"bz_id": 100}

        with pytest.raises(BuilderException) as exc:
            self.builder.build(package, opts)

        assert (
            exc.value.message == "Command 'git commit' returned non-zero exit status 1."
        )
        assert exc.value.value["build_id"] == 1000
        assert exc.value.std_out == "Some output"
        assert exc.value.std_err == "Failed miserably"
