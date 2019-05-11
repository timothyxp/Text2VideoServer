from utils.text_analyze import TextAnalyzeBase
from utils.video_download import VideoDownloadBase
from utils.video_maker import VideoMakerBase


class Config():
    def __init__(self):
        analyzer = TextAnalyzeBase()
        downloader = VideoDownloadBase()
        maker = VideoMakerBase()
