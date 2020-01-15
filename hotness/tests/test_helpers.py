"""
Unit tests for hotness.helpers
"""
from __future__ import unicode_literals, absolute_import

import unittest
import re

from unittest.mock import Mock, call, patch
from hotness import helpers


class TestHelpers(unittest.TestCase):
    def test_expand_subdirs_no_match(self):
        # Test no glob match
        self.assertEqual(
            helpers.expand_subdirs("https://example.com"), "https://example.com"
        )

    def test_expand_subdirs_no_directory_listing(self):
        # Test no directory listing
        with patch.object(helpers, "get_html") as mock_get_html:
            mock_get_html.return_value = None

            self.assertEqual(
                helpers.expand_subdirs("https://example.com/*/"),
                "https://example.com/*/",
            )

    def test_expand_subdirs_hrefs(self):
        # Test with no subdirs
        root_hrefs = ['<a href="./">.</a>', '<a href="../">..</a>']

        with patch.object(helpers, "get_html") as mock_get_html:
            mock_get_html.return_value = " ".join(root_hrefs)

            self.assertEqual(
                helpers.expand_subdirs("https://example.com/*/"),
                "https://example.com/*/",
            )

        # Test with href subdirs
        package_hrefs = [
            '<a href="./">.</a>',
            '<a href="../">..</a>',
            '<a href="package-1.0.0/">package-1.0.0</a>',
            '<a href="package-2.0.0/">package-2.0.0</a>',
        ]

        with patch.object(helpers, "get_html") as mock_get_html:
            mock_get_html.return_value = " ".join(root_hrefs + package_hrefs)

            self.assertEqual(
                helpers.expand_subdirs("https://example.com/*/"),
                "https://example.com/package-2.0.0/",
            )

    def test_expand_subdirs_ftp(self):
        # Test with ftp subdirs
        # Derived from ftp://gcc.gnu.org/pub/gcc/
        package_ftp_paths = [
            "drwxrwsr-x   8 ftp      ftp          4096 Feb  5  2015 .",
            "drwxrwsr-x  56 ftp      ftp          4096 Oct  1 20:11 ..",
            "drwxrwsr-x   4 ftp      ftp          4096 Feb 12  2017 package-1.0.0",
            "drwxrwsr-x   4 ftp      ftp          4096 Feb 12  2017 package-2.0.0",
        ]

        with patch.object(helpers, "get_html") as mock_get_html:
            mock_get_html.return_value = "\r\n".join(package_ftp_paths)

            self.assertEqual(
                helpers.expand_subdirs("ftp://example.com/*/"),
                "ftp://example.com/package-2.0.0/",
            )

    def test_get_html_ftp(self):
        import urllib

        # Test ftp
        mock_ftp_request = Mock()
        mock_ftp_request.read.return_value = "mock FTP read value"

        with patch.object(urllib.request, "urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_ftp_request

            get_html_result = helpers.get_html("ftp://example.com/file.extension")

            self.assertEqual(get_html_result, "mock FTP read value")

            # Test ftp with callback list
            mock_get_html_callback = Mock()

            get_html_result = helpers.get_html(
                "ftp://example.com/file.extension", callback=[mock_get_html_callback]
            )

            self.assertEqual(get_html_result, "mock FTP read value")
            mock_get_html_callback.assert_called_once_with("mock FTP read value")

            # Test ftp with single callback
            mock_get_html_callback = Mock()

            get_html_result = helpers.get_html(
                "ftp://example.com/file.extension", callback=mock_get_html_callback
            )

            self.assertEqual(get_html_result, "mock FTP read value")
            mock_get_html_callback.assert_called_once_with("mock FTP read value")

    def test_get_html_http_callbacks_list(self):
        import twisted.web.client

        # Test http with callbacks
        with patch.object(twisted.web.client, "getPage") as mock_twisted_client_getpage:
            mock_get_html_callback = Mock()

            # Test with callback list
            mock_twisted_async_request = Mock()
            mock_twisted_client_getpage.return_value = mock_twisted_async_request

            helpers.get_html(
                "https://example.com/file.extension", callback=[mock_get_html_callback]
            )

            mock_twisted_async_request.addCallback.assert_called_once_with(
                mock_get_html_callback
            )

    def test_get_html_http_callbacks_single(self):
        import twisted.web.client

        # Test http with callbacks
        with patch.object(twisted.web.client, "getPage") as mock_twisted_client_getpage:
            mock_get_html_callback = Mock()

            # Test with single callback
            mock_twisted_async_request = Mock()
            mock_twisted_client_getpage.return_value = mock_twisted_async_request

            helpers.get_html(
                "https://example.com/file.extension", callback=mock_get_html_callback
            )

            mock_twisted_async_request.addCallback.assert_called_once_with(
                mock_get_html_callback
            )

    def test_get_html_http_errbacks_list(self):
        import twisted.web.client

        # Test http with callbacks
        with patch.object(twisted.web.client, "getPage") as mock_twisted_client_getpage:
            mock_get_html_errback = Mock()

            # Test with errback list
            mock_twisted_async_request = Mock()
            mock_twisted_client_getpage.return_value = mock_twisted_async_request

            helpers.get_html(
                "https://example.com/file.extension",
                callback=Mock(),
                errback=[mock_get_html_errback],
            )

            mock_twisted_async_request.addErrback.assert_called_once_with(
                mock_get_html_errback
            )

    def test_get_html_http_errbacks_single(self):
        import twisted.web.client

        # Test http with callbacks
        with patch.object(twisted.web.client, "getPage") as mock_twisted_client_getpage:
            mock_get_html_errback = Mock()

            # Test with single errback
            mock_twisted_async_request = Mock()
            mock_twisted_client_getpage.return_value = mock_twisted_async_request

            helpers.get_html(
                "https://example.com/file.extension",
                callback=Mock(),
                errback=mock_get_html_errback,
            )

            mock_twisted_async_request.addErrback.assert_called_once_with(
                mock_get_html_errback
            )

    def test_get_html_http_no_callbacks(self):
        import pycurl
        import io

        # Test http with no callbacks
        mock_curl_instance = Mock()
        mock_stringio_instance = Mock()

        mock_stringio_instance.getvalue.return_value = "mock StringIO value"

        # Expected pycurl setopt calls
        expected_setopt_calls = [
            call(pycurl.URL, b"https://example.com/file.extension"),
            call(pycurl.WRITEFUNCTION, mock_stringio_instance.write),
            call(pycurl.FOLLOWLOCATION, 1),
            call(pycurl.MAXREDIRS, 10),
            call(
                pycurl.USERAGENT,
                "Fedora Upstream Release Monitoring "
                "(https://fedoraproject.org/wiki/Upstream_release_monitoring)",
            ),
            call(pycurl.CONNECTTIMEOUT, 10),
            call(pycurl.TIMEOUT, 30),
        ]

        with patch.object(pycurl, "Curl") as mock_curl_constructor:
            with patch.object(io, "StringIO") as mock_stringio_constructor:
                mock_curl_constructor.return_value = mock_curl_instance
                mock_stringio_constructor.return_value = mock_stringio_instance

                get_html_result = helpers.get_html("https://example.com/file.extension")

        # Check curl calls
        mock_curl_instance.setopt.assert_has_calls(expected_setopt_calls)
        mock_curl_instance.perform.assert_called_once_with()
        mock_curl_instance.close.assert_called_once_with()

        self.assertEqual(get_html_result, "mock StringIO value")

    def test_rpm_cmp(self):
        cases = [
            ("rc1", "pre1", 1),
            ("beta1", "pre1", -1),
            ("beta1", "alpha1", 1),
            ("rc1", "rc2", -1),
            ("rc3", "rc2", 1),
            ("rc3", "rc3", 0),
            ("rc1", "rc", 1),
            ("rc", "rc1", -1),
            ("rc", "rc", 0),
        ]
        for v1, v2, result in cases:
            self.assertEqual(helpers.rpm_cmp(v1, v2), result)

    def test_rpm_max(self):
        cases = [
            (["rc1", "rc2", "rc3"], "rc3"),
            (["pre6", "pre5", "pre4"], "pre6"),
            (["beta8", "beta9", "beta7"], "beta9"),
            (["alpha1", "alpha2", "alpha3"], "alpha3"),
            (["dev6", "dev5", "dev4"], "dev6"),
        ]
        for versions, result in cases:
            self.assertEqual(helpers.rpm_max(versions), result)

    def test_upstream_cmp(self):
        cases = [
            ("1", "2", -1),
            ("2", "1", 1),
            ("1", "1", 0),
            ("1.0", "1.0", 0),
            ("2.0", "1.0", 1),
            ("1.0.a", "1.0", 1),
            ("1.0.a", "1.1", -1),
            ("2.0.rc1", "2.0.pre1", 1),
            ("2.0.beta1", "2.0.pre1", -1),
            ("2.0.beta1", "2.0.alpha1", 1),
            ("1.0.rc1", "1.0.rc2", -1),
            ("1.0.rc3", "1.0.rc2", 1),
            ("2.0.0.rc3", "2.0.0.rc3", 0),
            ("2.0.0.rc1", "2.0.0.rc", 1),
            ("2.0.0.rc", "2.0.0.rc1", -1),
            ("2.0.0.rc", "2.0.0.rc", 0),
            ("3.0.0rc1", "3.0.0", -1),
            ("3.0.0", "3.0.0rc1", 1),
        ]
        for v1, v2, result in cases:
            self.assertEqual(helpers.upstream_cmp(v1, v2), result)

    def test_split_rc(self):
        cases = [
            ("1.0.0.rc1", ("1.0.0", "rc", "1")),
            ("2.3.pre4", ("2.3", "pre", "4")),
            ("4.56.beta7", ("4.56", "beta", "7")),
            ("7.8.90-alpha1", ("7.8.90", "alpha", "1")),
            ("23.4-dev5", ("23.4", "dev", "5")),
            ("1.0.0", ("1.0.0", "", "")),
            ("1.8.23-20100128-r1100", ("1.8.23-20100128-r1100", "", "")),
        ]
        for version, result in cases:
            self.assertEqual(helpers.split_rc(version), result)

    def test_get_rc(self):
        cases = [
            ("0.1.rc2", ("rc", "2")),
            ("0.3.pre4", ("pre", "4")),
            ("0.5.beta6", ("beta", "6")),
            ("0.7.alpha7", ("alpha", "7")),
            ("0.8.dev9", ("dev", "9")),
            ("1.0.rc1", ("", "")),
        ]
        for version, result in cases:
            self.assertEqual(helpers.get_rc(version), result)

    def test_upstream_max(self):
        cases = [
            (["1.0.0", "2.0.0", "3.0.0"], "3.0.0"),
            (["3.0", "2.0", "3.0"], "3.0"),
            (["1.0.0.rc1", "1.0.0.rc2", "1.0.0.rc3"], "1.0.0.rc3"),
            (["1.0.rc1", "1.0.rc2", "1.0"], "1.0"),
        ]
        for versions, result in cases:
            self.assertEqual(helpers.upstream_max(versions), result)

    def test_cmp_upstream_repo(self):
        cases = [
            ("1", ("2", "1"), -1),
            ("2", ("1", "1"), 1),
            ("1", ("1", "1"), 0),
            ("1.0", ("1.0", "1"), 0),
            ("2.0", ("1.0", "1"), 1),
            ("1.0.a", ("1.0", "1"), 1),
            ("1.0.a", ("1.1", "1"), -1),
            ("1.1", ("1.1", "1"), 0),
            ("1.1", ("1.1", "2"), 0),
        ]
        for upstream_v, repo_vr, result in cases:
            self.assertEqual(helpers.cmp_upstream_repo(upstream_v, repo_vr), result)

    def test_filter_dict(self):
        test_dict = {"a": 1, "b": 2, "c": 3, "d": 4}
        self.assertEqual(helpers.filter_dict(test_dict, ["b", "d"]), {"b": 2, "d": 4})

    def test_match_interval(self):
        # Taken directly from helpers
        rc_upstream_regex = re.compile(
            r"(.*?)\.?(-?(rc|pre|beta|alpha|dev)([0-9]*))", re.I
        )

        cases = [
            ("1.0.0.rc1", ("1.0.0", "rc1", "rc", "1")),
            ("2.3.pre4", ("2.3", "pre4", "pre", "4")),
            ("4.56.beta7", ("4.56", "beta7", "beta", "7")),
            ("7.8.90-alpha1", ("7.8.90", "-alpha1", "alpha", "1")),
            ("23.4-dev5", ("23.4", "-dev5", "dev", "5")),
            ("1.0.0", None),
            ("1.8.23-20100128-r1100", None),
        ]
        # Build a test text block
        case_text = []
        result_tuples = []
        for case_line, result in cases:
            case_text.append(case_line)

            if result:
                result_tuples.append(result)

        test_text = "\n".join(
            ["outside", "BEGIN MARKER"] + case_text + ["END MARKER", "outside"]
        )

        test_result = list(
            helpers.match_interval(
                test_text, rc_upstream_regex, "BEGIN MARKER", "END MARKER"
            )
        )

        self.assertEqual(test_result, result_tuples)

        # Test again with no end marker for coverage reasons
        test_text = "\n".join(["outside", "BEGIN MARKER"] + case_text)

        test_result = list(
            helpers.match_interval(
                test_text, rc_upstream_regex, "BEGIN MARKER", "END MARKER"
            )
        )

        self.assertEqual(test_result, result_tuples)

    def test_secure_download(self):
        import pycurl
        import io

        # Required mocks
        mock_curl_instance = Mock()
        mock_stringio_instance = Mock()

        mock_stringio_instance.getvalue.return_value = "mock StringIO value"

        # Expected pycurl setopt calls
        expected_setopt_calls = [
            call(pycurl.URL, b"https://example.com/file.extension"),
            call(pycurl.SSL_VERIFYPEER, 1),
            call(pycurl.SSL_VERIFYHOST, 2),
            call(pycurl.CAINFO, "/etc/certs/cabundle.pem"),
            call(pycurl.WRITEFUNCTION, mock_stringio_instance.write),
            call(pycurl.FOLLOWLOCATION, 1),
            call(pycurl.MAXREDIRS, 10),
        ]

        with patch.object(pycurl, "Curl") as mock_curl_constructor:
            with patch.object(io, "StringIO") as mock_stringio_constructor:
                mock_curl_constructor.return_value = mock_curl_instance
                mock_stringio_constructor.return_value = mock_stringio_instance

                secure_download_result = helpers.secure_download(
                    "https://example.com/file.extension", "/etc/certs/cabundle.pem"
                )

        # Check curl calls
        mock_curl_instance.setopt.assert_has_calls(expected_setopt_calls)
        mock_curl_instance.perform.assert_called_once_with()
        mock_curl_instance.close.assert_called_once_with()

        # Check StringIO call
        mock_stringio_instance.getvalue.assert_called_once_with()

        self.assertEqual(secure_download_result, "mock StringIO value")

    def test_secure_download_no_cainfo(self):
        import pycurl
        import io

        # Required mocks
        mock_curl_instance = Mock()
        mock_stringio_instance = Mock()

        mock_stringio_instance.getvalue.return_value = "mock StringIO value"

        mock_stringio_instance.getvalue.return_value = "mock StringIO value"

        expected_setopt_calls = [
            call(pycurl.URL, b"https://example.com/file.extension"),
            call(pycurl.SSL_VERIFYPEER, 1),
            call(pycurl.SSL_VERIFYHOST, 2),
            call(pycurl.WRITEFUNCTION, mock_stringio_instance.write),
            call(pycurl.FOLLOWLOCATION, 1),
            call(pycurl.MAXREDIRS, 10),
        ]

        with patch.object(pycurl, "Curl") as mock_curl_constructor:
            with patch.object(io, "StringIO") as mock_stringio_constructor:
                mock_curl_constructor.return_value = mock_curl_instance
                mock_stringio_constructor.return_value = mock_stringio_instance

                secure_download_result = helpers.secure_download(
                    "https://example.com/file.extension"
                )

        # Check curl calls
        mock_curl_instance.setopt.assert_has_calls(expected_setopt_calls)
        mock_curl_instance.perform.assert_called_once_with()
        mock_curl_instance.close.assert_called_once_with()

        # Check StringIO call
        mock_stringio_instance.getvalue.assert_called_once_with()

        self.assertEqual(secure_download_result, "mock StringIO value")
