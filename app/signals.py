from collections import deque
from typing import Dict, Optional


class SignalEngine:
    """
    Lightweight real-time signal engine.
    Generates BUY / SELL / MOMENTUM signals
    based on short-term price behavior.
    """

    def __init__(self, window: int = 12):
        self.window = window
        self.prices: Dict[str, deque] = {
            "BTC": deque(maxlen=window),
            "ETH": deque(maxlen=window),
        }

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    def update(self, symbol: str, price: float) -> Optional[str]:
        """
        Feed a new price.
        Returns signal string if triggered.
        """
        symbol = symbol.upper()
        if symbol not in self.prices:
            return None

        data = self.prices[symbol]
        data.append(price)

        if len(data) < self.window:
            return None

        return self._analyze(data)

    # --------------------------------------------------
    # SIGNAL LOGIC
    # --------------------------------------------------

    def _analyze(self, data: deque) -> Optional[str]:
        start = data[0]
        end = data[-1]
        delta = end - start
        pct = (delta / start) * 100

        # Strong upward momentum
        if pct >= 1.0:
            return "BUY ▲"

        # Strong downward momentum
        if pct <= -1.0:
            return "SELL ▼"

        # Flat but active
        if abs(pct) < 0.2:
            return "HOLD"

        return None
