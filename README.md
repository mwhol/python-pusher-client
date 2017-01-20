https://github.com/ysobolev/python-pusher-client

# python-pusher-client
Autobahn backed python pusher client

## Usage:
    import sys
    from twisted.internet import reactor
    from twisted.python import log

    from pusher_client import PusherClient
    bitstamp = PusherClient("de504dc5763aeef9ff52")
    
    def run(event, data):
        def on_data(channel, event, data):
            print(data)

        channel = bitstamp.subscribe("order_book")
        channel.bind("data", on_data)

    bitstamp.on("pusher:connection_established", run)

    log.startLogging(sys.stdout)
    reactor.run()

