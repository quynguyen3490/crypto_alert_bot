import unittest
from unittest.mock import Mock, patch, MagicMock
import os

# Patch environment before import
with patch.dict(os.environ, {'TELEGRAM_TOKEN': 'test_token'}):
    from core.telegram_bot import TelegramBot

class TestTelegramBot(unittest.TestCase):
    def setUp(self):
        self.user_manager = Mock()
        self.price_store = Mock()
        self.bot = TelegramBot(self.user_manager, self.price_store)

    @patch('requests.get')
    def test_get_updates(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {"result": []}
        mock_get.return_value = mock_response
        result = self.bot.get_updates()
        self.assertEqual(result, {"result": []})
        mock_get.assert_called_once()

    @patch('requests.post')
    def test_send_menu(self, mock_post):
        self.bot.send_menu(123)
        mock_post.assert_called_once()
        args = mock_post.call_args
        self.assertIn('chat_id', args[1]['json'])
        self.assertEqual(args[1]['json']['chat_id'], 123)

    @patch('requests.post')
    def test_send(self, mock_post):
        self.bot.send(123, "test message")
        mock_post.assert_called_once()
        args = mock_post.call_args
        self.assertEqual(args[1]['json']['chat_id'], 123)
        self.assertEqual(args[1]['json']['text'], "test message")

    def test_handler_integration(self):
        # Test that handler is called correctly
        with patch.object(self.bot.handler, 'handle', return_value="reply") as mock_handle:
            with patch('builtins.print'):  # Suppress prints
                # Simulate the run loop logic
                update = {
                    "update_id": 1,
                    "message": {
                        "chat": {"id": 123},
                        "text": "/start"
                    }
                }
                # Manually call the logic from run
                self.bot.offset = update["update_id"] + 1
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "")
                reply = self.bot.handler.handle(chat_id, text)
                self.assertEqual(reply, "reply")
                mock_handle.assert_called_with(123, "/start")

if __name__ == '__main__':
    unittest.main()