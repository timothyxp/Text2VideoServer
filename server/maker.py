from server.app import app

from flask import request, abort

from config.configuration import Config

from data.ImageInterval import ImageInterval
from data.VideoInterval import VideoInterval

import json

@app.route('/make', methods=['POST'])
def make():
    if not request.json:
        return abort(400)
    data = request.get_json()
    
    intervals = data['intervals']

    ints = []

    for interval in intervals:
        if interval.type == 'video':
            ints.append(VideoInterval(interval['begin'], interval['end'], interval['text'], interval['href'], interval['video_begin'], interval['video_end']))
        elif interval.type == 'image':
            ints.append(ImageInterval(interval['begin'], interval['end'], interval['text'], interval['href']))

    print(ints)

    return json.dumps({
        'type': 'ok',
        'url': '/clip.mp4'
    })
