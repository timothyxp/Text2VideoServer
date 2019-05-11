from server.app import app

from flask import request, abort

from config.configuration import Config

from config import DOWNLOAD_PATH

from os import path

import json

@app.route('/search', methods=["POST"])
def search():
    if not request.json:
        return abort(400)

    data = request.get_json()

    config = Config()

    data = data["text"]
    data = config.analyzer.analyze(data)
    videos = []

    bad_videos = {}

    for video in data['videos']:
        token = config.downloader.download(video)
        if token == None:
            bad_videos[video] = True
            continue
        video_path = path.join(DOWNLOAD_PATH, token)
        videos.append(video_path)

    print(data)
    for sentence in data['data']:
        print(sentence)
        buffer = []
        for elem in data['data'][sentence]:
            print(elem, end = ' ')
            if elem['type'] == 'video':
                if not elem['href'] in bad_videos:
                    buffer.append(elem)
                else:
                    print("Found bad video:", elem)
            else:
                buffer.append(elem)
        print()
        data['data'][sentence] = buffer

    return json.dumps(data)

