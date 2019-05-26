from server.app import app, working_status
import json

import maker

def last_videos():
    return json.dumps(working_status)

@app.route('/last', methods=['GET'])
def last_route():
    return last_videos()

@app.route('/')
def main_route():
    return 'Hello'
