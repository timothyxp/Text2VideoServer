from server.app import app, socketio

from flask import request, abort

from config.configuration import config

from data.ImageInterval import ImageInterval
from data.VideoInterval import VideoInterval

from flask_socketio import send, emit

from utils.load_json import load_json

from utils.conf import *

import json

import time

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

def load_config(data):
    result = {
        'fps': VIDEO_FPS,
        'width': IMAGE_WIDTH,
        'height': IMAGE_HEIGHT,
        'textSize': TEXT_SIZE,
        'textMode': TEXT_MODE,
        'shadowSize': SHADOW_SIZE,
        'iconSize': ICON_SIZE,
        'iconMargin': ICON_MARGIN,
        'letterWidth': LETTER_WIDTH,
        'shadowEnabled': SHADOW_ENABLED
    }

    if 'fps' in data:
        try:
            fps = int(data['fps'])
            result['fps'] = fps
        except:
            print("Unknown fps format", data['fps'])
    
    if 'width' in data:
        try:
            width = int(data['width'])
            result['width'] = width
        except:
            print("Unknown width format", data['width'])

    if 'height' in data:
        try:
            height = int(data['height'])
            if height in [240 , 360, 720, 1080]:
                result['height'] = height
            else:
                print("Unknown height format", data['height'])
        except:
            print("Unknown height format", data['height'])

    if 'textSize' in data:
        try:
            textSize = int(data['textSize'])
            result['textSize'] = textSize
        except:
            print("Unknown text size format", data['textSize'])
    
    if 'textMode' in data:
        try:
            textMode = str(data['textMode'])
            if textMode in ['LEFT', 'RIGHT', 'CENTER']:
                result['textMode'] = textMode
            else:
                print("Unknown text mode format", data['textMode'])
        except:
            print("Unknown text mode format", data['textMode'])

    if 'shadowEnabled' in data:
        try:
            shadowEnabled = str(data['shadowEnabled'])
            if shadowEnabled == "True":
                result['shadowEnabled'] = True
            elif shadowEnabled == "False":
                result['shadowEnabled'] = False
            else:
                print("Unknown shadow enabled format", data['shadowEnabled'])
        except:
            print("Unknown shadow enabled format", data['shadowEnabled'])
    
    return result

def make_video(data):
    with open("make_req.json", 'w') as out:
        out.write(json.dumps(data))

    ints = []
    error = None

    video_config = load_config(data)
    print(video_config)

    download_time = 0
    download_start = 0
    download_finish = 0

    if not 'intervals' in data:
        error = "Unknown request format"
    else:
        download_start = time.time()
        intervals = data['intervals']
        for interval in intervals:
            print(interval)
            if not 'type' in interval:
                error = 'For one or more intervals type is not specified'
                break
            if interval['type'] == 'video':
                error = checkVideoInterval(interval)
                if error != None:
                    break
                video_loaded = config.downloader.download(interval['href'], video_config)
                if video_loaded == None:
                    error = "Sorry but we cannot download one or more of videos you selected"
                    break
                video_src =video_loaded
                print(video_src)
                ints.append(VideoInterval(interval['begin'], interval['end'], interval['text'], video_src, interval['video_begin'], interval['video_end']))
            elif interval['type'] == 'image':
                error = checkImageInterval(interval)
                if error != None:
                    break
                image_src = load_image(interval['href'])
                print(image_src)
                ints.append(ImageInterval(interval['begin'], interval['end'], interval['text'], image_src))
        download_finish = time.time()
        download_time = download_finish - download_start

    if error == None:
        making_time = 0
        make_begin = time.time()
        res_file = config.maker.make(ints, "none", video_config, icon=None, overlay=None)
        make_end = time.time()
        making_time = make_end - make_begin
        print("Download time: {:.2f}, making time: {:.2f}".format(download_time, making_time))
        return json.dumps({
            'type': 'ok',
            'url': res_file
        })
    else:
        return json.dumps({
            'type': 'error', 
            'error': str(error)
        })

@app.route('/make', methods=['POST'])
def make():
    if not request.json:
        return abort(400)
    if DEMO:
        data = json.loads(load_json("beta/make_top.json"))
    else:
        data = request.get_json()
    print(data)
    return make_video(data)

@socketio.on('make')
def make_socket_io(data):
    print(data)
    with open("make_req_socket.json", 'w') as out:
        out.write(json.dumps(data))

    ints = []
    error = None

    video_config = load_config(data)
    print(video_config)

    emit("message", "Configured successfully")

    download_time = 0
    download_start = 0
    download_finish = 0

    if not 'intervals' in data:
        error = "Unknown request format"
    else:
        download_start = time.time()
        intervals = data['intervals']
        index = 0
        for interval in intervals:
            print(interval)
            if not 'type' in interval:
                error = 'For one or more intervals type is not specified'
                break
            if interval['type'] == 'video':
                error = checkVideoInterval(interval)
                if error != None:
                    break
                video_loaded = config.downloader.download(interval['href'], video_config)
                if video_loaded == None:
                    error = "Sorry but we cannot download one or more of videos you selected"
                    break
                video_src =video_loaded
                print(video_src)
                ints.append(VideoInterval(interval['begin'], interval['end'], interval['text'], video_src, interval['video_begin'], interval['video_end']))
            elif interval['type'] == 'image':
                error = checkImageInterval(interval)
                if error != None:
                    break
                image_src = load_image(interval['href'])
                print(image_src)
                ints.append(ImageInterval(interval['begin'], interval['end'], interval['text'], image_src))
            index += 1
            emit("message", "Downloaded: {:d}/{:d}".format(index, len(intervals)))
        download_finish = time.time()
        download_time = download_finish - download_start

    if error == None:
        making_time = 0
        make_begin = time.time()
        emit("message", "Making your video")
        res_file = config.maker.make(ints, "none", video_config, icon=None, overlay=None)
        make_end = time.time()
        making_time = make_end - make_begin
        print("Download time: {:.2f}, making time: {:.2f}".format(download_time, making_time))
        print(res_file)
        try:
            emit("video_make_result", json.dumps({
                'type': 'ok',
                'url': res_file
            })) 
        except Exception as error:
            print(error)
    else:
        emit("video_make_result", json.dumps({
            'type': 'error', 
            'error': str(error)
        }))