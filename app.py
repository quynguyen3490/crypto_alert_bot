import threading
import time
import os
from dotenv import load_dotenv
load_dotenv()

from core.websocket_client import WebSocketClient
from core.telegram_bot import TelegramBot
from core.user_manager import UserManager


def main():
    user_manager = UserManager("config/users.json")

    ws_client = WebSocketClient(user_manager)
    telegram_bot = TelegramBot(user_manager)

    ws_thread = threading.Thread(target=ws_client.run, daemon=True)
    tg_thread = threading.Thread(target=telegram_bot.run, daemon=True)

    ws_thread.start()
    print("Starting WebSocket thread...")
    tg_thread.start()
    print("Starting Telegram thread...")

    while True:
        time.sleep(5)

if __name__ == "__main__":
    main()