class Interval:
    def __init__(self, begin, end, text):
        self.begin = begin
        self.end = end
        self.text = text

    def __str__(self):
        return "abstract interval begin: {:s}, end: {:s}, text: {:s}".format(str(self.begin), str(self.end), str(self.text))
    
    def __repr__(self):
        return self.__str__()