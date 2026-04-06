from collections import deque
import json

class PriceStore:
    def __init__(self, max_candles=500):
        # mỗi symbol sẽ có danh sách nến
        self.data = {}
        self.max_candles = max_candles

    def update_kline(self, symbol, k):
        """
        k: object "k" từ Binance websocket
        """

        if symbol not in self.data:
            self.data[symbol] = deque(maxlen=self.max_candles)

        candles = self.data[symbol]

        candle = {
            "open_time": k["t"],
            "close_time": k["T"],
            "open": float(k["o"]),
            "high": float(k["h"]),
            "low": float(k["l"]),
            "close": float(k["c"]),
            "volume": float(k["v"]),
            "trades": k["n"],
            "is_closed": k["x"]
        }

        # 🔥 logic quan trọng
        if not candles:
            candles.append(candle)
            return candle

        last_candle = candles[-1]

        # nếu cùng 1 cây nến (đang update realtime)
        if last_candle["open_time"] == candle["open_time"]:
            candles[-1] = candle
        else:
            candles.append(candle)

        # print("Debug PriceStore@updatekline: " + json.dumps(candle, indent=2), flush=True)

        return candle

    def get_latest(self, symbol):
        if symbol not in self.data or not self.data[symbol]:
            return None
        return self.data[symbol][-1]

    def get_all(self, symbol):
        return list(self.data.get(symbol, []))

    def get_closed(self, symbol):
        """chỉ lấy nến đã đóng"""
        return [c for c in self.data.get(symbol, []) if c["is_closed"]]
    
    def get_ma(self, symbol, length=14, source="close", only_closed=True):
        candles = self.data.get(symbol, [])

        if not candles:
            return None

        # lọc nến đã đóng nếu cần
        if only_closed:
            candles = [c for c in candles if c["is_closed"]]

        if not candles:
            return None

        # 🔥 lấy tối đa length nến gần nhất (nếu thiếu thì lấy hết)
        selected = list(candles)[-length:]

        values = [c[source] for c in selected]

        # 🔥 chia theo số phần tử thực tế (không phải length)
        return sum(values) / len(values)