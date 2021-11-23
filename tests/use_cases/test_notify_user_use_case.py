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
from unittest import mock

from hotness.use_cases import NotifyUserUseCase
from hotness import responses


class TestNotifyUserUseCaseInit:
    """
    Test class for `hotness.use_cases.NotifyUserUseCase.__init__` method
    """

    def test_init(self):
        """
        Assert that the object is correctly created.
        """
        notifier = mock.Mock()

        use_case = NotifyUserUseCase(notifier=notifier)

        assert use_case.notifier == notifier


class TestNotifyUserUseCaseNotify:
    """
    Test class for `hotness.use_cases.NotifyUserUseCase.notify` method
    """

    def test_notify(self):
        """
        Assert that the notify is called correctly and successful response
        is returned when no error is encountered.
        """
        message = "message"
        opts = {}
        notifier = mock.Mock()
        notifier.notify.return_value = {"message_sent": message}

        package = mock.Mock()
        request = mock.MagicMock()
        request.package = package
        request.message = message
        request.opts = opts
        request.__bool__.return_value = True

        use_case = NotifyUserUseCase(notifier=notifier)

        result = use_case.notify(request)

        notifier.notify.assert_called_with(package, message, opts)
        assert type(result) is responses.ResponseSuccess
        assert bool(result) is True
        assert result.value == {"message_sent": message}

    def test_notify_invalid_request(self):
        """
        Assert that the notify fails when request validation fails.
        """
        errors = [
            {
                "parameter": "param",
                "error": "This is not the parameter you are looking for.",
            }
        ]
        notifier = mock.Mock()

        request = mock.MagicMock()
        request.__bool__.return_value = False
        request.errors = errors

        use_case = NotifyUserUseCase(notifier=notifier)

        result = use_case.notify(request)

        assert type(result) is responses.ResponseFailure
        assert bool(result) is False
        assert result.value == {
            "type": responses.ResponseFailure.INVALID_REQUEST_ERROR,
            "message": str(errors),
            "use_case_value": None,
        }

    def test_notify_failure(self):
        """
        Assert that the notify is called correctly and failure response
        is returned when notifier raises exception.
        """
        message = "message"
        opts = {}
        notifier = mock.Mock()
        notifier.notify.side_effect = Exception("This is heresy!")

        package = mock.Mock()
        request = mock.MagicMock()
        request.package = package
        request.message = message
        request.opts = opts
        request.__bool__.return_value = True

        use_case = NotifyUserUseCase(notifier=notifier)

        result = use_case.notify(request)

        notifier.notify.assert_called_with(package, message, opts)
        assert type(result) is responses.ResponseFailure
        assert bool(result) is False
        assert result.value == {
            "type": responses.ResponseFailure.NOTIFIER_ERROR,
            "message": "Exception: This is heresy!",
            "use_case_value": None,
        }
