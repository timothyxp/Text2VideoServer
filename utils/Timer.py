import time

class Timer:
    def __init__(self):
        self.startMoment = 0
        self.endMoment = 0

    def start(self):
        self.startMoment = time.time()

    def end(self):
        self.endMoment = time.time()
        return self.endMoment - self.startMoment