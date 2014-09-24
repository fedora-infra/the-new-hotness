import socket
hostname = socket.gethostname().split('.', 1)[0]

config = {
    "endpoints": {
        # You need as many of these as you have worker threads.
        'bugzilla.%s' % hostname: [
            'tcp://127.0.0.1:3032',
            'tcp://127.0.0.1:3033',
            'tcp://127.0.0.1:3034',
            'tcp://127.0.0.1:3035',
        ],
    },
}
