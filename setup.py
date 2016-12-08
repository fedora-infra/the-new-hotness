# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


def get_requirements(requirements_file='requirements.txt'):
    """Get the contents of a file listing the requirements.

    :arg requirements_file: path to a requirements file
    :type requirements_file: string
    :returns: the list of requirements, or an empty list if
              `requirements_file` could not be opened or read
    :return type: list
    """

    lines = open(requirements_file).readlines()
    return [
        line.rstrip().split('#')[0]
        for line in lines
        if not line.startswith('#')
    ]


setup(
    name='the-new-hotness',
    version='0.7.3',
    description='Consume anitya fedmsg messages to file bugzilla bugs',
    license='LGPLv2+',
    author='Ralph Bean',
    author_email='rbean@redhat.com',
    url='https://github.com/fedora-infra/the-new-hotness',
    install_requires=get_requirements(),
    tests_require=get_requirements('dev-requirements.txt'),
    packages=find_packages(),
    entry_points="""
    [moksha.consumer]
    bug_filer = hotness.consumers:BugzillaTicketFiler
    """,
    test_suite='tests',
)
