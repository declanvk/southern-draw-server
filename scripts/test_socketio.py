import logging
from socketIO_client import SocketIO, BaseNamespace

class TestNamespace(BaseNamespace):

    def on_aaa_response(self, *args):
        print('on_aaa_response', args)
        self.emit('bbb')

socketIO = SocketIO('127.0.0.1', 8000)

test_namespace = socketIO.define(TestNamespace, '/games')
test_namespace.emit('aaa')

socketIO.wait(seconds=1)
