from flask_socketio import Namespace, emit, join_room, leave_room
import random
from flask import request

class GameRoomSpace(Namespace):
    def __init__(self, *args, **kwargs):
        super(GameRoomSpace, self).__init__(*args, **kwargs)

        self.main_room = Room()

    def on_connect(self):
        self.enter_room(request.sid, self.main_room.room_id)

    def on_disconnect(self):
        self.leave_room(request.sid, self.main_room.room_id)

    def on_error(self):
        pass

class Room:
    def __init__(self):
        self.inner_room_id: str = '%030x'.format(random.randrange(16**30))

    @property
    def room_id(self) -> str:
        return self.inner_room_id
