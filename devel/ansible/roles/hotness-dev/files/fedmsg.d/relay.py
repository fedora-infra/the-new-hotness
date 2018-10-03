config = dict(
    endpoints={
        # This is the output side of the relay to which the-new-hotness
        # can listen (where the-new-hotness is running as a part of 'fedmsg-hub')
        "relay_outbound": ["tcp://127.0.0.1:4001"]
    },
    # This is the input side of the relay to which 'fedmsg-logger' and
    # 'fedmsg-dg-replay' will send messages. It will just repeat those
    # messages out the 'relay_outbound' endpoint on your own box.
    relay_inbound=["tcp://127.0.0.1:2003"],
)
