import time

class SimpleTimer:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.result = None
    
    def start(self):
        self.result = None
        self.start_time = time.time()
        return self.start_time

    def end(self):
        self.end_time = time.time()
        self.result = self.end_time - self.start_time
        return self.end_time

    def result(self):
        return self.result

    def end_with_results(self):
        self.end()
        return self.result