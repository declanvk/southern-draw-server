import logging
from socketIO_client import SocketIO, BaseNamespace

class TestNamespace(BaseNamespace):

    def on_message_response(self, *args):
        print('on_aaa_response', args)
        self.emit('bbb')

    def on_room_number(self, *args):
        print(*args)

socketIO = SocketIO('127.0.0.1', 8000)

test_namespace = socketIO.define(TestNamespace, '/game')
test_namespace.emit('message')

socketIO.wait(seconds=5)
