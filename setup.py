# -*- coding: utf-8 -*-

import os
import re

from setuptools import find_packages, setup


ON_READ_THE_DOCS = os.environ.get("READTHEDOCS") == "True"


def get_version():
    """Get the current version of the hotness package"""
    with open("hotness/__init__.py", "r") as fd:
        regex = r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]'
        version = re.search(regex, fd.read(), re.MULTILINE).group(1)
    if not version:
        raise RuntimeError("No version set in hotness/__init__.py")
    return version


def get_requirements(requirements_file="requirements.txt"):
    """Get the contents of a file listing the requirements.

    :arg requirements_file: path to a requirements file
    :type requirements_file: string
    :returns: the list of requirements, or an empty list if
              `requirements_file` could not be opened or read
    :return type: list
    """

    if ON_READ_THE_DOCS:
        # These packages are not needed to build on Read the Docs
        ignored_packages = ["koji", "pycurl"]
    else:
        ignored_packages = []

    lines = [
        line.rstrip().split("#")[0] for line in open(requirements_file).readlines()
    ]

    packages = []
    for line in lines:
        if line.startswith("#"):
            continue
        if any(line.startswith(package) for package in ignored_packages):
            continue
        packages.append(line)

    return packages


setup(
    name="the-new-hotness",
    version=get_version(),
    description="Consume anitya fedora messaging messages to file bugzilla bugs",
    license="LGPLv2+",
    author="Ralph Bean",
    author_email="rbean@redhat.com",
    url="https://github.com/fedora-infra/the-new-hotness",
    install_requires=get_requirements(),
    tests_require=get_requirements("dev-requirements.txt"),
    packages=find_packages(exclude=("hotness.tests", "hotness.tests.*")),
    test_suite="hotness.tests",
    python_requires=">=3.6",
)
