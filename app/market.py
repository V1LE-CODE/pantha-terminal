import threading
import time
import requests

from typing import Callable, Dict

# Uses CoinGecko public API (no key required, near-real-time)
API_URL = "https://api.coingecko.com/api/v3/simple/price"

SYMBOL_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
}


class Market:
    """
    Live crypto market data manager.
    - Fetches BTC / ETH prices
    - Calls update callbacks on change
    - Designed for Textual background threads
    """

    def __init__(self, refresh_interval: float = 2.0):
        self.refresh_interval = refresh_interval
        self.running = False
        self.thread: threading.Thread | None = None

        self.prices: Dict[str, float] = {}
        self.callbacks: list[Callable[[str, float], None]] = []

    # --------------------------------------------------
    # CALLBACKS
    # --------------------------------------------------

    def on_update(self, callback: Callable[[str, float], None]) -> None:
        """
        Register a callback(symbol, price) that fires on price change
        """
        self.callbacks.append(callback)

    def _notify(self, symbol: str, price: float) -> None:
        for cb in self.callbacks:
            try:
                cb(symbol, price)
            except Exception:
                pass

    # --------------------------------------------------
    # FETCH
    # --------------------------------------------------

    def fetch(self) -> Dict[str, float]:
        """
        Fetch latest prices from CoinGecko
        """
        params = {
            "ids": ",".join(SYMBOL_MAP.values()),
            "vs_currencies": "usd",
        }

        r = requests.get(API_URL, params=params, timeout=5)
        r.raise_for_status()
        data = r.json()

        prices = {}
        for sym, cid in SYMBOL_MAP.items():
            prices[sym] = float(data[cid]["usd"])

        return prices

    # --------------------------------------------------
    # LOOP
    # --------------------------------------------------

    def _loop(self) -> None:
        while self.running:
            try:
                new_prices = self.fetch()

                for sym, price in new_prices.items():
                    old = self.prices.get(sym)
                    if old != price:
                        self.prices[sym] = price
                        self._notify(sym, price)

            except Exception:
                # Silent fail (keeps terminal clean)
                pass

            time.sleep(self.refresh_interval)

    # --------------------------------------------------
    # CONTROL
    # --------------------------------------------------

    def start(self) -> None:
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._loop,
            daemon=True,
            name="MarketThread",
        )
        self.thread.start()

    def stop(self) -> None:
        self.running = False

    # --------------------------------------------------
    # ACCESS
    # --------------------------------------------------

    def get(self, symbol: str) -> float | None:
        return self.prices.get(symbol.upper())

    def snapshot(self) -> Dict[str, float]:
        return dict(self.prices)
