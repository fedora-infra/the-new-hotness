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

from hotness.databases import Database
from hotness.requests import InsertDataRequest
from hotness import responses


logger = logging.getLogger(__name__)


class InsertDataUseCase:
    """
    This class represents use case for inserting key/value pairs using databases.

    Attributes:
        database: Database to use.
    """

    def __init__(self, database: Database):
        """
        Class constructor.
        """
        self.database = database

    def insert(self, request: InsertDataRequest) -> responses.Response:
        """
        Call the insert method on the database.
        This method will handle any error that happens when inserting data.

        Params:
            request: Request to handle.

        Return:
           Output of the data insertion.
        """
        if not request:
            return responses.ResponseFailure.invalid_request_error(request)
        try:
            result = self.database.insert(request.key, request.value)
            return responses.ResponseSuccess(result)
        except Exception as exc:
            logger.exception("Insert data use case failure", exc_info=True)
            return responses.ResponseFailure.database_error(exc)
