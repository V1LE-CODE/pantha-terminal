class AlertManager:
    def __init__(self):
        self.alerts = []

    def add(self, symbol, target):
        self.alerts.append((symbol.upper(), target))

    def check(self, symbol, price, notify):
        for a in self.alerts[:]:
            if a[0] == symbol and price >= a[1]:
                notify(f"🔔 {symbol} HIT {a[1]:,.2f}")
                self.alerts.remove(a)
