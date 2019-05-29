import json
import threading
import time

import numpy as np
from flask import request, abort
from flask_socketio import emit

from config.configuration import config
from data.ImageInterval import ImageInterval
from data.VideoInterval import VideoInterval
from server.app import app, socketio, working_status
from utils.conf import *
from utils.image_download import load_image
from utils.logging.logger import logger


def make_error(error):
    return json.dumps({
        'type': 'error',
        'error': str(error)
    })


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
            logger.warning("Unknown fps format" + data['fps'])

    if 'width' in data:
        try:
            width = int(data['width'])
            result['width'] = width
        except:
            logger.warning("Unknown width format" + data['width'])

    if 'height' in data:
        try:
            height = int(data['height'])
            if height in [240, 360, 720, 1080]:
                result['height'] = height
            else:
                logger.warning("Unknown height format" + data['height'])
        except:
            logger.warning("Unknown height format" + data['height'])

    if 'textSize' in data:
        try:
            textSize = int(data['textSize'])
            result['textSize'] = textSize
        except:
            logger.warning("Unknown text size format" + data['textSize'])

    if 'textMode' in data:
        try:
            textMode = str(data['textMode'])
            if textMode in ['LEFT', 'RIGHT', 'CENTER']:
                result['textMode'] = textMode
            else:
                logger.warning("Unknown text mode format" + data['textMode'])
        except:
            logger.warning("Unknown text mode format" + data['textMode'])

    if 'shadowEnabled' in data:
        try:
            shadowEnabled = str(data['shadowEnabled'])
            if shadowEnabled == "True":
                result['shadowEnabled'] = True
            elif shadowEnabled == "False":
                result['shadowEnabled'] = False
            else:
                logger.warning("Unknown shadow enabled format" + data['shadowEnabled'])
        except:
            logger.warning("Unknown shadow enabled format" + data['shadowEnabled'])

    return result


def set_ready_status(current_id, res_file):
    if current_id == None:
        return
    working_status[current_id]['status'] = 'ready'
    working_status[current_id]['url'] = res_file


def set_process_status(current_id, message):
    if current_id == None:
        return
    working_status[current_id]['status'] = 'process'
    working_status[current_id]['message'] = message


def set_error_status(current_id, error):
    if current_id == None:
        return
    working_status[current_id]['status'] = 'error'
    working_status[current_id]['error'] = error


def make_video(data, current_id=None):
    with open("make_req.json", 'w') as out:
        out.write(json.dumps(data))

    ints = []
    error = None

    video_config = load_config(data)
    logger.debug(video_config)
    set_process_status(current_id, "Инициализация")

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
            logger.debug(interval)
            if not 'type' in interval:
                error = 'For one or more intervals type is not specified'
                break
            if interval['type'] == 'video':
                error = checkVideoInterval(interval)
                if error != None:
                    break
                video_loaded = config.downloader.download(
                    interval['href'], video_config)
                if video_loaded == None:
                    error = "Sorry but we cannot download one or more of videos you selected"
                    break
                video_src = video_loaded
                logger.debug(video_src)
                ints.append(VideoInterval(
                    interval['begin'], interval['end'], interval['text'], video_src, interval['video_begin'], interval['video_end']))
            elif interval['type'] == 'image':
                error = checkImageInterval(interval)
                if error != None:
                    break
                image_src = load_image(interval['href'])
                logger.debug(image_src)
                ints.append(ImageInterval(
                    interval['begin'], interval['end'], interval['text'], image_src))
            index += 1
            set_process_status(
                current_id, "Загружено: {:d}/{:d}".format(index, len(intervals)))
        set_process_status(current_id, "Все видео успешно загружены")
        download_finish = time.time()
        download_time = download_finish - download_start

    if error == None:
        making_time = 0
        make_begin = time.time()
        res_file = config.maker.make(ints, "none", video_config, current_id=current_id,
                                     set_process_status=set_process_status, icon=None, overlay=None)
        make_end = time.time()
        making_time = make_end - make_begin
        logger.info("Download time: {:.2f}, making time: {:.2f}".format(
            download_time, making_time))
        if current_id != None:
            set_ready_status(current_id, res_file)
        return json.dumps({
            'type': 'ok',
            'url': res_file
        })
    else:
        if current_id != None:
            set_error_status(current_id, str(error))
        return json.dumps({
            'type': 'error',
            'error': str(error)
        })


