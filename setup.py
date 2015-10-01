from setuptools import setup, find_packages

setup(
    name='the-new-hotness',
    version='0.6.2',
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
        "fedmsg_meta_fedora_infrastructure",
    ],
    packages=find_packages(),
    entry_points="""
    [moksha.consumer]
    bug_filer = hotness.consumers:BugzillaTicketFiler
    """,
)
