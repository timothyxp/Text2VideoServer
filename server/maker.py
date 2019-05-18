from server.app import app

from flask import request, abort

from config.configuration import Config

from data.ImageInterval import ImageInterval
from data.VideoInterval import VideoInterval

from utils.load_json import load_json

from utils.conf import *

import json

from utils.image_download import load_image

def checkImageInterval(interval):
    if not 'href' in interval:
        return 'Link to image cannot be empty'
    if not 'begin' in interval:
        return 'Begin field cannot be empty'
    if not 'end' in interval:
        return 'End field cannot be empty'
    if not 'text' in interval:
        return 'Text cannot be empty'
    return None

def checkVideoInterval(interval):
    if not 'href' in interval:
        return 'Link to image cannot be empty'

    if not 'begin' in interval:
        return 'Begin field cannot be empty'
    if not 'end' in interval:
        return 'End field cannot be empty'
    
    if not 'video_begin' in interval:
        return 'Video_begin field cannot be empty'
    if not 'video_end' in interval:
        return 'Video_end field cannot be empty'

    if not 'text' in interval:
        return 'Text cannot be empty'
    return None

@app.route('/make', methods=['POST'])
def make():
    if not request.json:
        return abort(400)

    if DEMO:
        data = json.loads(load_json("beta/make_top.json"))
    else:
        data = request.get_json()
    print(data)

    with open("make_req.json", 'w') as out:
        out.write(json.dumps(data))
    
    config = Config()

    intervals = data['intervals']

    ints = []
    error = None

    for interval in intervals:
        if interval['type'] == 'video':
            error = checkVideoInterval(interval)
            if error != None:
                break
            video_src = "downloaded/" + config.downloader.download(interval['href']) + ".mp4"
            print(video_src)
            ints.append(VideoInterval(interval['begin'], interval['end'], interval['text'], video_src, interval['video_begin'], interval['video_end']))
        elif interval['type'] == 'image':
            error = checkVideoInterval(interval)
            if error != None:
                break
            image_src = load_image(interval['href'])
            print(image_src)
            ints.append(ImageInterval(interval['begin'], interval['end'], interval['text'], image_src))

    if error == None:
        res_file = config.maker.make(ints, "none", icon="downloaded/new_icon.png", overlay="downloaded/overlay.png")
        return json.dumps({
            'type': 'ok',
            'url': res_file
        })
    else:
        return json.dumps({
            'type': 'error', 
            'error': str(error)
        })
