# This file is part of anitya and was originally a part of cnucnu.
#
# the-new-hotness is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# the-new-hotness is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with the-new-hotness.  If not, see <http://www.gnu.org/licenses/>.
""" :author: Till Maas
    :contact: opensource@till.name
    :license: GPLv2+
"""

import fnmatch
import functools
import re
import pprint as pprint_module

# The rpm version comparison is copied from
# https://github.com/fedora-infra/anitya/blob/master/anitya/lib/versions/rpm.py
try:
    from rpm import labelCompare as _compare_rpm_labels
except ImportError:
    # Emulate RPM field comparisons as described in
    # https://stackoverflow.com/a/3206477
    #
    # * Search each string for alphabetic fields [a-zA-Z]+ and
    #   numeric fields [0-9]+ separated by junk [^a-zA-Z0-9]*.
    # * Successive fields in each string are compared to each other.
    # * Alphabetic sections are compared lexicographically, and the
    #   numeric sections are compared numerically.
    # * In the case of a mismatch where one field is numeric and one is
    #   alphabetic, the numeric field is always considered greater (newer).
    # * In the case where one string runs out of fields, the other is always
    #   considered greater (newer).

    import warnings

    warnings.warn("Failed to import 'rpm', emulating RPM label comparisons")

    try:
        from itertools import zip_longest
    except ImportError:
        from itertools import izip_longest as zip_longest

    _subfield_pattern = re.compile(
        r"(?P<junk>[^a-zA-Z0-9]*)((?P<text>[a-zA-Z]+)|(?P<num>[0-9]+))"
    )

    def _iter_rpm_subfields(field):
        """Yield subfields as 2-tuples that sort in the desired order

        Text subfields are yielded as (0, text_value)
        Numeric subfields are yielded as (1, int_value)
        """
        for subfield in _subfield_pattern.finditer(field):
            text = subfield.group("text")
            if text is not None:
                yield (0, text)
            else:
                yield (1, int(subfield.group("num")))

    def _compare_rpm_field(lhs, rhs):
        # Short circuit for exact matches (including both being None)
        if lhs == rhs:
            return 0
        # Otherwise assume both inputs are strings
        lhs_subfields = _iter_rpm_subfields(lhs)
        rhs_subfields = _iter_rpm_subfields(rhs)
        for lhs_sf, rhs_sf in zip_longest(lhs_subfields, rhs_subfields):
            if lhs_sf == rhs_sf:
                # When both subfields are the same, move to next subfield
                continue
            if lhs_sf is None:
                # Fewer subfields in LHS, so it's less than/older than RHS
                return -1
            if rhs_sf is None:
                # More subfields in LHS, so it's greater than/newer than RHS
                return 1
            # Found a differing subfield, so it determines the relative order
            return -1 if lhs_sf < rhs_sf else 1
        # No relevant differences found between LHS and RHS
        return 0

    def _compare_rpm_labels(lhs, rhs):
        lhs_epoch, lhs_version, lhs_release = lhs
        rhs_epoch, rhs_version, rhs_release = rhs
        result = _compare_rpm_field(lhs_epoch, rhs_epoch)
        if result:
            return result
        result = _compare_rpm_field(lhs_version, rhs_version)
        if result:
            return result
        return _compare_rpm_field(lhs_release, rhs_release)


__docformat__ = "restructuredtext"

pp = pprint_module.PrettyPrinter(indent=4)
pprint = pp.pprint

__html_regex = re.compile(r'\bhref\s*=\s*["\']([^"\'/]+)/["\']', re.I)
__text_regex = re.compile(r"^d.+\s(\S+)\s*$", re.I | re.M)


def expand_subdirs(url, glob_char="*"):
    """Expand dirs containing glob_char in the given URL with the latest
    Example URL: http://www.example.com/foo/*/

    The globbing char can be bundled with other characters enclosed within
    the same slashes in the URL like "/rel*/".
    """
    glob_pattern = "/([^/]*%s[^/]*)/" % re.escape(glob_char)
    glob_match = re.search(glob_pattern, url)
    if not glob_match:
        return url
    glob_str = glob_match.group(1)

    # url until first slash before glob_match
    url_prefix = url[0 : glob_match.start() + 1]

    # everything after the slash after glob_match
    url_suffix = url[glob_match.end() :]

    dir_listing = get_html(url_prefix)
    if not dir_listing:
        return url
    subdirs = []
    regex = url.startswith("ftp://") and __text_regex or __html_regex
    for match in regex.finditer(dir_listing):
        subdir = match.group(1)
        if subdir not in (".", "..") and fnmatch.fnmatch(subdir, glob_str):
            subdirs.append(subdir)
    if not subdirs:
        return url
    latest = upstream_max(subdirs)

    url = "%s%s/%s" % (url_prefix, latest, url_suffix)
    return expand_subdirs(url, glob_char)


