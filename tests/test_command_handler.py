import unittest
from unittest.mock import Mock, MagicMock
from core.command_handler import CommandHandler

class TestCommandHandler(unittest.TestCase):
    def setUp(self):
        self.user_manager = Mock()
        self.price_store = Mock()
        self.handler = CommandHandler(self.user_manager, self.price_store)

    def test_format_help(self):
        result = self.handler.format_help()
        self.assertIn("Crypto Alert Bot Guide", result)
        self.assertIn("/add", result)
        self.assertIn("/remove", result)

    def test_format_price(self):
        self.assertEqual(self.handler.format_price(1000), "1,000.00")
        self.assertEqual(self.handler.format_price(1.234), "1.234")
        self.assertEqual(self.handler.format_price(0.01234), "0.0123")
        self.assertEqual(self.handler.format_price(0.000123), "0.000123")
        self.assertEqual(self.handler.format_price(0.00001234), "0.00001234")

    def test_format_candle(self):
        candle = {
            'open': 50000,
            'high': 51000,
            'low': 49000,
            'close': 50500,
            'volume': 100.5
        }
        result = self.handler.format_candle("BTCUSDT", candle)
        self.assertIn("BTCUSDT", result)
        self.assertIn("50,000.00", result)
        self.assertIn("51,000.00", result)

    def test_format_list_no_alerts(self):
        self.user_manager.get_users.return_value = {}
        result = self.handler.format_list(123)
        self.assertIn("No alerts yet", result)

    def test_format_list_with_alerts(self):
        self.user_manager.get_users.return_value = {
            "123": {
                "coins": {
                    "BTCUSDT": [
                        {"mode": "percent", "threshold": 0.5},
                        {"mode": "usd", "threshold": 100}
                    ]
                }
            }
        }
        result = self.handler.format_list(123)
        self.assertIn("BTCUSDT", result)
        self.assertIn("percent ≥ 0.5%", result)
        self.assertIn("usd ≥ 100$", result)

    def test_handle_start(self):
        result = self.handler.handle(123, "/start")
        self.user_manager.add_user.assert_called_with(123)
        self.assertIn("Registered", result)

    def test_handle_add_valid(self):
        result = self.handler.handle(123, "/add BTCUSDT percent 0.5")
        self.user_manager.add_alert.assert_called_with(123, "BTCUSDT", "percent", 0.5)
        self.assertIn("Added BTCUSDT percent 0.5", result)

    def test_handle_add_invalid(self):
        result = self.handler.handle(123, "/add BTCUSDT")
        self.assertIn("Usage:", result)

    def test_handle_remove_symbol(self):
        self.user_manager.remove_alert.return_value = True
        result = self.handler.handle(123, "/remove BTCUSDT")
        self.user_manager.remove_alert.assert_called_with(123, "BTCUSDT")
        self.assertIn("Removed BTCUSDT", result)

    def test_handle_remove_specific(self):
        self.user_manager.remove_alert.return_value = True
        result = self.handler.handle(123, "/remove BTCUSDT usd 100")
        self.user_manager.remove_alert.assert_called_with(123, "BTCUSDT", "usd", 100.0)
        self.assertIn("Removed BTCUSDT usd 100", result)

    def test_handle_get_all(self):
        self.price_store.data = {"BTCUSDT": []}
        self.price_store.get_latest.return_value = {
            'open': 50000, 'high': 51000, 'low': 49000, 'close': 50500, 'volume': 100
        }
        result = self.handler.handle(123, "/get")
        self.assertIn("Latest candle", result)

    def test_handle_get_symbol(self):
        self.price_store.get_latest.return_value = {
            'open': 50000, 'high': 51000, 'low': 49000, 'close': 50500, 'volume': 100
        }
        result = self.handler.handle(123, "/get BTCUSDT")
        self.assertIn("BTCUSDT", result)

    def test_handle_config_kline(self):
        result = self.handler.handle(123, "/config kline 15m")
        self.user_manager.update_config.assert_called_with(123, kline="15m")
        self.assertIn("Update Config KLINE to 15m", result)

    def test_handle_config_ma(self):
        result = self.handler.handle(123, "/config ma 20")
        self.user_manager.update_config.assert_called_with(123, malength="20")
        self.assertIn("Update Config MA to 20", result)

    def test_handle_config_log(self):
        result = self.handler.handle(123, "/config log 1")
        self.user_manager.update_config.assert_called_with(123, log="1")
        self.assertIn("Update Config LOG to 1", result)

    def test_handle_unknown(self):
        result = self.handler.handle(123, "/unknown")
        self.assertIn("Unknown command", result)

if __name__ == '__main__':
    unittest.main()