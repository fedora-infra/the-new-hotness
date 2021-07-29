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
import traceback
from typing import Any

from hotness.exceptions import BuilderException
from hotness.requests import Request
from hotness.responses import Response


class ResponseFailure(Response):
    """
    Class that represents failure response returned from use case.
    It is send when some exception happen during the use case.
    Defines constants for error types.

    Attributes:
        type: Type of the failure.
        message: Error message.
        traceback: Exception traceback as string.
        output: Partial use case output from Exception, if provided.
        std_out: Standard output from exception, if provided.
        std_err: Error output from exception, if provided.
    """

    VALIDATOR_ERROR = "ValidatorError"
    BUILDER_ERROR = "BuilderError"
    DATABASE_ERROR = "DatabaseError"
    NOTIFIER_ERROR = "NotifierError"
    PATCHER_ERROR = "PatherError"
    INVALID_REQUEST_ERROR = "InvalidRequestError"

    def __init__(self, type: str, message: Any) -> None:
        """
        Class constructor.
        """
        self.type = type
        self.message = self._format_message(message)
        self.traceback = self._get_stack_trace(message)
        self.output = self._get_output(message)
        self.stdout, self.stderr = self._get_std_out_err(message)

    def _get_std_out_err(self, message: Any) -> (str, str):
        """
        Retrieves the standard output and error output from Exception,
        otherwise just returns tuple with empty strings.

        Params:
            message: Input to retrieve use case output from

        Returns:
            Output if message is Exception, otherwise tuple containing empty strings
        """
        std_out = ""
        std_err = ""

        if type(message) is BuilderException:
            std_out = message.std_out
            std_err = message.std_err

        return (std_out, std_err)

    def _get_output(self, message: Any) -> dict:
        """
        Retrieves the use case output information from Exception,
        otherwise just returns empty dict.

        Params:
            message: Input to retrieve use case output from

        Returns:
            Output if message is Exception, otherwise empty dict
        """
        output = {}

        if isinstance(message, BuilderException):
            output = message.output

        return output

    def _get_stack_trace(self, message: Any) -> [str]:
        """
        Retrieves the stack trace information from Exception,
        otherwise just returns empty list.

        Params:
            message: Input to retrieve stack trace from

        Returns:
            Stack trace if message is Exception, otherwise empty string
        """
        stack_trace = []

        if isinstance(message, Exception):
            stack_trace = traceback.format_tb(message.__traceback__)

        return stack_trace

    def _format_message(self, message: Any) -> Any:
        """
        Formats the input message if the message inherits from Exception,
        otherwise just return it back.

        Params:
            message: Input message to format

        Returns:
            String if exception, otherwise return the same object we received.
        """
        if isinstance(message, Exception):
            return "{}: {}".format(message.__class__.__name__, "{}".format(message))

        return message

    @property
    def value(self):
        """
        Returns the dict representation of the failure response.
        """
        return {"type": self.type, "message": self.message}

    def __bool__(self) -> bool:
        """
        Boolean representation of response.
        """
        return False

    @classmethod
    def validator_error(cls, message: Any) -> "ResponseFailure":
        """
        Creates response for validator failure.

        Params:
            message: Message to add to this error

        Returns:
            ResponseFailure object
        """
        response = ResponseFailure(
            type=ResponseFailure.VALIDATOR_ERROR, message=message
        )

        return response

    @classmethod
    def builder_error(cls, message: Any) -> "ResponseFailure":
        """
        Creates response for builder failure.

        Params:
            message: Message to add to this error

        Returns:
            ResponseFailure object
        """
        response = ResponseFailure(type=ResponseFailure.BUILDER_ERROR, message=message)

        return response

    @classmethod
    def database_error(cls, message: Any) -> "ResponseFailure":
        """
        Creates response for database failure.

        Params:
            message: Message to add to this error

        Returns:
            ResponseFailure object
        """
        response = ResponseFailure(type=ResponseFailure.DATABASE_ERROR, message=message)

        return response

    @classmethod
    def notifier_error(cls, message: Any) -> "ResponseFailure":
        """
        Creates response for notifier failure.

        Params:
            message: Message to add to this error

        Returns:
            ResponseFailure object
        """
        response = ResponseFailure(type=ResponseFailure.NOTIFIER_ERROR, message=message)

        return response

    @classmethod
    def patcher_error(cls, message: Any) -> "ResponseFailure":
        """
        Creates response for patcher failure.

        Params:
            message: Message to add to this error

        Returns:
            ResponseFailure object
        """
        response = ResponseFailure(type=ResponseFailure.PATCHER_ERROR, message=message)

        return response

    @classmethod
    def invalid_request_error(cls, request: Request) -> "ResponseFailure":
        """
        Creates response for invalid request failure.

        Params:
            request: Invalid request to add to this error

        Returns:
            ResponseFailure object
        """
        response = ResponseFailure(
            type=ResponseFailure.INVALID_REQUEST_ERROR, message=str(request.errors)
        )

        return response
