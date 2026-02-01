class AlertManager:
    def __init__(self):
        # alert = {
        #   "symbol": "BTC",
        #   "target": 45000.0,
        #   "direction": "above" | "below",
        #   "once": True
        # }
        self.alerts: list[dict] = []

    def add(
        self,
        symbol: str,
        target: float,
        direction: str = "above",
        once: bool = True,
    ) -> None:
        self.alerts.append(
            {
                "symbol": symbol.upper(),
                "target": float(target),
                "direction": direction,
                "once": once,
            }
        )

    def check(self, symbol: str, price: float, notify) -> None:
        symbol = symbol.upper()

        for alert in self.alerts[:]:
            if alert["symbol"] != symbol:
                continue

            hit = False

            if alert["direction"] == "above" and price >= alert["target"]:
                hit = True
            elif alert["direction"] == "below" and price <= alert["target"]:
                hit = True

            if hit:
                notify(
                    f"🔔 {symbol} {alert['direction'].upper()} "
                    f"{alert['target']:,.2f} (now {price:,.2f})"
                )

                if alert["once"]:
                    self.alerts.remove(alert)
