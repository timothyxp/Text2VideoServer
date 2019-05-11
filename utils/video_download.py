from abc import ABC, abstractmethod
import pytube

from os import path

from config import DOWNLOAD_PATH


class VideoDownloadBase(ABC):
    @abstractmethod
    def download(self, href):
        pass


class VideoDownload(VideoDownloadBase):
    def download(self, href):
        yt = pytube.YouTube(href)

        video = yt.streams\
            .filter(subtype='mp4') \
            .filter(progressive=False) \
            .filter(resolution='720p') \
            .first()

        token = href.split('=')[1]

        subtype = video.subtype

        file_path = path.join(DOWNLOAD_PATH, token) + '.' + subtype

        if path.exists(file_path):
            return token

        video.download(
            DOWNLOAD_PATH,
            filename=token
        )

        return token
