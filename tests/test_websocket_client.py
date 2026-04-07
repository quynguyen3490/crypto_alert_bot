import unittest
from unittest.mock import Mock, patch
import os

# Patch environment before import
with patch.dict(os.environ, {'TELEGRAM_TOKEN': 'test_token'}):
    from core.websocket_client import WebSocketClient

class TestWebSocketClient(unittest.TestCase):
    def setUp(self):
        self.user_manager = Mock()
        self.price_store = Mock()
        self.user_manager.get_users.return_value = {"1": {"config": {"kline": "1m", "malength": 14, "log": 0}}}
        self.client = WebSocketClient(self.user_manager, self.price_store)

    def test_get_symbols(self):
        self.user_manager.get_users.return_value = {
            "1": {"coins": {"BTCUSDT": [], "ETHUSDT": []}},
            "2": {"coins": {"BTCUSDT": []}}
        }
        symbols = self.client.get_symbols()
        self.assertIn(("btcusdt", "15m"), symbols)
        self.assertIn(("ethusdt", "15m"), symbols)

    def test_format_price(self):
        self.assertEqual(self.client.format_price(1000), "$1,000.00")
        self.assertEqual(self.client.format_price(1.234), "$1.234")
        self.assertEqual(self.client.format_price(0.01234), "$0.0123")

    def test_format_percent(self):
        self.assertEqual(self.client.format_percent(1.234), "1.23%")

    def test_format_usd(self):
        self.assertEqual(self.client.format_usd(1234.56), "$1,234.56")

    def test_trend_icon(self):
        self.assertEqual(self.client.trend_icon(100, 105), "📈")
        self.assertEqual(self.client.trend_icon(105, 100), "📉")

    def test_build_message_percent(self):
        msg = self.client.build_message("1", "BTCUSDT", 100, 101, "percent", 1.0)
        self.assertIn("BTCUSDT", msg)
        self.assertIn("1.00%", msg)

    def test_build_message_usd(self):
        msg = self.client.build_message("1", "BTCUSDT", 100, 110, "usd", 5.0)
        self.assertIn("BTCUSDT", msg)
        self.assertIn("$10.00", msg)

    def test_build_message_price(self):
        msg = self.client.build_message("1", "BTCUSDT", 100, 105, "price", 102)
        self.assertIn("BREAK UP", msg)

    @patch('requests.post')
    def test_send_telegram(self, mock_post):
        mock_response = Mock()
        mock_response.text = "ok"
        mock_post.return_value = mock_response
        self.client.send_telegram(123, "test")
        mock_post.assert_called_once()

    # Note: generate_chart and send_photo are harder to test without mocking mplfinance and io

if __name__ == '__main__':
    unittest.main()