from collections import deque
from typing import Iterable


class Sparkline:
    BLOCKS = "▁▂▃▄▅▆▇█"

    def __init__(self, size: int = 30):
        self.size = size
        self.data: deque[float] = deque(maxlen=size)

    # -------------------------------
    # DATA
    # -------------------------------

    def add(self, value: float) -> None:
        try:
            self.data.append(float(value))
        except (TypeError, ValueError):
            pass

    def extend(self, values: Iterable[float]) -> None:
        for v in values:
            self.add(v)

    # -------------------------------
    # RENDERING
    # -------------------------------

    def render(
        self,
        *,
        show_last: bool = True,
        color: bool = True,
    ) -> str:
        if not self.data:
            return ""

        mn = min(self.data)
        mx = max(self.data)
        span = mx - mn or 1.0

        chars = [
            self.BLOCKS[
                int((v - mn) / span * (len(self.BLOCKS) - 1))
            ]
            for v in self.data
        ]

        spark = "".join(chars)

        if not color:
            return spark

        # Directional color (last vs first)
        if len(self.data) >= 2:
            if self.data[-1] > self.data[0]:
                spark = f"[green]{spark}[/]"
            elif self.data[-1] < self.data[0]:
                spark = f"[red]{spark}[/]"
            else:
                spark = f"[yellow]{spark}[/]"

        if show_last:
            spark += f" [#888888]{self.data[-1]:,.2f}[/]"

        return spark
