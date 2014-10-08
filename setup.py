from setuptools import setup

setup(
    name='the-new-hotness',
    version='0.1.0',
    description='Consume anitya fedmsg messages to file bugzilla bugs'
    license='LGPLv2+',
    author='Ralph Bean',
    author_email='rbean@redhat.com',
    url='https://github.com/fedora-infra/the-new-hotness',
    install_requires=[
        "fedmsg",
        "python-bugzilla",
    ],
    packages=[],
    py_modules=['the_new_hotness'],
    entry_points="""
    [moksha.consumer]
    bug_filer = the_new_hotness:BugzillaTicketFiler
    """,
)
