from __future__ import annotations

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
# PANTHAM ASCII
# --------------------------------------------------

PANTHAM_ASCII = r"""
⠀⠀⠀⠀⠀⠀⠀/\_/\ 
   ____/ o o \
 /~____  =ø= /
(______)__m_m)
      ░▒▓█▓▒░  P A N T H A M   A W A K E N E D  ░▒▓█▓▒░
"""


# --------------------------------------------------
# LIVE CRYPTO PANEL (SAFE)
# --------------------------------------------------

class PanthamCryptoTerminal(Vertical):
    currency: reactive[str] = reactive("usd")

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold #ff4dff]PANTHAM LIVE CRYPTO TERMINAL[/]\n"
            "[#888888]C → USD/AUD | ESC → close[/]"
        )
        self.btc = Static()
        self.eth = Static()
        yield self.btc
        yield self.eth

    def on_mount(self) -> None:
        self.update_prices()
        self._timer = self.set_interval(15, self.update_prices)

    def on_unmount(self) -> None:
        self._timer.stop()

    def update_prices(self) -> None:
        try:
            r = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "bitcoin,ethereum", "vs_currencies": self.currency},
                timeout=5,
            )
            data = r.json()
            self.btc.update(f"BTC: {data['bitcoin'][self.currency]}")
            self.eth.update(f"ETH: {data['ethereum'][self.currency]}")
        except Exception:
            self.btc.update("[red]BTC ERROR[/]")
            self.eth.update("[red]ETH ERROR[/]")


# --------------------------------------------------
# MAIN TERMINAL
# --------------------------------------------------

class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Official Pantha Terminal"

    pantham_mode: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Vertical():
            yield PanthaBanner()

            with Horizontal():
                with Vertical(id="left"):
                    yield Static("SYSTEM")
                    yield Static("• Pantham Mode\n• Live Crypto")

                with Vertical(id="right"):
                    with ScrollableContainer():
                        yield RichLog(id="log", markup=True)
                    yield Input(id="input", placeholder="Type a command...")

        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[bold green]Pantha Terminal Online[/]")
        self.query_one("#input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip().lower()
        event.input.value = ""

        log = self.query_one("#log", RichLog)
        log.write(f"> {cmd}")

        if cmd == "pantham":
            self.pantham_mode = True
            log.write(PANTHAM_ASCII)
            return

        if cmd == "stock":
            if not self.pantham_mode:
                log.write("[red]Pantham Mode required[/]")
                return

            if not self.query(PanthamCryptoTerminal):
                self.query_one("#right").mount(PanthamCryptoTerminal())
            return

        if cmd in ("exit", "quit"):
            self.exit()
            return

        log.write("[#888888]Unknown command[/]")

    def on_exception(self, exception: Exception) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[red]CRASH PREVENTED:[/] {exception}")


# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    PanthaTerminal().run()
