from abc import ABC, abstractmethod
import pytube

import os
from os import path

from config import DOWNLOAD_PATH

import json


class VideoDownloadBase(ABC):
    @abstractmethod
    def download(self, href):
        pass


class VideoDownload(VideoDownloadBase):
    def __init__(self):
        self.errored = {}
        if os.path.exists('error_cache.txt'):
            with open('error_cache.txt', 'r') as inp:
                data = str(inp.read())
                self.errored = json.loads(data)

    def __save_cache__(self):
        print('Saving cache')
        with open('error_cache.txt', 'w') as out:
            out.write(json.dumps(self.errored))

    def download(self, href):
        print(self.errored)
        
        token = href.split('=')[1]

        file_path = path.join(DOWNLOAD_PATH, token) + '.mp4'

        if path.exists(file_path):
            print('Already exists')
            return token

        if href in self.errored:
            print('Was errored before', href)
            return None
        else:
            print('Wasn\'t errored')

        try:
            yt = pytube.YouTube(href)

            video = yt.streams\
                .filter(subtype='mp4') \
                .filter(progressive=False) \
                .filter(resolution='720p') \
                .first()

            if video == None:
                self.errored[href] = True
                self.__save_cache__()
                return None
            subtype = video.subtype

            print('Downloading')

            video.download(
                DOWNLOAD_PATH,
                filename=token
            )

            return token
        except:
            print('Error handled')
            self.errored[href] = True
            self.__save_cache__()
            return None
