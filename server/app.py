# This Python file uses the following encoding: utf-8

from flask import Flask

app = Flask("__app__", static_folder='tmp', static_url_path='')

from server import main_handler
from server import maker
from server import search