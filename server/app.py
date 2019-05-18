# This Python file uses the following encoding: utf-8

from flask import Flask, request

app = Flask("__app__", static_folder='tmp', static_url_path='')

from server import main_handler
from server import maker
from server import search


def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    if request.method == 'OPTIONS':
        response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT, OPTIONS'
        headers = request.headers.get('Access-Control-Request-Headers')
        if headers:
            response.headers['Access-Control-Allow-Headers'] = headers
    return response


app.after_request(add_cors_headers)