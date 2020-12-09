import json
import logging
import signal
import time

from collections import defaultdict
from urllib.parse import urlparse
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from redis import Redis
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, parse_command_line, options
from tornado.web import Application, RequestHandler, HTTPError
from tornado.websocket import WebSocketHandler, WebSocketClosedError
from tornadoredis import Client
from tornadoredis.pubsub import BaseSubscriber

define("debug", default=False, type=bool, help='Run in debug mode')
define('port', default=8080, type=int, help='Server port')
define('allowed_hosts', default='localhost:8080', multiple=True,
        help='Allowed hosts for cross domain connections')


class RedisSubscriber(BaseSubscriber):

    def on_message(self, msg):
        if msg and msg.kind == 'message':
            try:
                message = json.load(msg.body)
                sender = message['sender']
                message = message['message']
            except (ValueError, KeyError):
                message = msg.body
                sender = None
                subscribers = list(self.subscribers[msg.channel].keys())
                for subscriber in subscribers:
                    try:
                        subscriber.write_message(msg.body)
                    except WebSocketClosedError:
                        self.unsubscribe(msg.channel, subscriber)
        super().on_message(msg)

class SprintHandler(WebSocketHandler):
    """ Handles real-time updates to the board """

    def check_origin(self, origin):
        allowed = super().check_origin(origin)
        parsed = urlparse(origin.lower())
        matched = any(parsed.netloc == host for host in options.allowed_hosts)
        return options.debug or allowed or matched

    def open(self):
        self.sprint = None
        channel = self.get_argument('channel', None)
        if not channel:
            self.close()
        else:
            try:
                self.sprint = self.application.signer.unsign(channel, max_age=60*30)
            except (BadSignature, SignatureExpired):
                self.close()
            else:
            self.uid = uuid.uuid4().hex
            self.application.add_subscriber(self.sprint, self)

    def on_message(self, message):
        if self.sprint is not None:
            self.application.broadcast(message, channel=self.sprint, sender=self)

    def on_close(self):
        if self.sprint is not None:
            self.application.remove_subscriber(self.sprint, self)


class ScrumApplication(Application):
    
    def __init__(self, **kwargs):
        routes = [
            (r'/(?P<sprint>[0-9]+)', SprintHandler),
            (r'/(?P<model>task|sprint|user)/(?<pk>[0-9]+)', UpdateHandler)
        ]
        super().__init__(routes, **kwargs)
        self.subscriber = RedisSubscriber(Client())
        self.publisher = Redis()
        self._key = os.environ.get('WATERCOOLER_SECRET', 'pTyz1dzMeVUGrb0Su4QXsP984qTlvQRHpFnnlHuHs')
        self.signer = TimestampSigner(self._key)
        # self.subscriptions = defaultdict(list)

    def add_subscriber(self, channel, subscriber):
        # self.subscriptions[channel].append(subscriber)
        self.subscriber.subscribe(['all', channel], subscriber)

    def remove_subscriber(self, channel, subscriber):
        # self.subscriptions[channel].remove(subscriber)
        self.subscriber.unsubscribe(channel, subscriber)
        self.subscriber.unsubscribe('all', subscriber)

    def get_subscribers(self, channel):
        return self.subscriptions[channel]

    def broadcast(self, message, channel=None, sender=None):
        # if channel is None:
        #     for c in self.subscriptions.keys():
        #         self.broadcast(message, channel=c, sender=sender)
        # else:
        #     peers = self.get_subscribers(channel)
        #     for peer in peers:
        #         if peer != sender:
        #             try:
        #                 peer.write_message(message)
        #             except WebSocketClosedError:
        #                 self.remove_subscriber(channel, peer)
        channel = 'all' if channel is None else channel
        message = json.dumps({
            'sender': sender and sender.uid,
            'message': message
        })
        self.publisher.publish(channel, message)


class UpdateHandler(RequestHandler):
    
    def post(self, model, pk):
        self._broadcast(model, pk, 'add')

    def put(self, model, pk):
        self._broadcast(model, pk, 'put')

    def delete(self, model, pk):
        self._broadcast(model, pk, 'remove')

    def _broadcast(self, model, pk, action):
        sinature = self.request.headers.get('X-Signature', None)
        if not signature:
            raise HTTPError(400)
        try:
            result = self.request.signer.unsign(signature, max_age=60)
        except (BadSignature, SignatureExpired):
            raise HTTPError(400)
        else: 
            expected = '{method}:{url}:{body}'.format(
                method=self.request.method.lower(),
                url=self.request.full_url(),
                body=hashlib.sha256(self.request.body).hexadigest()
            )
            if not constant_time_compare(result, expected):
                raise HTTPError(400)
        try:
            body = json.load(self.request.body.decode('utf-8'))
        except ValueError:
            body = None
        message = json.dumps({
            'model': model,
            'id': pk,
            'action': action,
            'body': body
        })
        self.application.broadcast(message)
        self.write('ok')

def shutdown(server):
    ioloop = IOLoop.instance()
    logging.info('Sotpping server.')
    server.stop()

    def finalize():
        ioloop.stop()
        logging.info('Stopped.')

    ioloop.add_timeout(time.time() + 1.5, finalize)

if __name__ == '__main__':
    parse_command_line()
    application = ScrumApplication(debug=options.debug)
    server = HTTPServer(application)
    server.listen(options.port)
    signal.signal(signal.SIGINT, lambda sig, frame: shutdown(server))
    logging.info('Starting server on localhost:{}'.format(options.port))
    IOLoop.instance().start()