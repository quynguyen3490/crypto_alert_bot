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
        try:
            res = requests.get(url, params={"offset": self.offset, "timeout": 30, "limit": 50}, timeout=35)
            res.raise_for_status()
            print("GET UPDATES:", res.text)
            return res.json()
        except requests.exceptions.RequestException as e:
            print("GET UPDATES ERROR:", e)
            return {}
        except ValueError as e:
            print("GET UPDATES JSON ERROR:", e)
            return {}

    def send(self, chat_id, text):
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        try:
            res = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=15)
            print("SEND:", res.text)
        except requests.exceptions.RequestException as e:
            print("SEND ERROR:", e)

    def send_photo(self, chat_id, photo_bytes, caption=""):
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            files = {'photo': ('chart.png', photo_bytes, 'image/png')}
            data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
            res = requests.post(url, files=files, data=data, timeout=10)
            print("SEND PHOTO:", res.text)
        except Exception as e:
            print("SEND PHOTO ERROR:", e)

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

                    if not text:
                        continue

                    print("RECEIVED:", text)

                    reply = self.handler.handle(chat_id, text)

                    print("REPLY:", reply)

                    if reply:
                        if reply.startswith("CHART:"):
                            symbol = reply.split(":", 1)[1]
                            chart_bytes = self.handler.generate_chart(symbol)
                            self.send_photo(chat_id, chart_bytes, caption=f"📊 Chart for {symbol}")
                        else:
                            self.send(chat_id, reply)

            except Exception as e:
                print("ERROR:", e)

            time.sleep(2)