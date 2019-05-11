from flask import Flask

app = Flask("__app__")

from server import main_handler
from server import maker