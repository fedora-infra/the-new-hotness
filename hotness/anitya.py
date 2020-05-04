# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Red Hat, Inc.
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
import logging

from fedora.client import OpenIdBaseClient


ANITYA_URL = "https://release-monitoring.org/"


_log = logging.getLogger(__name__)


class Anitya(OpenIdBaseClient):
    def __init__(self, url=ANITYA_URL, insecure=False):
        super(Anitya, self).__init__(
            base_url=url,
            login_url=url + "/login/fedora",
            useragent="The New Hotness",
            debug=False,
            insecure=insecure,
            openid_insecure=insecure,
            username=None,  # We supply this later
            cache_session=True,
            retries=7,
            timeout=120,
            retry_backoff_factor=0.3,
        )

    def force_check(self, project_id):
        """ Force anitya to check for a new upstream release. """
        url = "%s/api/version/get" % self.base_url
        data = self.send_request(url, verb="POST", data=dict(id=project_id))

        if "error" in data:
            _log.warning("Anitya error: %r" % data["error"])
        else:
            _log.info(
                "Check yielded upstream version %s for %s"
                % (data["version"], data["name"])
            )
