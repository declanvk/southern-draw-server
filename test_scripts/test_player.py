import logging
import json
import sys
import numpy as np
from socketIO_client import SocketIO, BaseNamespace

class PlayerNamespace(BaseNamespace):

    def on_room_number(self, *args):
        print(*args)

if (len(sys.argv) == 2):
    print('Include lounge number as argument')

socketIO = SocketIO('127.0.0.1', 8000)

player = socketIO.define(PlayerNamespace, '/game/player')
player.emit('join_room', {
    'room_number': sys.argv[1],
    'user_name': 'Declan Kelley'
})

t = np.linspace(10, 100, 100)
x = t * np.sin(t/10)
y = t * np.cos(t/10)

points = map(lambda x: {'x': x[0], 'y': x[1]}, zip(x, y))

draw_data = {
    'pkt_name': 'draw_data_ios_move',
    'color': 'red',
    'points': points
}

end_line_data = {
    'pkt_name': 'draw_data_ios_end_line'
}

socketIO.wait()
