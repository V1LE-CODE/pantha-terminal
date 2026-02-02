from __future__ import annotations

import requests
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive
from textual import events


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
# ASCII
# --------------------------------------------------

PANTHAM_ASCII = r"""
⠀⠀⠀⠀⠀⠀⠀/\_/\ 
   ____/ o o \
 /~____  =ø= /
(______)__m_m)

░▒▓█▓▒░  P A N T H A M   A W A K E N E D  ░▒▓█▓▒░
"""

HELP_TEXT = """
[bold #ff4dff]COMMANDS[/]

help
  Show this menu

pantham
  Enable Pantham Mode

stock
  Open live crypto panel (Pantham Mode required)

exit / quit
  Close terminal

[bold #ff4dff]CRYPTO PANEL[/]
C   Toggle USD / AUD
ESC Close panel
"""


# --------------------------------------------------
# CRYPTO PANEL
# --------------------------------------------------

class PanthamCryptoTerminal(Vertical):
    currency: reactive[str] = reactive("usd")

    def compose(self) -> ComposeResult:
        self.btc = Static()
        self.eth = Static()

        yield Static(
            "[bold #ff4dff]PANTHAM LIVE CRYPTO TERMINAL[/]\n"
            "[#888888]C → USD/AUD | ESC → close[/]"
        )
        yield self.btc
        yield self.eth

    def on_mount(self) -> None:
        self.update_prices()
        self.timer = self.set_interval(15, self.update_prices)

    def on_unmount(self) -> None:
        if hasattr(self, "timer"):
            self.timer.stop()

    def update_prices(self) -> None:
        try:
            r = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "bitcoin,ethereum", "vs_currencies": self.currency},
                timeout=5,
            )
            data = r.json()

            self.btc.update(
                f"[bold #b066ff]BTC[/]\n"
                f"[#ff4dff]{data['bitcoin'][self.currency]:,.2f} {self.currency.upper()}[/]"
            )
            self.eth.update(
                f"[bold #b066ff]ETH[/]\n"
                f"[#ff4dff]{data['ethereum'][self.currency]:,.2f} {self.currency.upper()}[/]"
            )
        except Exception:
            self.btc.update("[red]BTC ERROR[/]")
            self.eth.update("[red]ETH ERROR[/]")

    def on_key(self, event: events.Key) -> None:
        if event.key.lower() == "c":
            self.currency = "aud" if self.currency == "usd" else "usd"
            self.update_prices()
            event.stop()

        elif event.key == "escape":
            self.remove()
            event.stop()


# --------------------------------------------------
# MAIN APP
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
                    yield Static("[bold]SYSTEM[/]")
                    yield Static("• Pantham Mode\n• Live Crypto")

                # ✅ STORE REFERENCE
                self.right_panel = Vertical()
                yield self.right_panel

        yield Footer()

    def on_mount(self) -> None:
        self.log = RichLog(markup=True)
        self.input = Input(placeholder="Type a command...")

        self.right_panel.mount(
            ScrollableContainer(self.log),
            self.input,
        )

        self.log.write("[bold #ff4dff]Pantha Terminal Online[/]")
        self.log.write("[#b066ff]Type [bold]help[/] to begin[/]")
        self.input.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip().lower()
        event.input.value = ""

        self.log.write(f"> {cmd}")

        if not cmd:
            return

        if cmd == "help":
            self.log.write(HELP_TEXT)

        elif cmd == "pantham":
            self.pantham_mode = True
            self.log.write(f"[bold #ff4dff]{PANTHAM_ASCII}[/]")

        elif cmd == "stock":
            if not self.pantham_mode:
                self.log.write("[red]Pantham Mode required[/]")
            else:
                existing = self.right_panel.query(PanthamCryptoTerminal)
                for panel in existing:
                    panel.remove()
                self.right_panel.mount(PanthamCryptoTerminal())

        elif cmd in ("exit", "quit"):
            self.exit()

        else:
            self.log.write("[#888888]Unknown command (type help)[/]")


# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    PanthaTerminal().run()
