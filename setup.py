from setuptools import setup, find_packages
import re


def get_version():
    """Get the current version of the hotness package"""
    with open('hotness/__init__.py', 'r') as fd:
        regex = r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]'
        version = re.search(regex, fd.read(), re.MULTILINE).group(1)
    if not version:
        raise RuntimeError('No version set in hotness/__init__.py')
    return version


setup(
    name='the-new-hotness',
    version=get_version(),
    description='Consume anitya fedmsg messages to file bugzilla bugs',
    license='LGPLv2+',
    author='Ralph Bean',
    author_email='rbean@redhat.com',
    url='https://github.com/fedora-infra/the-new-hotness',
    install_requires=[
        "fedmsg",
        "python-bugzilla",
        "dogpile.cache",
        "requests",
        "sh",
        "six",
        "fedmsg_meta_fedora_infrastructure",
    ],
    packages=find_packages(),
    entry_points="""
    [moksha.consumer]
    bug_filer = hotness.consumers:BugzillaTicketFiler
    """,
    test_suite='tests',
)