def get_html(url, callback=None, errback=None):
    if url.startswith("ftp://"):
        import urllib

        req = urllib.request.urlopen(url)  # nosec
        data = req.read()
        if callback:
            try:
                for cb in callback:
                    cb(data)
            except TypeError:
                callback(data)
        return data
    else:
        if callback:
            from twisted.web.client import getPage

            df = getPage(url)
            try:
                for cb in callback:
                    df.addCallback(cb)
            except TypeError:
                df.addCallback(callback)

            if errback:
                try:
                    for eb in errback:
                        df.addErrback(eb)
                except TypeError:
                    df.addErrback(errback)
        else:
            import io
            import pycurl

            res = io.StringIO()

            c = pycurl.Curl()
            c.setopt(pycurl.URL, url.encode("ascii"))

            c.setopt(pycurl.WRITEFUNCTION, res.write)
            c.setopt(pycurl.FOLLOWLOCATION, 1)
            c.setopt(pycurl.MAXREDIRS, 10)
            c.setopt(
                pycurl.USERAGENT,
                "Fedora Upstream Release Monitoring "
                "(https://fedoraproject.org/wiki/Upstream_release_monitoring)",
            )
            c.setopt(pycurl.CONNECTTIMEOUT, 10)
            c.setopt(pycurl.TIMEOUT, 30)

            c.perform()
            c.close()

            data = res.getvalue()
            res.close()
            return data


def rpm_cmp(v1, v2):
    diff = _compare_rpm_labels((None, v1, None), (None, v2, None))
    return diff


def rpm_max(list):
    list.sort(key=functools.cmp_to_key(rpm_cmp))
    return list[-1]


def upstream_cmp(v1, v2):
    """Compare two upstream versions

    :Parameters:
        v1 : str
            Upstream version string 1
        v2 : str
            Upstream version string 2

    :return:
        - -1 - second version newer
        - 0  - both are the same
        - 1  - first version newer

    :rtype: int

    """

    v1, rc1, rcn1 = split_rc(v1)
    v2, rc2, rcn2 = split_rc(v2)

    diff = rpm_cmp(v1, v2)
    if diff != 0:
        # base versions are different, ignore rc-status
        return diff

    if rc1 and rc2:
        # rc > pre > beta > alpha
        if rc1.lower() > rc2.lower():
            return 1
        elif rc1.lower() < rc2.lower():
            return -1

        # both are same rc, higher rc is newer
        if rcn1 and rcn2:
            if int(rcn1) > int(rcn2):
                return 1
            elif int(rcn1) < int(rcn2):
                return -1
        elif rcn1:
            return 1
        elif rcn2:
            return -1

        # both rc numbers are missing or same
        return 0

    if rc1:
        # only first is rc, then second is newer
        return -1
    if rc2:
        # only second is rc, then first is newer
        return 1

    # neither is a rc
    return 0


__rc_upstream_regex = re.compile(r"(.*?)\.?(-?(rc|pre|beta|alpha|dev)([0-9]*))", re.I)
__rc_release_regex = re.compile(r"0\.[0-9]+\.(rc|pre|beta|alpha|dev)([0-9]*)", re.I)


def split_rc(version):
    """Split (upstream) version into version and release candidate string +
    release candidate number if possible
    """
    match = __rc_upstream_regex.match(version)
    if not match:
        return (version, "", "")

    rc_str = match.group(3)
    v = match.group(1)
    rc_num = match.group(4)
    return (v, rc_str, rc_num)


def get_rc(release):
    """Get the rc value of a package's release"""
    match = __rc_release_regex.match(release)

    if match:
        return (match.group(1), match.group(2))
    else:
        return ("", "")


def upstream_max(list):
    list.sort(key=functools.cmp_to_key(upstream_cmp))
    return list[-1]


def cmp_upstream_repo(upstream_v, repo_vr):
    repo_rc = get_rc(repo_vr[1])

    repo_version = "%s%s%s" % (repo_vr[0], repo_rc[0], repo_rc[1])

    # Strip a leading 'v' which is sometimes prefixed to github releases
    # https://github.com/fedora-infra/anitya/issues/102
    upstream_v = upstream_v.lstrip("v")

    return upstream_cmp(upstream_v, repo_version)


def filter_dict(d, key_list):
    """return a dict that only contains keys that are in key_list"""
    return dict([v for v in d.items() if v[0] in key_list])


def secure_download(url, cainfo=""):
    import pycurl
    import io

    c = pycurl.Curl()
    c.setopt(pycurl.URL, url.encode("ascii"))

    # -k / --insecure
    # c.setopt(pycurl.SSL_VERIFYPEER, 0)

    # Verify certificate
    c.setopt(pycurl.SSL_VERIFYPEER, 1)

    # Verify CommonName or Subject Alternate Name
    c.setopt(pycurl.SSL_VERIFYHOST, 2)

    # --cacert
    if cainfo:
        c.setopt(pycurl.CAINFO, cainfo)

    res = io.StringIO()

    c.setopt(pycurl.WRITEFUNCTION, res.write)

    # follow up to 10 http location: headers
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.MAXREDIRS, 10)

    c.perform()
    c.close()
    data = res.getvalue()
    res.close()

    return data


def match_interval(text, regex, begin_marker, end_marker):
    """returns a list of match.groups() for all lines after a line
    like begin_marker and before a line like end_marker
    """

    inside = False
    for line in text.splitlines():
        if not inside:
            if line == begin_marker:
                inside = True
        else:
            match = regex.match(line)
            if match:
                yield match.groups()
            elif line == end_marker:
                inside = False
                break
