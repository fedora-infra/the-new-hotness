# -*- coding: utf-8 -*-
#
# This file is part of the-new-hotness project.
# Copyright (C) 2020-2021  Red Hat, Inc.
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
import logging
from typing import Dict

from packit.config import Config, PackageConfig
from packit.distgit import DistGit
from packit.utils import run_command

from hotness.domain import Package
from .patcher import Patcher

_logger = logging.getLogger(__name__)


class Pagure(Patcher):
    """
    This class is a wrapper above `packit` module https://github.com/packit-service/packit.
    It handles creation of pull request to
    Fedora dist-git repository https://src.fedoraproject.org/.

    Attributes:
        config (`Config`): Packit configuration
        dist_git_url (str): Dist git URL
        changelog_template (str): Changelog template to use when creating
            changelog entry
        pr_template (str): Pull request message template
    """

    def __init__(
        self,
        dist_git_url: str,
        pagure_user_token: str,
        fas_user: str,
        changelog_template: str,
        pr_template: str
    ) -> None:
        """
        Constructor. It creates config for the packit module.

        Params:
            dist_git_url: Pagure dist-git URL to file PR against
            pagure_user_token: API token for pagure. The token needs
                to allow the user to fork projects and file pull requests
            fas_user: User to use for pagure dist-git
            changelog_template: Template for changelog message
            pr_template: Pull request message template
        """
        self.dist_git_url = config["dist_git_url"]
        raw_packit_config = {
            "authentication": {
                "pagure": {
                    "token": config["pagure_user_token"],
                    "instance_url": self.dist_git_url,
                }
            }
        }

        self.config = Config(fas_user=config["fas_user"], **raw_packit_config)

        self.changelog_template = config["changelog_template"]
        self.pr_template = config["pull_request_template"]

    def submit_patch(self, package: Package, patch: str, opts: dict) -> dict:
        """
        This method is inherited from `hotness.patchers.Patcher`.

        Create pull request against downstream repository.

        Params:
            package: Package to create notification for
            patch: Patch to attach. Not used by this patcher
            opts: Additional options for pagure. Example:
                {
                    "bz_id": 100, # Bugzilla ticket id
                }

        Returns:
            Dictionary containing pull request url
            Example:
            {
                "pull_request_url": "https://src.fedoraproject.org/rpms/repo/pull-request/0"
            }
        """
        package_config = PackageConfig(
            downstream_package_name=package.name, dist_git_base_url=self.dist_git_url
        )

        dist_git = DistGit(self.config, package_config)

        # Use master branch
        branch = "rawhide"

        _logger.info(
            "Creating pull request for '{}' in dist-git repository '{}'".format(
                package, package_config.dist_git_package_url
            )
        )

        dist_git.update_branch(branch)
        self._bump_spec(package.version, dist_git.absolute_specfile_path)

        title = self.changelog_template.format(version=package.version)
        dist_git.commit(title, "", prefix="[the-new-hotness]")
        dist_git.push_to_fork(branch)
        msg = self.pr_template.format(package=package, version=version)
        dist_git.create_pull(title, msg, branch, branch)

    def _bump_spec(self, version: str, specfile_path: str):
        """
        Run rpmdev-bumpspec on the upstream spec file: it enables
        changing version and adding a changelog entry

        Params:
            version: New version
            specfile_path: Path to specfile
        """
        _logger.debug(
            "Update specfile '{}' to version '{}'".format(specfile_path, version)
        )
        changelog_entry = self.changelog_template.format(version=version)
        cmd = ["rpmdev-bumpspec"]
        if version:
            # 1.2.3-4 means, version = 1.2.3, release = 4
            cmd += ["--new", version]
        if changelog_entry:
            cmd += ["--comment", changelog_entry]
        cmd.append(str(specfile_path))

        run_command(cmd)
