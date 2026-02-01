from __future__ import annotations

import os
import sys
import subprocess
import requests
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive


# --------------------------------------------------
# UTILS
# --------------------------------------------------

def resource_path(relative: str) -> str:
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative)


# --------------------------------------------------
# BANNER
# --------------------------------------------------

class PanthaBanner(Static):
    def on_mount(self) -> None:
        self.update(
            r"""
     ^---^
    ( . . )
    (___'_)
v1  ( | | )___
   (__m_m__)__}
██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗
██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗
██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝

        ░▒▓█▓▒░  P A N T H A   T E R M I N A L  ░▒▓█▓▒░
"""
        )


# --------------------------------------------------
# CRYPTO TERMINAL (SPAWNED)
# --------------------------------------------------

class CryptoPriceBox(Static):
    def update_price(self, name: str, price: float, currency: str) -> None:
        self.update(
            f"[bold #b066ff]{name}[/]\n"
            f"[#ff4dff]{price:,.2f} {currency.upper()}[/]"
        )


class PanthaCryptoTerminal(App):
    TITLE = "Pantha Crypto Terminal"
    SUB_TITLE = "BTC • ETH • LIVE"

    currency: reactive[str] = reactive("usd")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Vertical(id="crypto_root"):
            yield Static(
                "[bold #ff4dff]PANTHA CRYPTO MONITOR[/]\n"
                "[#888888]Press C to change currency (USD / AUD / EUR)[/]",
                id="crypto_title",
            )

            with Horizontal():
                self.btc = CryptoPriceBox()
                self.eth = CryptoPriceBox()
                yield self.btc
                yield self.eth

        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(5, self.refresh_prices)

    def refresh_prices(self) -> None:
        try:
            r = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": "bitcoin,ethereum",
                    "vs_currencies": self.currency,
                },
                timeout=5,
            ).json()

            self.btc.update_price("BITCOIN", r["bitcoin"][self.currency], self.currency)
            self.eth.update_price("ETHEREUM", r["ethereum"][self.currency], self.currency)

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
# MAIN TERMINAL
# --------------------------------------------------

class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Official Pantha Terminal V1.0.0"

    status_text: reactive[str] = reactive("Ready")

    def __init__(self) -> None:
        super().__init__()
        self.command_history: list[str] = []
        self.history_index = -1
        self.pantha_mode = False

        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = (
            os.environ.get("COMPUTERNAME")
            or (os.uname().nodename if hasattr(os, "uname") else "local")
        )

    # ---------------- UI ----------------

    def compose(self) -> ComposeResult:
        with Vertical(id="frame"):
            yield Header(show_clock=True)

            with Vertical(id="root"):
                yield PanthaBanner()

                with Horizontal():
                    with Vertical(id="left_panel"):
                        yield Static("SYSTEM")
                        yield Static(
                            f"• User: {self.username}\n"
                            f"• Host: {self.hostname}\n"
                            "• Pantham Mode",
                        )

                        yield Static("HOTKEYS")
                        yield Static(
                            "pantham → enable mode\n"
                            "stock   → crypto terminal\n"
                            "CTRL+L  → clear\n"
                        )

                    with Vertical(id="right_panel"):
                        yield Static("OUTPUT")

                        with ScrollableContainer():
                            yield RichLog(id="log", markup=True)

                        yield Static("", id="status_line")
                        yield Input(placeholder="Type a command...", id="command_input")

            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#log", RichLog).write(
            "[bold #ff4dff]Pantha Terminal Online.[/]\n"
            "[#b066ff]Type pantham to awaken the core.[/]"
        )
        self.query_one("#command_input", Input).focus()

    # ---------------- INPUT ----------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""
        self.run_command(cmd)

    # ---------------- COMMANDS ----------------

    def update_status(self, text: str) -> None:
        self.query_one("#status_line", Static).update(
            f"[#ff4dff]STATUS:[/] {text}"
        )

    def prompt(self) -> str:
        return f"[#b066ff]{self.username}[/]@[#ff4dff]{self.hostname}[/]:~$"

    def run_command(self, cmd: str) -> None:
        if not cmd:
            return

        log = self.query_one("#log", RichLog)
        log.write(f"{self.prompt()} {cmd}")

        low = cmd.lower()

        if low == "pantham":
            self.pantha_mode = True
            log.write("[bold #ff4dff]PANTHAM MODE ONLINE[/]")
            self.update_status("PANTHAM MODE")
            return

        if low == "pantham off":
            self.pantha_mode = False
            log.write("[#888888]Pantham Mode disengaged.[/]")
            self.update_status("NORMAL MODE")
            return

        if low == "stock":
            if not self.pantha_mode:
                log.write("[red]Access denied. Pantham Mode required.[/]")
                return

            log.write("[#b066ff]Launching Pantha Crypto Terminal...[/]")
            subprocess.Popen([sys.executable, __file__, "--crypto"])
            return

        if low in ("exit", "quit"):
            self.exit()
            return

        log.write("[#888888]Unknown command.[/]")


# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    if "--crypto" in sys.argv:
        PanthaCryptoTerminal().run()
    else:
        PanthaTerminal().run()
