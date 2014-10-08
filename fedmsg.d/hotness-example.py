import socket
hostname = socket.gethostname().split('.', 1)[0]

config = {
    'hotness.bugzilla.enabled': True,

    # TODO - you need to fill these out
    #'bugzilla.username': None
    #'bugzilla.password': None
    'bugzilla.url': 'https://partner-bugzilla.redhat.com',

    "endpoints": {
        # You need as many of these as you have worker threads.
        'hotness.%s' % hostname: [
            'tcp://127.0.0.1:3032',
            'tcp://127.0.0.1:3033',
            'tcp://127.0.0.1:3034',
            'tcp://127.0.0.1:3035',
        ],
    },
}
