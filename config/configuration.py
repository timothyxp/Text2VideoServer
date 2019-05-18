from utils.text_analyze import TextAnalyze
from utils.video_download import VideoDownload
from utils.video_maker import VideoMaker


class Config:
    def __init__(self):
        self.analyzer = TextAnalyze()
        self.downloader = VideoDownload()
        self.maker = VideoMaker()

config = Config()
