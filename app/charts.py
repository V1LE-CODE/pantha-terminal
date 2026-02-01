from collections import deque

class Sparkline:
    def __init__(self, size=30):
        self.data = deque(maxlen=size)

    def add(self, value):
        self.data.append(value)

    def render(self):
        blocks = "▁▂▃▄▅▆▇█"
        if not self.data:
            return ""
        mn, mx = min(self.data), max(self.data)
        span = mx - mn or 1
        return "".join(
            blocks[int((v - mn) / span * (len(blocks) - 1))]
            for v in self.data
        )
