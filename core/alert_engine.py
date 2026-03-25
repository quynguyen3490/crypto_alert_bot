class AlertEngine:
    def __init__(self):
        self.last_trigger = {}

    def format_price(self, price):
        if price >= 1000:
            return f"{price:,.2f}"     # 67,123.45
        elif price >= 1:
            return f"{price:,.3f}"     # 123.456
        elif price >= 0.01:
            return f"{price:,.4f}"     # 0.1234
        elif price >= 0.0001:
            return f"{price:,.6f}"     # 0.000123
        else:
            return f"{price:,.8f}"     # 0.00001234
        
    def format_percent(self, p):
        return f"{p:.2f}%"

    def format_usd(self, v):
        return f"{v:,.2f}$"

    def check(self, symbol, prev, last, mode, threshold):
        if prev is None:
            return None

        key = f"{symbol}_{mode}_{threshold}"

        if (last - prev) <= 0:
            idicator = "🔴"
        elif (last - prev) > 0:
            idicator = "🟢"

        if mode == "percent":
            change = abs((last - prev) / prev * 100)
            if change >= threshold:
                return f"{symbol} ${self.format_price(last)} {idicator}{((last - prev) / prev * 100):.2f}%"

        elif mode == "usd":
            change = abs(last - prev)

            if change >= threshold:
                return f"{symbol} ${self.format_price(last)} {idicator}{(last - prev):.2f}$"

        elif mode == "price":
            if prev < threshold <= last:
                if self.last_trigger.get(key) != "up":
                    self.last_trigger[key] = "up"
                    return f"{symbol} 🚀 BREAK UP {threshold}"
            elif prev > threshold >= last:
                if self.last_trigger.get(key) != "down":
                    self.last_trigger[key] = "down"
                    return f"{symbol} 🔻 BREAK DOWN {threshold}"

        return None