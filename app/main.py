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
# HELP TEXT
# --------------------------------------------------

HELP_TEXT = """
[bold #ff4dff]AVAILABLE COMMANDS[/]

[bold]help[/]
  Show this help menu

[bold]pantham[/]
  Awaken Pantham Mode (required for advanced systems)

[bold]stock[/]
  Open live crypto terminal (Pantham Mode only)

[bold]exit[/], [bold]quit[/]
  Close Pantha Terminal

[bold #ff4dff]CRYPTO PANEL KEYS[/]
  [bold]C[/]     Toggle USD / AUD
  [bold]ESC[/]   Close crypto panel
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
                params={
                    "ids": "bitcoin,ethereum",
                    "vs_currencies": self.currency,
                },
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
                    yield Static("[bold]SYSTEM[/]")
                    yield Static("• Pantham Mode\n• Live Crypto")

                with Vertical(id="right"):
                    with ScrollableContainer():
                        yield RichLog(id="log", markup=True)
                    yield Input(id="input", placeholder="Type a command...")

        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]Pantha Terminal Online[/]")
        log.write("[#b066ff]Type [bold]help[/] for available commands[/]")
        self.query_one("#input", Input).focus()

    # Prevent hard crashes (EXE safe)
    def on_exception(self, exception: Exception) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[bold red]ERROR PREVENTED:[/] {exception}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        try:
            cmd = event.value.strip().lower()
            event.input.value = ""

            log = self.query_one("#log", RichLog)
            log.write(f"> {cmd}")

            if not cmd:
                return

            if cmd == "help":
                log.write(HELP_TEXT)

            elif cmd == "pantham":
                self.pantham_mode = True
                log.write(f"[bold #ff4dff]{PANTHAM_ASCII}[/]")

            elif cmd == "stock":
                if not self.pantham_mode:
                    log.write("[red]Pantham Mode required[/]")
                else:
                    old = self.query_one("#crypto", default=None)
                    if old:
                        old.remove()
                    self.query_one("#right").mount(
                        PanthamCryptoTerminal(id="crypto")
                    )

            elif cmd in ("exit", "quit"):
                self.exit()

            else:
                log.write("[#888888]Unknown command (type help)[/]")

        except Exception as e:
            self.on_exception(e)

        # 🔑 Always restore input focus
        self.call_later(self.query_one("#input", Input).focus)

    # Global key handling (safe)
    def on_key(self, event: events.Key) -> None:
        panel = self.query_one("#crypto", default=None)

        if event.key == "enter":
            return

        if not panel:
            return

        if event.key.lower() == "c":
            panel.currency = "aud" if panel.currency == "usd" else "usd"
            panel.update_prices()

        elif event.key == "escape":
            panel.remove()


# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    PanthaTerminal().run()
