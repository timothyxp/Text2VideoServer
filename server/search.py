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

    for key in data:
        print(key)
        print(data[key])

    data = data["text"]

    data = config.analyzer.analyze(data)

    videos = []

    for video in data['videos']:
        token = config.downloader.download(video)

        video_path = path.join(DOWNLOAD_PATH, token)

        videos.append(video_path)

    data.videos = videos

    return json.dumps(data)

