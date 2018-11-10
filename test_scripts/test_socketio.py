import logging
import json
from socketIO_client import SocketIO, BaseNamespace

class PlayerNamespace(BaseNamespace):

    def on_room_number(self, *args):
        print(*args)

class WebNamespace(BaseNamespace):

    def on_new_room(self, data):
        player = socketIO.define(PlayerNamespace, '/game/player')
        player.emit('join_room', {
            'room_number': data['room_number'],
            'user_name': 'Declan Kelley',
            'screen_dim': {'width': 800, 'height': 600}
        })

socketIO = SocketIO('127.0.0.1', 8000)

web = socketIO.define(WebNamespace, '/game/web')

socketIO.wait()
