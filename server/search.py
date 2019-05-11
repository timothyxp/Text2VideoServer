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

    data = Config.analyzer.analyze(data.text)

    videos = []

    for video in data.videos:
        token = Config.downloader.download(video)

        path = path.join(DOWNLOAD_PATH, token)

        videos.append(path)

    data.videos = videos

    return json.dumps(data)

