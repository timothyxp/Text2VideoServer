from abc import ABC, abstractmethod


class VideoDownloadBase(ABC):
    @abstractmethod
    def download(self, href):
        return "downloaded/first.mp4"
