from abc import ABC, abstractmethod


class VideoMakerBase(ABC):
    def make(self, intervals, text, emotions, overlay=None):
        pass


class VideoMaker(ABC):
    def make(self, intervals, text, emotions, overlay=None):
        pass
