from .Interval import Interval

class ImageInterval(Interval):
    def __init__(self, begin, end, text, src):
        Interval.__init__(self, begin, end, text)
        self.src = src

    def __str__(self):
        return "IMAGE interval begin: {:s}, end: {:s}, text: {:s}".format(str(self.begin), str(self.end), str(self.text))
    
    def __repr__(self):
        return self.__str__()