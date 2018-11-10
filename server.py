from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, Namespace, emit, join_room, leave_room
from os import getenv
from pathlib import Path
import random
import logging

# create logger with '__name__'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
app.config['STATIC_FOLDER'] = Path(getenv("SOUTHERN_STATIC_FOLDER", default='static/'))
app.config['SECRET_KEY'] = 'this is a big fat secret! don\'t tell anyone'
socketio = SocketIO(app)

# Handle first page
@app.route('/')
def main_page():
    return send_from_directory(app.config['STATIC_FOLDER'], 'index.html')

# Handle all static resources
@app.route('/<path:subpath>')
def static_content(subpath):
    return send_from_directory(app.config['STATIC_FOLDER'], subpath)

class WebNamespace(Namespace):

    def __init__(self, *args, **kwargs):
        super(WebNamespace, self).__init__(*args, **{key: kwargs[key] for key in kwargs if key != 'parent'})

        if 'parent' not in kwargs:
            raise ValueError("'parent' keyword not found in namespace init")

        self.parent = kwargs['parent']

    def on_connect(self):
        logger.info('Web interface {} connected'.format(request.sid))
        self.parent.register_web_connect(request.sid)

    def on_disconnect(self):
        logger.info('Web interface {} disconnected'.format(request.sid))
        self.parent.register_web_disconnect(request.sid)

    def send_new_room(self, conn_id, room_number):
        self.emit('new_room', { 'pkt_type': 'new_room', 'room_number': room_number }, room=conn_id)

    def send_all_players(self, conn_id, players):
        self.emit('all_players', { 'pkt_type': 'all_players', 'players': players}, room=conn_id)

    def send_start_game(self, conn_id, prompt_player_pairs):
        self.emit('start_game', { 'pkt_type': 'start_game', 'prompts': prompt_player_pairs }, room=conn_id)

    def send_draw_data(self, conn_id, user_name, lines):
        self.emit('draw_data_web', { 'pkt_type': 'draw_data_web', 'user_name': user_name, 'lines': lines }, room=conn_id)

class PlayerNamespace(Namespace):

    def __init__(self, *args, **kwargs):
        super(PlayerNamespace, self).__init__(*args, **{key: kwargs[key] for key in kwargs if key != 'parent'})

        if 'parent' not in kwargs:
            raise ValueError("'parent' keyword not found in namespace init")

        self.parent = kwargs['parent']

    def on_connect(self):
        logger.info('Player {} connected'.format(request.sid))
        self.parent.register_player_connect(request.sid)

    def on_disconnect(self):
        logger.info('Player {} disconnected'.format(request.sid))
        room_id = self.parent.register_player_disconnect(request.sid)

        if room_id is not None:
            leave_room(request.sid, room_id)

    def on_join_room(self, data):
        room_number = data['room_number']
        user_name = data['user_name']

        room_id = self.parent.join_room_message(request.sid, room_number, user_name)

        if room_id is not None:
            join_room(request.sid, room_id)

    def on_draw_data_ios_move(self, data):
        color = data['color']
        points = data['points']
        screen_dim = data['screen_dim']

        self.parent.draw_data_message(request.sid, points, screen_dim, color)

    def send_join_room_status(self, player_id, status):
        self.emit('join_room_status', status, room=player_id)

    def send_state_game(self, room_id, prompt_player_pairs):
        self.emit('start_game', { 'pkt_type': 'start_game', 'prompts': prompt_player_pairs }, room=room_id)

class Server:
    def __init__(self, web_namespace_class, player_namespace_class):
        self.web_namespace_class = web_namespace_class
        self.player_namespace_class = player_namespace_class

        # Map player connection ids to all player data
        self.players = {}
        # Map lounge id to all lounge data
        self.lounges = {}
        # Map web connection id to all web data
        self.web_connections = {}

    def register(self, socket_io):
        self.socket_io = socket_io
        self.web_namespace = self.web_namespace_class('/game/web', parent=self)
        self.player_namespace = self.player_namespace_class('/game/player', parent=self)

        socket_io.on_namespace(self.web_namespace)
        socket_io.on_namespace(self.player_namespace)

    def register_player_connect(self, player_id):
        # Create a new player object
        self.players[player_id] = {
            'player_id': player_id,
            'user_name': None,
            'lounge_id': None
        }

    def register_player_disconnect(self, player_id):
        lounge_id = self.players[player_id]['lounge_id']
        del self.players[player_id]

        # Check if the lounge exists
        if lounge_id is not None and lounge_id in self.lounges:
            lounge = self.lounges[lounge_id]

            # If it does, remove the disconnecting player
            lounge['player_client'].remove(player_id)

            # Attempt to delete the lounge
            self.try_lounge_cleanup(lounge, lounge_id)

            return lounge_id
        else:
            return None

    def register_web_connect(self, web_id):
        lounge_id = self.generate_lounge_id()

        # Create web connection object
        self.web_connections[web_id] = {
            'web_id': web_id,
            'lounge_id': lounge_id
        }

        # Create loung connection
        self.lounges[lounge_id] = {
            'lounge_id': lounge_id,
            'player_clients': [],
            'web_client': web_id,
        }

        # Tell web connection that they belong to the specified lounge
        self.web_namespace.send_new_room(web_id, lounge_id)

    def register_web_disconnect(self, web_id):
        lounge_id = self.web_connections[web_id]['lounge_id']
        # Delete leaving web object
        del self.web_connections[web_id]

        # Check if lounge object exists
        if lounge_id is not None and lounge_id in self.lounges:
            lounge = self.lounges[lounge_id]

            # If it does, delete the web client from it
            lounge['web_client'] = None

            # Try to delete the lounge if it is empty
            self.try_lounge_cleanup(lounge, lounge_id)

    def join_room_message(self, player_id, room_number, user_name):
        player = self.players[player_id]

        # If the lounge exists
        if room_number in self.lounges:
            lounge = self.lounges[room_number]

            # Add the player to the lounge and give them a user name
            lounge['player_clients'].append(player_id)
            player['lounge_id'] = room_number
            player['user_name'] = user_name

            # Then generate the list of current players in the lounge and send it to the front end
            current_players = [ { 'user_name': self.players[in_game_player_id]['user_name']} \
                        for in_game_player_id in lounge['player_clients'] ]
            self.web_namespace.send_all_players(lounge['web_client'], current_players)

            return room_number
        else:
            return None

    def draw_data_message(self, player_id, points, screen_dim, color):
        pass

    def try_cleanup_lounge(self, lounge, lounge_id):
        if lounge['player_client'] is not None and \
               len(lounge['player_client']) == 0 and \
               lounge['web_client'] is None:
               del self.lounges[lounge_id]

    def generate_lounge_id(self):
        return "{:030x}".format(random.randrange(16**30))

server = Server(WebNamespace, PlayerNamespace)
server.register(socketio)

if __name__ == '__main__':
    socketio.run(app)
