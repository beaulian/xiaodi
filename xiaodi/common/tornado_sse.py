# coding=utf-8

from tornado import gen
from tornado import websocket
from xiaodi.settings import REDIS_EVENT_DB, REDIS_CHANNEL
from xiaodi.common.redis_client import get_aredis_client, call


class SSEHandler(websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        self._client = get_aredis_client(REDIS_EVENT_DB)

        super(SSEHandler, self).__init__(*args, **kwargs)
        self.listen()

    @gen.coroutine
    def listen(self):
        yield call(self._client.subscribe, REDIS_CHANNEL)

        self._client.listen(self.on_message)

    def on_message(self, msg):
        if msg.kind == 'message':
            self.write_message(str(msg.body))
        if msg.kind == 'disconnect':
            # Do not try to reconnect, just send a message back
            # to the client and close the client connection
            self.write_message('The connection terminated '
                               'due to a Redis server error.')
            self.close()

    def on_close(self):
        if self._client.subscribed:
            self._client.unsubscribe(REDIS_CHANNEL)
            self._client.disconnect()
