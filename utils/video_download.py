from abc import ABC, abstractmethod
import pytube

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

        video.download(
            DOWNLOAD_PATH,
            filename=token
        )

        return token


if __name__ == '__main__':
    d=VideoDownload()
    token = d.download('https://www.youtube.com/watch?v=3RmJh88D19Q')

    print(token)
