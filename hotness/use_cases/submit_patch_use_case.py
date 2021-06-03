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
import logging

from hotness.patchers import Patcher
from hotness.requests import SubmitPatchRequest
from hotness import responses


logger = logging.getLogger(__name__)


class SubmitPatchUseCase:
    """
    This class represents use case for submitting the patch to package with provided patcher.

    Attributes:
        patcher: Patcher to use.
    """

    def __init__(self, patcher: Patcher):
        """
        Class constructor.
        """
        self.patcher = patcher

    def submit_patch(self, request: SubmitPatchRequest) -> responses.Response:
        """
        Call the submit_patch method on the patcher.
        This method will handle any error that happens during submit of the patch.

        Params:
            request: Request to handle.

        Return:
           Output of the build.
        """
        if not request:
            return responses.ResponseFailure.invalid_request_error(request)
        try:
            result = self.patcher.submit_patch(
                request.package, request.patch, request.opts
            )
            return responses.ResponseSuccess(result)
        except Exception as exc:
            logger.exception("Submit patch use case failure", exc_info=True)
            return responses.ResponseFailure.patcher_error(exc)
