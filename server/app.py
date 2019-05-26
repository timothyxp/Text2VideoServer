# This Python file uses the following encoding: utf-8

from flask import Flask, request
from flask_socketio import SocketIO

app = Flask("__app__", static_folder='tmp', static_url_path='')
socketio = SocketIO(app)

working_status = {}

from server import main_handler
from server import maker
from server import search

def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept"
    response.headers['Access-Control-Allow-Methods'] = "DELETE, GET, POST, PUT, OPTIONS"
    # if request.method == 'OPTIONS':
        # response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT, OPTIONS'
        # headers = request.headers.get('Access-Control-Request-Headers')
        # if headers:
        #     response.headers['Access-Control-Allow-Headers'] = headers
    return response


app.after_request(add_cors_headers)