from server.app import app
import json

import maker

def last_videos():
    return json.dumps(maker.working_status)

@app.route('/last', methods=['GET'])
def last_route():
    return last_videos()

@app.route('/')
def main_route():
    return 'Hello'
