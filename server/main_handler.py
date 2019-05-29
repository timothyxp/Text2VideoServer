from server.app import app, working_status
import json
from flask import send_file


def last_videos():
    return json.dumps(working_status)


@app.route('/last', methods=['GET'])
def last_route():
    return last_videos()


@app.route('/')
def main_route():
    return send_file('tmp/index.html')
