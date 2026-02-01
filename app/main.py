from __future__ import annotations

import os
import sys
import json
import asyncio
from pathlib import Path
from collections import deque

import websockets

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive


# --------------------------------------------------
# PACKAGING HELPERS
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
v0  ( | | )___,
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
# MAIN APP
# --------------------------------------------------

class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Official Pantha Terminal V0.0.0"

    CSS_PATH = None
    status_text: reactive[str] = reactive("Ready")

    def __init__(self) -> None:
        super().__init__()

        # --- System ---
        self.command_history: list[str] = []
        self.history_index = -1
        self.pantha_mode = False

        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = (
            os.environ.get("COMPUTERNAME")
            or (os.uname().nodename if hasattr(os, "uname") else "local")
        )

        # --- Market State ---
        self.btc_price = 0.0
        self.eth_price = 0.0
        self.last_btc = None
        self.last_eth = None

        self.btc_history = deque(maxlen=30)
        self.eth_history = deque(maxlen=30)

        self.alerts: list[tuple[str, float]] = []
        self.candle_mode = False

        self.aud_rate = 1.0  # placeholder for future FX feed

    # --------------------------------------------------
    # STYLES
    # --------------------------------------------------

    def load_tcss(self) -> None:
        dev = Path(__file__).parent / "styles.tcss"
        if dev.exists():
            self.stylesheet.read(dev)
            return

        packed = Path(resource_path("app/styles.tcss"))
        if packed.exists():
            self.stylesheet.read(packed)

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def compose(self) -> ComposeResult:
        with Vertical(id="frame"):
            yield Header(show_clock=True)

            with Vertical(id="root"):
                yield PanthaBanner(id="banner")

                with Horizontal(id="main_row"):
                    with Vertical(id="left_panel"):
                        yield Static("SYSTEM", id="panel_title")
                        yield Static(
                            f"• User: {self.username}\n"
                            f"• Host: {self.hostname}\n"
                            "• Pantha Terminal\n"
                            "• Purple Aesthetic\n"
                            "• Pantham Mode",
                            id="system_info",
                        )

                        yield Static("HOTKEYS", id="panel_title2")
                        yield Static(
                            "ENTER     → run command\n"
                            "UP/DOWN   → history\n"
                            "CTRL+C    → quit\n"
                            "CTRL+L    → clear log\n"
                            "pantham   → toggle mode\n"
                            "alert btc 45000\n"
                            "candle on/off",
                            id="hotkeys",
                        )

                    with Vertical(id="right_panel"):
                        yield Static("OUTPUT", id="output_title")

                        with ScrollableContainer(id="log_wrap"):
                            yield RichLog(id="log", highlight=True, markup=True, wrap=True)

                        yield Static("", id="status_line")
                        yield Input(
                            placeholder="Type a command...",
                            id="command_input",
                        )

            yield Footer()

    # --------------------------------------------------
    # LIFECYCLE
    # --------------------------------------------------

    def on_mount(self) -> None:
        self.load_tcss()

        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]Pantha Terminal Online.[/]")
        log.write("[#b066ff]Type [bold]pantham[/] to awaken the core.[/]")

        self.update_status("Ready")
        self.query_one("#command_input", Input).focus()

    # --------------------------------------------------
    # INPUT
    # --------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""
        self.run_command(cmd)

    def on_key(self, event) -> None:
        inp = self.query_one("#command_input", Input)

        if event.key == "ctrl+l":
            self.query_one("#log", RichLog).clear()
            self.update_status("Cleared")
            event.stop()

        if event.key == "up" and self.command_history:
            self.history_index = max(0, self.history_index - 1)
            inp.value = self.command_history[self.history_index]
            inp.cursor_position = len(inp.value)
            event.stop()

        if event.key == "down" and self.command_history:
            self.history_index = min(len(self.command_history), self.history_index + 1)
            inp.value = "" if self.history_index >= len(self.command_history) else self.command_history[self.history_index]
            inp.cursor_position = len(inp.value)
            event.stop()

    # --------------------------------------------------
    # COMMANDS
    # --------------------------------------------------

    def update_status(self, text: str) -> None:
        self.status_text = text
        self.query_one("#status_line", Static).update(
            f"[#ff4dff]STATUS:[/] [#ffffff]{text}[/]"
        )

    def prompt(self) -> str:
        return f"[#b066ff]{self.username}[/]@[#ff4dff]{self.hostname}[/]:[#ffffff]~$[/]"

    def run_command(self, cmd: str) -> None:
        if not cmd:
            return

        self.command_history.append(cmd)
        self.history_index = len(self.command_history)

        log = self.query_one("#log", RichLog)
        log.write(f"{self.prompt()} [#ffffff]{cmd}[/]")

        low = cmd.lower()

        if low == "clear":
            log.clear()
            self.update_status("Cleared")
            return

        if low == "pantham":
            self.pantha_mode = True
            self.show_pantha_ascii()
            self.update_status("PANTHAM MODE ONLINE")
            self.run_worker(self.market_feed(), exclusive=True)
            return

        if low == "pantham off":
            self.pantha_mode = False
            self.update_status("PANTHAM MODE OFF")
            return

        if low.startswith("alert"):
            _, coin, price = low.split()
            self.alerts.append((coin.upper(), float(price)))
            self.update_status(f"Alert set: {coin.upper()} @ {price}")
            return

        if low == "candle on":
            self.candle_mode = True
            self.update_status("Candlestick mode ON")
            return

        if low == "candle off":
            self.candle_mode = False
            self.update_status("Candlestick mode OFF")
            return

        if low in ("exit", "quit"):
            self.exit()
            return

    # --------------------------------------------------
    # MARKET LOGIC
    # --------------------------------------------------

    async def market_feed(self):
        url = "wss://stream.binance.com:9443/ws/btcusdt@trade/ethusdt@trade"
        async with websockets.connect(url) as ws:
            while self.pantha_mode:
                msg = json.loads(await ws.recv())
                price = float(msg["p"])
                symbol = msg["s"]

                if symbol == "BTCUSDT":
                    self.last_btc = self.btc_price or price
                    self.btc_price = price
                    self.btc_history.append(price)
                    self.check_alert("BTC", price)

                elif symbol == "ETHUSDT":
                    self.last_eth = self.eth_price or price
                    self.eth_price = price
                    self.eth_history.append(price)
                    self.check_alert("ETH", price)

                self.refresh_market_ui()

    def sparkline(self, data):
        blocks = "▁▂▃▄▅▆▇█"
        if not data:
            return ""
        mn, mx = min(data), max(data)
        span = mx - mn or 1
        return "".join(blocks[int((v - mn) / span * (len(blocks) - 1))] for v in data)

    def ai_signal(self, data):
        if len(data) < 10:
            return "⏳ ANALYZING"
        avg = sum(list(data)[-10:]) / 10
        last = data[-1]
        if last > avg * 1.01:
            return "🟢 MOMENTUM"
        if last < avg * 0.99:
            return "🔴 WEAKNESS"
        return "🟡 NEUTRAL"

    def refresh_market_ui(self):
        log = self.query_one("#log", RichLog)

        btc_change = ((self.btc_price - self.last_btc) / self.last_btc * 100) if self.last_btc else 0
        eth_change = ((self.eth_price - self.last_eth) / self.last_eth * 100) if self.last_eth else 0

        log.write(
            f"""
[#ff4dff]┌── BITCOIN (BTC) ─────────────┐[/]
[#ffffff] ${self.btc_price:,.2f}  ({btc_change:+.2f}%)
 {self.sparkline(self.btc_history)}
 AI: {self.ai_signal(self.btc_history)}
[#ff4dff]└──────────────────────────────┘[/]

[#ff4dff]┌── ETHEREUM (ETH) ────────────┐[/]
[#ffffff] ${self.eth_price:,.2f}  ({eth_change:+.2f}%)
 {self.sparkline(self.eth_history)}
 AI: {self.ai_signal(self.eth_history)}
[#ff4dff]└──────────────────────────────┘[/]
"""
        )

    def check_alert(self, symbol, price):
        for alert in self.alerts[:]:
            if alert[0] == symbol and price >= alert[1]:
                self.query_one("#log", RichLog).write(
                    f"[bold red]🔔 ALERT:[/] {symbol} hit {alert[1]:,.2f}"
                )
                self.alerts.remove(alert)

    # --------------------------------------------------
    # PANTHAM MODE ASCII
    # --------------------------------------------------

    def show_pantha_ascii(self) -> None:
        ascii_art = r"""
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
      ░▒▓█▓▒░  STOCK • TERMINAL • MARKET        ░▒▓█▓▒░
"""

        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]" + ascii_art + "[/]")


if __name__ == "__main__":
    PanthaTerminal().run()
