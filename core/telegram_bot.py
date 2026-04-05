import time
import requests
from core.command_handler import CommandHandler

import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN in .env")

class TelegramBot:
    def __init__(self, user_manager, price_store):
        self.offset = 0
        self.user_manager = user_manager
        self.price_store = price_store
        self.handler = CommandHandler(user_manager, price_store)

    def get_updates(self):
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        res = requests.get(url, params={"offset": self.offset, "timeout": 10})
        print("GET UPDATES:", res.text)
        return res.json()
    
    def send_menu(self, chat_id):
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        keyboard = {
            "keyboard": [
                ["➕ Add Alert", "🗑 Remove Alert"],
                ["📋 List", "📘 Help"]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }

        requests.post(url, json={
            "chat_id": chat_id,
            "reply_markup": keyboard
        })

    def send(self, chat_id, text):
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        res = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
        print("SEND:", res.text)

    def run(self):
        print("Telegram bot started...")
        while True:
            try:
                data = self.get_updates()

                for update in data.get("result", []):
                    print("UPDATE:", update)

                    self.offset = update["update_id"] + 1

                    if "message" not in update:
                        continue

                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "")

                    print("RECEIVED:", text)

                    reply = self.handler.handle(chat_id, text)

                    print("REPLY:", reply)

                    if reply:
                        self.send(chat_id, reply)

                    # 👇 show menu
                    self.send_menu(chat_id)

            except Exception as e:
                print("ERROR:", e)

            time.sleep(2)