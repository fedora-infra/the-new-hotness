import socket
hostname = socket.gethostname().split('.', 1)[0]

config = {
    "endpoints": {
        'bugzilla.%s' % hostname: ['tcp:127.0.0.1:3032'],
    },
}
