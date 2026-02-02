from __future__ import annotations

import sys
import traceback
from pathlib import Path
import requests

from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive


# --------------------------------------------------
# HARD CRASH LOGGER (PREVENTS SILENT CLOSE)
# --------------------------------------------------

LOG_FILE = Path.home() / "pantha_crash.log"

def excepthook(exc_type, exc, tb):
    LOG_FILE.write_text(
        "".join(traceback.format_exception(exc_type, exc, tb)),
        encoding="utf-8",
    )

sys.excepthook = excepthook


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
██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗ ███╗   ███╗
██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗████╗ ████║
██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║██╔████╔██║
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║██║╚██╔╝██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║██║ ╚═╝ ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝

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
        if hasattr(self, "_timer"):
            self._timer.stop()

    def update_prices(self) -> None:
        try:
            r = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": "bitcoin,ethereum",
                    "vs_currencies": self.currency,
                },
                timeout=5,
            )
            r.raise_for_status()
            data = r.json()

            self.btc.update(
                f"[bold #b066ff]BITCOIN[/]\n"
                f"[#ff4dff]{data['bitcoin'][self.currency]:,.2f} {self.currency.upper()}[/]"
            )
            self.eth.update(
                f"[bold #b066ff]ETHEREUM[/]\n"
                f"[#ff4dff]{data['ethereum'][self.currency]:,.2f} {self.currency.upper()}[/]"
            )

        except Exception as e:
            self.btc.update("[red]BTC API ERROR[/]")
            self.eth.update("[red]ETH API ERROR[/]")


# --------------------------------------------------
# MAIN TERMINAL
# --------------------------------------------------

class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Official Pantha Terminal v1.0.0"

    pantham_mode: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Vertical():
            yield PanthaBanner()

            with Horizontal():
                with Vertical(id="left"):
                    yield Static("SYSTEM")
                    yield Static("• Pantham Mode\n• Live Crypto\n• Secure Terminal")

                with Vertical(id="right"):  # 🔥 FIXED: ID WAS MISSING
                    yield Static("OUTPUT")
                    with ScrollableContainer():
                        yield RichLog(id="log", markup=True)
                    yield Input(placeholder="Type a command...", id="input")

        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]Pantha Terminal Online.[/]")
        log.write("[#b066ff]Type [bold]pantham[/] to awaken the core.[/]")
        self.query_one("#input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip().lower()
        event.input.value = ""

        log = self.query_one("#log", RichLog)
        log.write(f"> {cmd}")

        try:
            if cmd == "pantham":
                self.pantham_mode = True
                log.write(PANTHAM_ASCII)
                return

            if cmd == "stock":
                if not self.pantham_mode:
                    log.write("[red]Pantham Mode required.[/]")
                    return

                if not self.query(PanthamCryptoTerminal):
                    self.query_one("#right").mount(PanthamCryptoTerminal())
                return

            if cmd in ("exit", "quit"):
                self.exit()
                return

            log.write("[#888888]Unknown command.[/]")

        except Exception as e:
            log.write(f"[red]Command error: {e}[/]")

    def on_key(self, event) -> None:
        panel = self.query_one(PanthamCryptoTerminal, default=None)
        if not panel:
            return

        if event.key.lower() == "c":
            panel.currency = "aud" if panel.currency == "usd" else "usd"

        if event.key == "escape":
            panel.remove()


# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    try:
        PanthaTerminal().run()
    except Exception as e:
        LOG_FILE.write_text(str(e), encoding="utf-8")
        input("Pantha crashed. Press Enter to close...")
