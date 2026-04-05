import threading
import time
import os
from dotenv import load_dotenv
load_dotenv()

from core.websocket_client import WebSocketClient
from core.telegram_bot import TelegramBot
from core.user_manager import UserManager
from core.price_store import PriceStore


def main():
    user_manager = UserManager("config/users.json")
    price_store = PriceStore()

    ws_client = WebSocketClient(user_manager, price_store)
    telegram_bot = TelegramBot(user_manager, price_store)

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