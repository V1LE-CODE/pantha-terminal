from __future__ import annotations

import asyncio
import requests

from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Static
from textual.reactive import reactive

COINS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
}


class PriceBox(Static):
    price: reactive[str] = reactive("Loading...")
    change: reactive[str] = reactive("")

    def update_price(self, price: float, currency: str) -> None:
        self.price = f"{price:,.2f} {currency.upper()}"
        self.update(f"[bold #ff4dff]{self.price}[/]")


class CryptoTerminal(App):
    TITLE = "Pantha Crypto Terminal"
    SUB_TITLE = "BTC • ETH • Live Market"

    currency: reactive[str] = reactive("usd")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Vertical(id="root"):
            yield Static(
                "[bold #b066ff]PANTHA CRYPTO MONITOR[/]\n"
                "[#888888]Press C to cycle currency[/]",
                id="title",
            )

            with Horizontal():
                self.btc = PriceBox("BTC", id="btc")
                self.eth = PriceBox("ETH", id="eth")
                yield self.btc
                yield self.eth

        yield Footer()

    async def on_mount(self) -> None:
        self.set_interval(5, self.refresh_prices)

    async def refresh_prices(self) -> None:
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": ",".join(COINS.keys()),
                "vs_currencies": self.currency,
            }

            data = requests.get(url, params=params, timeout=5).json()

            self.btc.update_price(
                data["bitcoin"][self.currency],
                self.currency,
            )
            self.eth.update_price(
                data["ethereum"][self.currency],
                self.currency,
            )

        except Exception:
            self.btc.update("[red]API Error[/]")
            self.eth.update("[red]API Error[/]")

    def on_key(self, event) -> None:
        if event.key.lower() == "c":
            self.currency = {
                "usd": "aud",
                "aud": "eur",
                "eur": "usd",
            }[self.currency]


if __name__ == "__main__":
    CryptoTerminal().run()
