from flask import Flask, send_from_directory
from flask_socketio import SocketIO
from os import getenv
from pathlib import Path

WEBSITE_STATIC = getenv("SOUTHERN_STATIC_FOLDER", default='static/')

app = Flask(__name__)
app.config['STATIC_FOLDER'] = Path(WEBSITE_STATIC)
app.config['SECRET_KEY'] = 'this is a big fat secret! don\'t tell anyone'
socketio = SocketIO(app)

@app.route('/')
def main_page():
    return send_from_directory(app.config['STATIC_FOLDER'], 'index.html')

@app.route('/<path:subpath>')
def static_content(subpath):
    return send_from_directory(app.config['STATIC_FOLDER'], subpath)

if __name__ == '__main__':
    socketio.run(app)
