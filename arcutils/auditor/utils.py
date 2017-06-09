from collections import Iterator


class Sequencer(Iterator):

    __slots__ = ('start', 'value', 'step')

    def __init__(self, start=0, step=1):
        self.start = start
        self.value = start
        self.step = step

    def __next__(self):
        value = self.value
        self.value += 1
        return value

    def reset(self):
        self.value = self.start
