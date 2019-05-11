from .Interval import Interval

class VideoInterval(Interval):
    def __init__(self, begin, end, text, src, video_from, video_to):
        Interval.__init__(self, begin, end, text)
        self.src = src
        self.video_begin = video_from
        self.video_end = video_to

    def __str__(self):
        return "VIDEO interval begin: {:s}, end: {:s}, text: {:s}, src: {:s}".format(str(self.begin), str(self.end), str(self.text), str(self.src))
    
    def __repr__(self):
        return self.__str__()