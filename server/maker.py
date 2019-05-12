from server.app import app

from flask import request, abort

from config.configuration import Config

from data.ImageInterval import ImageInterval
from data.VideoInterval import VideoInterval

from utils.load_json import load_json

from utils.conf import *

import json

from utils.image_download import load_image

@app.route('/make', methods=['POST'])
def make():
    if not request.json:
        return abort(400)

    if DEMO:
        data = json.loads(load_json("beta/make.json"))
    else:
        data = request.get_json()
    
    config = Config()

    intervals = data['intervals']

    ints = []

    for interval in intervals:
        if interval['type'] == 'video':
            video_src = "downloaded/" + config.downloader.download(interval['href']) + ".mp4"
            print(video_src)
            ints.append(VideoInterval(interval['begin'], interval['end'], interval['text'], video_src, interval['video_begin'], interval['video_end']))
        elif interval['type'] == 'image':
            image_src = load_image(interval['href'])
            print(image_src)
            ints.append(ImageInterval(interval['begin'], interval['end'], interval['text'], image_src))

    res_file = config.maker.make(ints, "none", icon="downloaded/new_icon.png", overlay="downloaded/overlay.png")

    return json.dumps({
        'type': 'ok',
        'url': res_file
    })