def random_string():
    ans = ''
    for i in range(0, 20):
        ans += chr(ord('a') + np.random.randint(0, 25))
    return ans


@app.route('/make', methods=['POST'])
def make():
    if not request.json:
        return abort(400)
    data = request.get_json()
    logger.debug(data)
    return make_video(data)


def proceed(current_id):
    working_status[current_id]['status'] = 'process'
    working_status[current_id]['message'] = 'Starting'
    make_video(working_status[current_id]['data'], current_id)


@app.route('/status', methods=['POST'])
def get_status():
    if not request.json:
        return abort(400)
    data = request.get_json()
    logger.debug(data)
    if not 'id' in data:
        return make_error("Id not found")
    current_id = data['id']
    logger.debug(current_id)
    logger.debug(working_status)
    if not current_id in working_status:
        return make_error("Unknown id: {:s}".format(current_id))
    if working_status[current_id]['status'] == 'process':
        return json.dumps({
            'status': 'process',
            'message': working_status[current_id]['message']
        })
    elif working_status[current_id]['status'] == 'error':
        return json.dumps({
            'status': 'error',
            'error': working_status[current_id]['error']
        })
    elif working_status[current_id]['status'] == 'ready':
        return json.dumps({
            'status': 'ready',
            'url': working_status[current_id]['url']
        })
    else:
        logger.debug(working_status[current_id])


@app.route('/make_queue', methods=['POST'])
def make_queued():
    if not request.json:
        return abort(400)
    data = request.get_json()
    logger.debug(data)
    working_id = random_string()
    # return make_video(data)
    working_status[working_id] = {
        'data': data,
        'status': 'NOT STARTED'
    }
    threading.Thread(target=proceed, args=(working_id,)).start()
    return json.dumps({
        'type': 'ok',
        'id': working_id
    })


@socketio.on('make')
def make_socket_io(data):
    logger.debug(data)
    with open("make_req_socket.json", 'w') as out:
        out.write(json.dumps(data))

    ints = []
    error = None

    video_config = load_config(data)
    logger.debug(video_config)

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
            logger.debug(interval)
            if not 'type' in interval:
                error = 'For one or more intervals type is not specified'
                break
            if interval['type'] == 'video':
                error = checkVideoInterval(interval)
                if error != None:
                    break
                video_loaded = config.downloader.download(
                    interval['href'], video_config)
                if video_loaded == None:
                    error = "Sorry but we cannot download one or more of videos you selected"
                    break
                video_src = video_loaded
                logger.debug(video_src)
                ints.append(VideoInterval(
                    interval['begin'], interval['end'], interval['text'], video_src, interval['video_begin'], interval['video_end']))
            elif interval['type'] == 'image':
                error = checkImageInterval(interval)
                if error != None:
                    break
                image_src = load_image(interval['href'])
                logger.debug(image_src)
                ints.append(ImageInterval(
                    interval['begin'], interval['end'], interval['text'], image_src))
            index += 1
            emit(
                "message", "Downloaded: {:d}/{:d}".format(index, len(intervals)))
        download_finish = time.time()
        download_time = download_finish - download_start

    if error is None:
        making_time = 0
        make_begin = time.time()
        emit("message", "Making your video")
        res_file = config.maker.make(
            ints, "none", video_config, icon=None, overlay=None)
        make_end = time.time()
        making_time = make_end - make_begin
        logger.info("Download time: {:.2f}, making time: {:.2f}".format(
            download_time, making_time))
        logger.debug(res_file)
        try:
            emit("video_make_result", json.dumps({
                'type': 'ok',
                'url': res_file
            }))
        except Exception as error:
            logger.error(error)
    else:
        emit("video_make_result", json.dumps({
            'type': 'error',
            'error': str(error)
        }))
