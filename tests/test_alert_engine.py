import unittest
from core.alert_engine import AlertEngine

class TestAlertEngine(unittest.TestCase):
    def setUp(self):
        self.engine = AlertEngine()

    def test_format_price(self):
        self.assertEqual(self.engine.format_price(1000), "1,000.00")
        self.assertEqual(self.engine.format_price(1.234), "1.234")
        self.assertEqual(self.engine.format_price(0.01234), "0.0123")
        self.assertEqual(self.engine.format_price(0.000123), "0.000123")
        self.assertEqual(self.engine.format_price(0.00001234), "0.00001234")

    def test_format_percent(self):
        self.assertEqual(self.engine.format_percent(1.234), "1.23%")

    def test_format_usd(self):
        self.assertEqual(self.engine.format_usd(1234.56), "1,234.56$")

    def test_check_percent_trigger(self):
        result = self.engine.check("BTCUSDT", 100, 101, "percent", 1.0)
        self.assertIn("BTCUSDT", result)
        self.assertIn("1.00%", result)

    def test_check_percent_no_trigger(self):
        result = self.engine.check("BTCUSDT", 100, 100.5, "percent", 1.0)
        self.assertIsNone(result)

    def test_check_usd_trigger(self):
        result = self.engine.check("BTCUSDT", 100, 110, "usd", 5.0)
        self.assertIn("BTCUSDT", result)
        self.assertIn("10.00$", result)

    def test_check_usd_no_trigger(self):
        result = self.engine.check("BTCUSDT", 100, 102, "usd", 5.0)
        self.assertIsNone(result)

    def test_check_price_break_up(self):
        result = self.engine.check("BTCUSDT", 100, 105, "price", 102)
        self.assertIn("BREAK UP", result)

    def test_check_price_break_down(self):
        result = self.engine.check("BTCUSDT", 100, 95, "price", 98)
        self.assertIn("BREAK DOWN", result)

    def test_check_price_no_trigger(self):
        result = self.engine.check("BTCUSDT", 100, 101, "price", 105)
        self.assertIsNone(result)

    def test_check_prev_none(self):
        result = self.engine.check("BTCUSDT", None, 100, "percent", 1.0)
        self.assertIsNone(result)

    def test_check_price_no_retrigger_up(self):
        # First trigger
        result1 = self.engine.check("BTCUSDT", 100, 105, "price", 102)
        self.assertIsNotNone(result1)
        # Second call should not trigger again
        result2 = self.engine.check("BTCUSDT", 103, 104, "price", 102)
        self.assertIsNone(result2)

    def test_check_price_no_retrigger_down(self):
        # First trigger
        result1 = self.engine.check("BTCUSDT", 100, 95, "price", 98)
        self.assertIsNotNone(result1)
        # Second call should not trigger again
        result2 = self.engine.check("BTCUSDT", 97, 96, "price", 98)
        self.assertIsNone(result2)

if __name__ == '__main__':
    unittest.main()