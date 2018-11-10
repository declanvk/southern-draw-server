from flask import request
from flask_socketio import Namespace, emit, join_room, leave_room

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class WebNamespace(Namespace):

    def __init__(self, *args, **kwargs):
        super(WebNamespace, self).__init__(*args, **{key: kwargs[key] for key in kwargs if key != 'parent'})

        if 'parent' not in kwargs:
            raise ValueError("'parent' keyword not found in namespace init")

        self.parent = kwargs['parent']

    def on_connect(self):
        self.parent.register_web_connect(request.sid)

    def on_disconnect(self):
        self.parent.register_web_disconnect(request.sid)

    def send_new_room(self, conn_id, room_number):
        self.emit('new_room', { 'pkt_type': 'new_room', 'room_number': room_number }, room=conn_id)

    def send_all_players(self, conn_id, players):
        self.emit('all_players', { 'pkt_type': 'all_players', 'players': players}, room=conn_id)

    def send_start_game(self, conn_id, prompt_player_pairs):
        self.emit('start_game', { 'pkt_type': 'start_game', 'prompts': prompt_player_pairs }, room=conn_id)

    def send_draw_data(self, conn_id, user_name, screen_dim, lines):
        self.emit('draw_data_web', {
            'pkt_type': 'draw_data_web',
            'user_name': user_name,
            'screen_dim': screen_dim,
            'lines': lines
        }, room=conn_id)

class PlayerNamespace(Namespace):

    def __init__(self, *args, **kwargs):
        super(PlayerNamespace, self).__init__(*args, **{key: kwargs[key] for key in kwargs if key != 'parent'})

        if 'parent' not in kwargs:
            raise ValueError("'parent' keyword not found in namespace init")

        self.parent = kwargs['parent']

    def on_connect(self):
        logger.info("Player {} connected.".format(request.sid))
        print("Player", request.sid, "connecting")
        self.parent.register_player_connect(request.sid)

    def on_disconnect(self):
        logger.info("Player {} disconnected.".format(request.sid))
        print("Player", request.sid, "disconnecting")
        room_id = self.parent.register_player_disconnect(request.sid)

        if room_id is not None:
            leave_room(request.sid, room_id)

    def on_join_room(self, data):
        room_number = data['room_number']
        user_name = data['user_name']
        screen_dim = data['screen_dim']

        logger.info("Player {} request to join room {}.".format(request.sid, room_number))

        room_id = self.parent.join_room_message(request.sid, room_number, user_name, screen_dim)

        if room_id is not None:
            join_room(request.sid, room_id)

    def on_draw_data_ios_move(self, data):
        color = data['color']
        points = data['points']
        screen_dim = data['screen_dim']

        self.parent.draw_data_message(request.sid, points, screen_dim, color)

    def on_draw_data_ios_end_line(self, data):
        self.parent.draw_data_end_line_message(request.sid)

    def send_join_room_status(self, player_id, status):
        self.emit('join_room_status', status, room=player_id)

    def send_state_game(self, room_id, prompt_player_pairs):
        self.emit('start_game', { 'pkt_type': 'start_game', 'prompts': prompt_player_pairs }, room=room_id)
