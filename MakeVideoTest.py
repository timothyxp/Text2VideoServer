# This Python file uses the following encoding: utf-8
from data.ImageInterval import ImageInterval
from data.VideoInterval import *
from utils.video_maker import *

def MainTest():
    intervals = [
        VideoInterval(0, 10, "Здесь какой-то текст", 'downloaded/clip.mp4', 0, 10),
        ImageInterval(10, 14, "Картинка 1", "https://artchive.ru/res/media/img/oy800/work/a77/337252.jpeg"),
        VideoInterval(14, 24, "Опять пятая колона", 'downloaded/clip.mp4', 20, 30)
    ]
    videoMaker = VideoMaker()
    videoFile = videoMaker.make(intervals, "unemotional")
    assert(videoFile != None)
    print(videoFile)

MainTest()