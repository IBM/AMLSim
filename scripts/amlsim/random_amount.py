import random

class RandomAmount:
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def getAmount(self):
        return random.uniform(self.min, self.max)
