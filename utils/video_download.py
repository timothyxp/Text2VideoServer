from abc import ABC, abstractmethod
import pytube

import os
from os import path

from config import DOWNLOAD_PATH
from utils.logging.logger import logger

import json


class VideoDownloadBase(ABC):
    @abstractmethod
    def download(self, href, config):
        pass


class VideoDownload(VideoDownloadBase):
    def __init__(self):
        self.errored = {}
        if os.path.exists('error_cache.txt'):
            with open('error_cache.txt', 'r') as inp:
                data = str(inp.read())
                self.errored = json.loads(data)

    def __save_cache__(self):
        logger.debug('Saving cache')
        with open('error_cache.txt', 'w') as out:
            out.write(json.dumps(self.errored))

    def download(self, href, config):
        token = href.split('=')[1]

        file_name = token + '-' + str(config['height'])
        file_path = DOWNLOAD_PATH + "/" + file_name + ".mp4"

        if path.exists(file_path):
            logger.debug('Already exists')
            return file_path

        if href in self.errored:
            logger.warning('Was errored before ' + href)
            return None
        else:
            logger.debug('Wasn\'t errored')

        logger.info('Searching for quality')

        # try:
        yt = pytube.YouTube(href)
        logger.debug("YT object created")
        video_filter = yt.streams\
            .filter(subtype='mp4') \
            .filter(progressive=False)
        logger.debug("video_filter created")
        quality = 0
        for video in video_filter.all():
            resolution = video.resolution
            logger.debug(f"get {video.url}")

            if resolution is not None:
                resolution = int(video.resolution.replace('p', ''))
                if resolution <= config['height'] and resolution >= quality:
                    quality = resolution
        video_filter = video_filter.filter(resolution=str(quality) + "p")
        video = video_filter.first()

        logger.info("Quality: " + str(quality) + "p")

        if video is None:
            self.errored[href] = True
            self.__save_cache__()
            return None

        logger.info(f"Downloading {file_path}")

        video.download(
            DOWNLOAD_PATH,
            filename=file_name
        )

        return file_path
        # except Exception as error:
        #     logger.error('Error handled ' + str(error))
        #     self.errored[href] = True
        #     self.__save_cache__()
        #     return None
