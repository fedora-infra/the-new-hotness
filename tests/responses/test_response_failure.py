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

from hotness.exceptions import BuilderException
from hotness.requests import Request
from hotness.responses import ResponseFailure


class TestResponseFailureInit:
    """
    Test class for `hotness.responses.response.ResponseFailure.__init__` method.
    """

    def test_init(self):
        """
        Assert that object is initialized correctly.
        """
        response = ResponseFailure(
            type=ResponseFailure.VALIDATOR_ERROR, message="This is heresy!"
        )

        assert response.type == ResponseFailure.VALIDATOR_ERROR
        assert response.value == {
            "type": ResponseFailure.VALIDATOR_ERROR,
            "message": "This is heresy!",
            "use_case_value": None,
        }
        assert response.traceback == []
        assert response.use_case_value is None


class TestResponseFailureBool:
    """
    Test class for `hotness.responses.response.ResponseFailure.__bool__` method.
    """

    def test_bool(self):
        """
        Assert that ResponseFailure always returns False.
        """
        response = ResponseFailure(
            type=ResponseFailure.VALIDATOR_ERROR, message=Exception("This is heresy!")
        )

        assert bool(response) is False


class TestResponseFailureValidatorError:
    """
    Test class for `hotness.responses.response.ResponseFailure.validator_error` method.
    """

    def test_validator_error(self):
        """
        Assert that validator error response is created correctly.
        """
        response = ResponseFailure.validator_error(
            message=Exception("This is validator heresy!")
        )

        assert response.type == ResponseFailure.VALIDATOR_ERROR
        assert response.value == {
            "type": ResponseFailure.VALIDATOR_ERROR,
            "message": "Exception: This is validator heresy!",
            "use_case_value": None,
        }


class TestResponseFailureBuilderError:
    """
    Test class for `hotness.responses.response.ResponseFailure.builder_error` method.
    """

    def test_builder_error(self):
        """
        Assert that builder error response is created correctly.
        """
        response = ResponseFailure.builder_error(
            message=Exception("This is builder heresy!")
        )

        assert response.type == ResponseFailure.BUILDER_ERROR
        assert response.value == {
            "type": ResponseFailure.BUILDER_ERROR,
            "message": "Exception: This is builder heresy!",
            "use_case_value": None,
        }

    def test_buider_exception(self):
        """
        Assert that `hotness.exceptions.BuilderException` is handled correctly.
        """
        builder_exception = BuilderException(
            "This is builder heresy!",
            value={"build_id": 100},
            std_out="This is a standard output.",
            std_err="This is an error output.",
        )

        response = ResponseFailure.builder_error(message=builder_exception)

        assert response.type == ResponseFailure.BUILDER_ERROR
        assert response.value == {
            "type": ResponseFailure.BUILDER_ERROR,
            "message": (
                "BuilderException: Build started, but failure happened "
                "during post build operations:\nThis is builder heresy!\n\n"
                "StdOut:\n"
                "This is a standard output.\n\n"
                "StdErr:\n"
                "This is an error output.\n"
            ),
            "use_case_value": {"build_id": 100},
        }
        assert response.traceback == traceback.format_tb(
            builder_exception.__traceback__
        )
        assert response.use_case_value == {"build_id": 100}


class TestResponseFailureDatabaseError:
    """
    Test class for `hotness.responses.response.ResponseFailure.database_error` method.
    """

    def test_database_error(self):
        """
        Assert that database error response is created correctly.
        """
        response = ResponseFailure.database_error(
            message=Exception("This is database heresy!")
        )

        assert response.type == ResponseFailure.DATABASE_ERROR
        assert response.value == {
            "type": ResponseFailure.DATABASE_ERROR,
            "message": "Exception: This is database heresy!",
            "use_case_value": None,
        }


class TestResponseFailureNotifierError:
    """
    Test class for `hotness.responses.response.ResponseFailure.notifier_error` method.
    """

    def test_notifier_error(self):
        """
        Assert that notifier error response is created correctly.
        """
        response = ResponseFailure.notifier_error(
            message=Exception("This is notifier heresy!")
        )

        assert response.type == ResponseFailure.NOTIFIER_ERROR
        assert response.value == {
            "type": ResponseFailure.NOTIFIER_ERROR,
            "message": "Exception: This is notifier heresy!",
            "use_case_value": None,
        }


class TestResponseFailurePatcherError:
    """
    Test class for `hotness.responses.response.ResponseFailure.patcher_error` method.
    """

    def test_patcher_error(self):
        """
        Assert that patcher error response is created correctly.
        """
        response = ResponseFailure.patcher_error(
            message=Exception("This is patcher heresy!")
        )

        assert response.type == ResponseFailure.PATCHER_ERROR
        assert response.value == {
            "type": ResponseFailure.PATCHER_ERROR,
            "message": "Exception: This is patcher heresy!",
            "use_case_value": None,
        }


class TestResponseFailureInvalidRequestError:
    """
    Test class for `hotness.responses.ResponseFailure.invalid_request_error` method.
    """

    def test_invalid_request_error(self):
        """
        Assert that invalid_request error response is created correctly.
        """
        request = Request()
        request.add_error("param", "You shall not pass!")
        response = ResponseFailure.invalid_request_error(request=request)

        assert response.type == ResponseFailure.INVALID_REQUEST_ERROR
        assert response.value == {
            "type": ResponseFailure.INVALID_REQUEST_ERROR,
            "message": "[{'parameter': 'param', 'error': 'You shall not pass!'}]",
            "use_case_value": None,
        }
