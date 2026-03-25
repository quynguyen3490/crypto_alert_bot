class PriceStore:
    def __init__(self):
        self.data = {}

    def update(self, symbol, price):
        if symbol not in self.data:
            self.data[symbol] = {"prev": None, "last": price}
            return None

        prev = self.data[symbol]["last"]
        self.data[symbol]["prev"] = prev
        self.data[symbol]["last"] = price

        return self.data[symbol]

    def get(self, symbol):
        return self.data.get(symbol)