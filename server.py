from flask import Flask, send_from_directory
from flask_socketio import SocketIO
from os import getenv
from pathlib import Path
from room import GameRoomSpace, Room

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

# handle all game messages
socketio.on_namespace(GameRoomSpace('/games'))

if __name__ == '__main__':
    socketio.run(app)
