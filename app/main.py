from __future__ import annotations

import os
import sys
import json
import asyncio
from pathlib import Path

import websockets

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive

from app.charts import Sparkline
from app.alerts import AlertManager
from app.signals import SignalEngine


# --------------------------------------------------
# PACKAGING
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
⠀⠀⠀⠀⠀⠀⠀/\_/\ 
   ____/ o o \ 
 /~____  =ø= / 
(______)__m_m)
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
    SUB_TITLE = "Real-Time Market Terminal"

    CSS_PATH = None
    status_text: reactive[str] = reactive("Ready")

    # --------------------------------------------------

    def __init__(self) -> None:
        super().__init__()

        self.pantha_mode = False
        self.market_task: asyncio.Task | None = None

        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = (
            os.environ.get("COMPUTERNAME")
            or (os.uname().nodename if hasattr(os, "uname") else "local")
        )

        # --- Market State ---
        self.prices = {"BTC": None, "ETH": None}
        self.history = {
            "BTC": Sparkline(),
            "ETH": Sparkline(),
        }

        self.alerts = AlertManager()
        self.signals = SignalEngine()

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

            with Vertical():
                yield PanthaBanner()

                with Horizontal():
                    with Vertical(id="left"):
                        yield Static("SYSTEM", classes="title")
                        yield Static(
                            f"User: {self.username}\n"
                            f"Host: {self.hostname}\n"
                            "Mode: Pantham",
                            id="system_info",
                        )

                    with Vertical(id="market"):
                        yield Static("", id="btc_panel")
                        yield Static("", id="eth_panel")

                yield RichLog(id="log", markup=True, highlight=True)
                yield Static("", id="status")
                yield Input(placeholder="Command…", id="input")

            yield Footer()

    # --------------------------------------------------
    # LIFECYCLE
    # --------------------------------------------------

    def on_mount(self) -> None:
        self.load_tcss()
        self.query_one("#input", Input).focus()
        self.log("[bold #ff4dff]Pantha Terminal Online.[/]")
        self.log("Type [bold]pantham[/] to awaken the market.")
        self.update_status("Ready")

    # --------------------------------------------------
    # INPUT
    # --------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""

        self.log(f"[#b066ff]{self.username}@{self.hostname}[/] $ {cmd}")

        if cmd == "pantham":
            self.enable_pantha()
            return

        if cmd == "pantham off":
            self.disable_pantha()
            return

        if cmd.startswith("alert"):
            _, sym, price = cmd.split()
            self.alerts.add(sym, float(price))
            self.update_status(f"Alert set: {sym.upper()} @ {price}")
            return

        if cmd in ("exit", "quit"):
            self.exit()

    # --------------------------------------------------
    # STATUS / LOG
    # --------------------------------------------------

    def log(self, msg: str) -> None:
        self.query_one("#log", RichLog).write(msg)

    def update_status(self, text: str) -> None:
        self.status_text = text
        self.query_one("#status", Static).update(
            f"[#ff4dff]STATUS:[/] {text}"
        )

    # --------------------------------------------------
    # PANTHAM MODE
    # --------------------------------------------------

    def enable_pantha(self) -> None:
        if self.pantha_mode:
            return

        self.pantha_mode = True
        self.update_status("PANTHAM MODE ONLINE")
        self.market_task = asyncio.create_task(self.market_loop())

    def disable_pantha(self) -> None:
        self.pantha_mode = False
        self.update_status("PANTHAM MODE OFF")

        if self.market_task:
            self.market_task.cancel()
            self.market_task = None

    # --------------------------------------------------
    # MARKET LOOP
    # --------------------------------------------------

    async def market_loop(self) -> None:
        url = "wss://stream.binance.com:9443/stream?streams=btcusdt@trade/ethusdt@trade"

        while self.pantha_mode:
            try:
                async with websockets.connect(url) as ws:
                    async for raw in ws:
                        msg = json.loads(raw)
                        data = msg["data"]

                        symbol = "BTC" if data["s"] == "BTCUSDT" else "ETH"
                        price = float(data["p"])

                        await self.on_price(symbol, price)

            except Exception:
                await asyncio.sleep(2)

    # --------------------------------------------------
    # PRICE UPDATE
    # --------------------------------------------------

    async def on_price(self, symbol: str, price: float) -> None:
        last = self.prices[symbol]
        self.prices[symbol] = price
        self.history[symbol].add(price)

        panel = self.query_one(f"#{symbol.lower()}_panel", Static)

        direction = ""
        if last:
            direction = "up" if price > last else "down"

        signal = self.signals.update(symbol, price)
        spark = self.history[symbol].render()

        panel.update(
            f"[bold]{symbol}[/]\n"
            f"${price:,.2f}\n"
            f"{spark}\n"
            f"Signal: {signal or '—'}",
        )

        panel.set_class(True, direction)
        await asyncio.sleep(0.15)
        panel.set_class(False, direction)

        self.alerts.check(
            symbol,
            price,
            lambda m: self.log(f"[bold red]{m}[/]"),
        )


# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    PanthaTerminal().run()
