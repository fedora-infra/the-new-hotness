from setuptools import setup

setup(
    name='bugzilla2fedmsg',
    version='0.1.2',
    description='Consume BZ messages over STOMP and republish to fedmsg',
    license='LGPLv2+',
    author='Ralph Bean',
    author_email='rbean@redhat.com',
    url='https://github.com/fedora-infra/bugzilla2fedmsg',
    install_requires=[
        "fedmsg",
        "python-bugzilla",
        "moksha.hub",
        "stomper",
    ],
    packages=[],
    py_modules=['bugzilla2fedmsg'],
    entry_points="""
    [moksha.consumer]
    bugzilla2fedmsg = bugzilla2fedmsg:BugzillaConsumer
    """,
)
