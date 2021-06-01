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
import re

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest


class RPM:
    """
    This class contains various helpful methods for working with RPM packages.
    """

    @classmethod
    def compare(cls, version1: str, version2: str) -> int:
        """
        Compare method for comparing two RPM versions.

        Params:
            version1: First RPM version
            version2: Second RPM version

        Returns:
            1 if version1 is newer than version2
            0 if version1 is equal to version2
            -1 if version1 is older than version2
        """
        v1, rc1, rcn1 = cls._split_rc(version1)
        v2, rc2, rcn2 = cls._split_rc(version2)

        diff = cls._compare_rpm_labels((None, v1, None), (None, v2, None))
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

    __rc_upstream_regex = re.compile(
        r"(.*?)\.?(-?(rc|pre|beta|alpha|dev)([0-9]*))", re.I
    )

    @classmethod
    def _split_rc(cls, version: str) -> tuple:
        """Split version into version and release candidate string +
        release candidate number if possible

        Params:
            version: Version to split

        Returns:
            Tuple containing version, release candidate string and release candidate number
        """
        match = cls.__rc_upstream_regex.match(version)
        if not match:
            return (version, "", "")

        rc_str = match.group(3)
        v = match.group(1)
        rc_num = match.group(4)
        return (v, rc_str, rc_num)

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
    _subfield_pattern = re.compile(
        r"(?P<junk>[^a-zA-Z0-9]*)((?P<text>[a-zA-Z]+)|(?P<num>[0-9]+))"
    )

    @classmethod
    def _iter_rpm_subfields(cls, field):
        """Yield subfields as 2-tuples that sort in the desired order

        Text subfields are yielded as (0, text_value)
        Numeric subfields are yielded as (1, int_value)
        """
        for subfield in cls._subfield_pattern.finditer(field):
            text = subfield.group("text")
            if text is not None:
                yield (0, text)
            else:
                yield (1, int(subfield.group("num")))

    @classmethod
    def _compare_rpm_field(cls, lhs, rhs):
        # Short circuit for exact matches (including both being None)
        if lhs == rhs:
            return 0
        # Otherwise assume both inputs are strings
        lhs_subfields = cls._iter_rpm_subfields(lhs)
        rhs_subfields = cls._iter_rpm_subfields(rhs)
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

    @classmethod
    def _compare_rpm_labels(cls, lhs, rhs):
        lhs_epoch, lhs_version, lhs_release = lhs
        rhs_epoch, rhs_version, rhs_release = rhs
        result = cls._compare_rpm_field(lhs_epoch, rhs_epoch)
        if result:
            return result
        result = cls._compare_rpm_field(lhs_version, rhs_version)
        if result:
            return result
        return cls._compare_rpm_field(lhs_release, rhs_release)
