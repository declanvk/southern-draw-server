from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, Namespace, emit, join_room, leave_room
from os import getenv
from pathlib import Path
import logging
from namespaces import WebNamespace, PlayerNamespace
from threading import Timer
from prompts import get_prompt
from string import ascii_lowercase
from random import choice

IDENTIFIER_LEN = 6
TIMER_LEN = 15
FUDGE_TIME = 2
PLAYERS_PER_ROOM = 1
WEB_ENDPOINT = '/game/web'
PLAYER_ENDPOINT = '/game/player'

# create logger with '__name__'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

STATIC_FOLDER = getenv("SOUTHERN_STATIC_FOLDER", default='static')

app = Flask(__name__, static_folder=STATIC_FOLDER)
app.config['STATIC_FOLDER'] = Path(STATIC_FOLDER)
app.config['SECRET_KEY'] = 'this is a big fat secret! don\'t tell anyone'
socketio = SocketIO(app, logger=logger)

# Handle first page
@app.route('/')
def main_page():
    return send_from_directory(app.config['STATIC_FOLDER'], 'index.html')

# Handle all static resources
@app.route('/<path:subpath>')
def static_content(subpath):
    return send_from_directory(app.config['STATIC_FOLDER'], subpath)

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
        self.web_namespace = self.web_namespace_class(WEB_ENDPOINT, parent=self)
        self.player_namespace = self.player_namespace_class(PLAYER_ENDPOINT, parent=self)

        socket_io.on_namespace(self.web_namespace)
        socket_io.on_namespace(self.player_namespace)

    def register_player_connect(self, player_id):
        # Create a new player object
        self.players[player_id] = {
            'player_id': player_id,
            'user_name': None,
            'lounge_id': None,
            'screen_dim': None
        }

    def register_player_disconnect(self, player_id):
        lounge_id = self.players[player_id]['lounge_id']
        del self.players[player_id]

        # Check if the lounge exists
        if lounge_id is not None and lounge_id in self.lounges:
            lounge = self.lounges[lounge_id]

            # If it does, remove the disconnecting player
            lounge['player_clients'].remove(player_id)

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
            'player_lines': {},
            "game_state": "starting" # possible states: "starting", "running", "complete"
        }

        print("New lounge {}".format(lounge_id))

        # player_lines schema
        # {
        #     "<player_id>": {
        #         "lines": [
        #             { "color": "...", "points": [ { "x": "x value", "y": "y value" } ] }
        #         ],
        #         "last_active": "<bool>"
        #     }
        # }

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

    def join_room_message(self, player_id, room_number, user_name, screen_dim):
        player = self.players[player_id]

        # If the lounge exists
        if room_number in self.lounges:
            lounge = self.lounges[room_number]

            # Add the player to the lounge and give them a user name
            lounge['player_clients'].append(player_id)
            lounge['player_lines'][player_id] = {
                'lines': [],
                'last_active': False
            }

            player['lounge_id'] = room_number
            player['user_name'] = user_name
            player['screen_dim'] = screen_dim

            # Then generate the list of current players in the lounge and send it to the front end
            current_players = [ { 'user_name': self.players[in_game_player_id]['user_name']} \
                        for in_game_player_id in lounge['player_clients'] ]
            self.web_namespace.send_all_players(lounge['web_client'], current_players)

            self.player_namespace.send_join_room_status(player_id, 'ok')

            if len(lounge['player_clients']) == PLAYERS_PER_ROOM:
                # Start game
                lounge['game_state'] = 'running'

                # Tell the web client the usernames of the players
                user_names = [self.players[player_id]['user_name'] for player_id in lounge['player_clients']]
                self.web_namespace.send_start_game(lounge['web_client'], user_names)

                # Tell each player their prompt
                for player_id in lounge['player_clients']:
                    prompt = get_prompt()
                    self.player_namespace.send_start_game(player_id, prompt)

                def on_game_end():
                    lounge['game_state'] = 'complete'
                    print("Game of {} has ended".format(lounge['player_clients']))

                t = Timer(TIMER_LEN + FUDGE_TIME, on_game_end)

                t.start()

            return room_number
        else:
            self.player_namespace.send_join_room_status(player_id, 'not ok')
            return None

    def draw_data_message(self, player_id, points, color):
        player = self.players[player_id]
        user_name = player['user_name']

        if player['lounge_id'] is not None and player['lounge_id'] in self.lounges:
            lounge = self.lounges[player['lounge_id']]

            web_client_id = lounge['web_client']

            player_lines = lounge['player_lines'][player_id]

            if player_lines['last_active']:
                player_lines['lines'][-1]['points'].append(points)
            else:
                player_lines['lines'].append({
                    'points': points,
                    'color': color
                })

            # Send complete updated picture for originating player to web connection
            self.send_web_complete_picture(lounge, player_id, web_client_id)

    def draw_data_end_line_message(self, player_id):
        player = self.players[player_id]

        if player['lounge_id'] is not None:
            lounge = self.lounges[player['lounge_id']]

            player_lines = lounge['player_lines'][player_id]
            player_lines['last_active'] = False


    def send_web_complete_picture(self, lounge, player_id, web_id):
        player_lines = lounge['player_lines'][player_id]
        player = self.players[player_id]

        screen_dim = player['screen_dim']
        user_name = player['user_name']
        self.web_namespace.send_draw_data(web_id, user_name,
                                          screen_dim, player_lines['lines'])

    def try_lounge_cleanup(self, lounge, lounge_id):
        if lounge.get('player_clients') is not None and \
               len(lounge['player_clients']) == 0 and \
               lounge['web_client'] is None:
               del self.lounges[lounge_id]

    def generate_lounge_id(self):
        return ''.join(choice(ascii_lowercase, k=IDENTIFIER_LEN))

server = Server(WebNamespace, PlayerNamespace)
server.register(socketio)

if __name__ == '__main__':
    socketio.run(app)
