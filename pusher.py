import sys

from twisted.internet import reactor
from twisted.python import log
import json

from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol, \
    connectWS

class PusherProtocol(WebSocketClientProtocol):
    def onOpen(self):
        self.factory.singleton = self

    def onClose(self, wasClean, code, reason):
        self.factory.singleton = None

    def onMessage(self, payload, binary=False):
        try:
            payload = json.loads(payload)
        except ValueError:
            print("Cannot parse: {}".format(payload))

        channel = payload.get("channel")
        event = payload.get("event")
        data = payload.get("data")

        if not event:
            raise Exception("Invalid Pusher payload: {}".format(payload))

        if channel:
            self.factory.pusher._emit_channel(**payload)
        else:
            self.factory.pusher._emit(**payload)

class Channel:
    def __init__(self, pusher, name):
        self.pusher = pusher
        self.name = name
        self.subscribed = False
        self.handler = None

    def on_event(self, handler):
        self.handler = handler

    def _emit(self, channel, event, data):
        if callable(self.handler):
            self.handler(channel, event, data)

class Pusher:
    def __init__(self, app_key):
        self.app_key = app_key
        self.events = {}
        self.channels = {}
        self.factory = WebSocketClientFactory("ws://ws.pusherapp.com:80/app/%s?client=python-twisted?version=1.0&protocol=4" % app_key)
        self.factory.protocol = PusherProtocol
        self.factory.singleton = None
        self.factory.pusher = self
        connectWS(self.factory)

    def on_subscription_succeded(self, data):
        channel = self.channels.setdefault(name, Channel(self, name))
        channel.subscribed = True

    def on_ping(self, data):
        self.send("pusher:pong")

    def subscribe(self, name, auth=None, channel_data=None):
        channel = self.channels.setdefault(name, Channel(self, name))
        payload = {"channel":name}
        if auth:
            payload["auth"] = auth
        if channel_data:
            payload["channel_data"] = channel_data
        self.send("pusher:subscribe", payload)
        return channel

    def unsubscribe(self, name):
        channel = self.channels.setdefault(name, Channel(self, name))
        self.send("pusher:unsubscribe", {"channel":name})
        channel.subscribed = False

    def _emit_channel(self, channel, event, data):
        channel = self.channels.get(channel)
        if channel:
            channel._emit(channel, event, data)

    def _emit(self, event, data):
        handler = self.events.get(event)
        if callable(handler):
            handler(event, data)

    def on(self, event, method):
        self.events[event] = method

    def send(self, event, data=None):
        if not self.factory.singleton:
            raise Exception("Not connected.")
        if not data:
            data = {}
        payload = {"event":event, "data":data}
        self.factory.singleton.sendMessage(json.dumps(payload), False)

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    pusher = Pusher(sys.argv[1])
    def foo(event, data):
        channel = pusher.subscribe("channel_name")

        def bar(channel, event, data):
            print "data:", data

        channel.on_event(bar)
    pusher.on("pusher:connection_established", foo)
    reactor.run()

