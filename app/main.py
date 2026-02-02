from __future__ import annotations

import os
import sys
import asyncio
import requests

from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive


# --------------------------------------------------
# BANNER
# --------------------------------------------------

class PanthaBanner(Static):
    def on_mount(self) -> None:
        self.update(
            r"""
     ^---^
    ( . . )
    (___'_ )
v1  ( | | )___
   (__m_m__)__}
██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗
██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗
██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝
"""
        )


# --------------------------------------------------
# CRYPTO PANEL (EMBEDDED, SAFE)
# --------------------------------------------------

class CryptoPanel(Vertical):
    currency: reactive[str] = reactive("usd")

    def on_mount(self) -> None:
        self.btc = Static("", id="btc")
        self.eth = Static("", id="eth")

        self.mount(
            Static(
                "[bold #ff4dff]PANTHA CRYPTO MONITOR[/]\n"
                "[#888888]C → currency | ESC → close[/]"
            )
        )
        self.mount(self.btc)
        self.mount(self.eth)

        self.set_interval(6, self.refresh_prices)
        self.refresh_prices()

    async def refresh_prices(self) -> None:
        try:
            data = await asyncio.to_thread(
                lambda: requests.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={
                        "ids": "bitcoin,ethereum",
                        "vs_currencies": self.currency,
                    },
                    timeout=8,
                ).json()
            )

            self.btc.update(
                f"[bold #b066ff]BITCOIN[/]\n[#ff4dff]{data['bitcoin'][self.currency]:,.2f} {self.currency.upper()}[/]"
            )
            self.eth.update(
                f"[bold #b066ff]ETHEREUM[/]\n[#ff4dff]{data['ethereum'][self.currency]:,.2f} {self.currency.upper()}[/]"
            )

        except Exception:
            self.btc.update("[red]BTC API ERROR[/]")
            self.eth.update("[red]ETH API ERROR[/]")

    def on_key(self, event) -> None:
        if event.key.lower() == "c":
            self.currency = {
                "usd": "aud",
                "aud": "eur",
                "eur": "usd",
            }[self.currency]

        if event.key == "escape":
            self.remove()


# --------------------------------------------------
# MAIN TERMINAL
# --------------------------------------------------

class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Official Pantha Terminal V1.0.0"

    pantha_mode: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Vertical():
            yield PanthaBanner()

            with Horizontal():
                with Vertical(id="left"):
                    yield Static("SYSTEM")
                    yield Static("• Pantham Mode\n• Crypto Enabled")

                with Vertical(id="right"):
                    yield Static("OUTPUT")
                    with ScrollableContainer():
                        yield RichLog(id="log", markup=True)
                    yield Input(placeholder="Type a command...", id="input")

        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]Pantha Terminal Online.[/]")
        log.write("[#b066ff]Type pantham to awaken the core.[/]")
        self.query_one("#input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip().lower()
        event.input.value = ""

        log = self.query_one("#log", RichLog)
        log.write(f"> {cmd}")

        if cmd == "pantham":
            self.pantha_mode = True
            log.write("[bold #ff4dff]PANTHAM MODE ONLINE[/]")
            return

        if cmd == "stock":
            if not self.pantha_mode:
                log.write("[red]Pantham Mode required.[/]")
                return

            if not self.query(CryptoPanel):
                self.mount(CryptoPanel())

            return

        if cmd in ("exit", "quit"):
            self.exit()
            return

        log.write("[#888888]Unknown command.[/]")


# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    PanthaTerminal().run()
