import unittest
from core.price_store import PriceStore

class TestPriceStore(unittest.TestCase):
    def setUp(self):
        self.store = PriceStore(max_candles=10)

    def test_update_kline_new_symbol(self):
        k = {
            "t": 1000, "T": 2000, "o": "100", "h": "110", "l": "90", "c": "105", "v": "10", "n": 5, "x": True
        }
        candle = self.store.update_kline("BTCUSDT", k)
        self.assertEqual(candle["close"], 105.0)
        self.assertEqual(len(self.store.get_all("BTCUSDT")), 1)

    def test_update_kline_same_candle(self):
        k1 = {
            "t": 1000, "T": 2000, "o": "100", "h": "110", "l": "90", "c": "105", "v": "10", "n": 5, "x": False
        }
        self.store.update_kline("BTCUSDT", k1)
        k2 = {
            "t": 1000, "T": 2000, "o": "100", "h": "115", "l": "85", "c": "110", "v": "15", "n": 10, "x": False
        }
        candle = self.store.update_kline("BTCUSDT", k2)
        self.assertEqual(candle["high"], 115.0)
        self.assertEqual(len(self.store.get_all("BTCUSDT")), 1)

    def test_update_kline_new_candle(self):
        k1 = {
            "t": 1000, "T": 2000, "o": "100", "h": "110", "l": "90", "c": "105", "v": "10", "n": 5, "x": True
        }
        self.store.update_kline("BTCUSDT", k1)
        k2 = {
            "t": 2000, "T": 3000, "o": "105", "h": "120", "l": "100", "c": "115", "v": "12", "n": 8, "x": True
        }
        self.store.update_kline("BTCUSDT", k2)
        self.assertEqual(len(self.store.get_all("BTCUSDT")), 2)

    def test_get_latest(self):
        k = {
            "t": 1000, "T": 2000, "o": "100", "h": "110", "l": "90", "c": "105", "v": "10", "n": 5, "x": True
        }
        self.store.update_kline("BTCUSDT", k)
        latest = self.store.get_latest("BTCUSDT")
        self.assertEqual(latest["close"], 105.0)

    def test_get_latest_no_data(self):
        latest = self.store.get_latest("NONEXIST")
        self.assertIsNone(latest)

    def test_get_all(self):
        k = {
            "t": 1000, "T": 2000, "o": "100", "h": "110", "l": "90", "c": "105", "v": "10", "n": 5, "x": True
        }
        self.store.update_kline("BTCUSDT", k)
        all_candles = self.store.get_all("BTCUSDT")
        self.assertEqual(len(all_candles), 1)

    def test_get_closed(self):
        k1 = {
            "t": 1000, "T": 2000, "o": "100", "h": "110", "l": "90", "c": "105", "v": "10", "n": 5, "x": True
        }
        k2 = {
            "t": 2000, "T": 3000, "o": "105", "h": "120", "l": "100", "c": "115", "v": "12", "n": 8, "x": False
        }
        self.store.update_kline("BTCUSDT", k1)
        self.store.update_kline("BTCUSDT", k2)
        closed = self.store.get_closed("BTCUSDT")
        self.assertEqual(len(closed), 1)
        self.assertTrue(closed[0]["is_closed"])

    def test_get_ma(self):
        # Add some closed candles
        for i in range(5):
            k = {
                "t": i*1000, "T": (i+1)*1000, "o": str(100+i), "h": str(110+i), "l": str(90+i), "c": str(105+i), "v": "10", "n": 5, "x": True
            }
            self.store.update_kline("BTCUSDT", k)
        ma = self.store.get_ma("BTCUSDT", length=3)
        # MA of last 3 closes: 107+108+109 = 324 / 3 = 108
        self.assertAlmostEqual(ma, 108.0)

    def test_get_ma_no_data(self):
        ma = self.store.get_ma("NONEXIST")
        self.assertIsNone(ma)

    def test_get_ma_only_closed_false(self):
        k1 = {
            "t": 1000, "T": 2000, "o": "100", "h": "110", "l": "90", "c": "105", "v": "10", "n": 5, "x": True
        }
        k2 = {
            "t": 2000, "T": 3000, "o": "105", "h": "120", "l": "100", "c": "115", "v": "12", "n": 8, "x": False
        }
        self.store.update_kline("BTCUSDT", k1)
        self.store.update_kline("BTCUSDT", k2)
        ma = self.store.get_ma("BTCUSDT", length=2, only_closed=False)
        # Includes the open candle
        self.assertAlmostEqual(ma, (105 + 115) / 2)

if __name__ == '__main__':
    unittest.main()