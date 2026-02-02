from __future__ import annotations

import json
import urllib.request

from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Static
from textual.reactive import reactive


# --------------------------------------------------
# PRICE BOX
# --------------------------------------------------

class PriceBox(Static):
    def update_price(self, name: str, price: float, currency: str) -> None:
        self.update(
            f"[bold #b066ff]{name}[/]\n"
            f"[#ff4dff]{price:,.2f} {currency.upper()}[/]"
        )


# --------------------------------------------------
# CRYPTO TERMINAL
# --------------------------------------------------

class CryptoTerminal(App):
    TITLE = "Pantha Crypto Terminal"
    SUB_TITLE = "BTC • ETH • Live Market"

    currency: reactive[str] = reactive("usd")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Vertical(id="root"):
            yield Static(
                "[bold #b066ff]PANTHA CRYPTO MONITOR[/]\n"
                "[#888888]Press C to cycle currency (USD / AUD / EUR)[/]",
                id="title",
            )

            with Horizontal():
                self.btc = PriceBox(id="btc")
                self.eth = PriceBox(id="eth")
                yield self.btc
                yield self.eth

        yield Footer()

    def on_mount(self) -> None:
        self.refresh_prices()
        self.set_interval(5, self.refresh_prices)

    def refresh_prices(self) -> None:
        try:
            url = (
                "https://api.coingecko.com/api/v3/simple/price"
                f"?ids=bitcoin,ethereum&vs_currencies={self.currency}"
            )

            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read().decode())

            self.btc.update_price(
                "BITCOIN",
                data["bitcoin"][self.currency],
                self.currency,
            )
            self.eth.update_price(
                "ETHEREUM",
                data["ethereum"][self.currency],
                self.currency,
            )

        except Exception:
            self.btc.update("[red]API ERROR[/]")
            self.eth.update("[red]API ERROR[/]")

    def on_key(self, event) -> None:
        if event.key.lower() == "c":
            self.currency = {
                "usd": "aud",
                "aud": "eur",
                "eur": "usd",
            }[self.currency]


# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    CryptoTerminal().run()
