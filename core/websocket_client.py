import websocket
import json
import time
import threading
import requests
from datetime import datetime, timedelta
import io
import pandas as pd
import mplfinance as mpf

from core.price_store import PriceStore
from core.alert_engine import AlertEngine

import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN in .env")


class WebSocketClient:
    def __init__(self, user_manager, price_store):
        self.user_manager = user_manager
        self.price_store = price_store
        self.alert_engine = AlertEngine()

        self.ws = None
        self.current_version = -1
        self.ws_thread = None
        self.lock = threading.Lock()

    # =========================
    # BUILD STREAM
    # =========================
    def get_symbols(self):
        users = self.user_manager.get_users()
        symbols = set()

        for uid, u in users.items():
            coins = u.get("coins", {})
            kline = u.get("config", {}).get("kline", "15m")

            for s in coins.keys():
                symbols.add((s.lower(), kline))

        return list(symbols)

    def build_url(self):
        symbols = self.get_symbols()

        if not symbols:
            return None

        streams = [f"{s}@kline_{kline}" for s, kline in symbols]   # 🔥 đổi ở đây
        return f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
    # =========================
    # TELEGRAM
    # =========================

    def send_telegram(self, chat_id, text):
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            res = requests.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }, timeout=5)

            print("SEND:", res.text)
        except Exception as e:
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

    def generate_chart(self, symbol, num_candles=50):
        candles = self.price_store.get_all(symbol)
        if len(candles) < num_candles:
            num_candles = len(candles)
        recent_candles = candles[-num_candles:]
        
        # Convert to DataFrame
        df = pd.DataFrame(recent_candles)
        df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
        df['timestamp'] = df['timestamp'] + pd.Timedelta(hours=7)
        df.set_index('timestamp', inplace=True)
        df = df[['open', 'high', 'low', 'close', 'volume']]
        df = df.astype(float)
        
        # Create plot
        buf = io.BytesIO()
        mpf.plot(df, type='candle', volume=True, style='charles', savefig=dict(fname=buf, format='png', bbox_inches='tight'))
        buf.seek(0)
        return buf.getvalue()

    # =========================
    # FORMAT
    # =========================
    def format_price(self, price):
        if price >= 1000:
            return f"${price:,.2f}"
        elif price >= 1:
            return f"${price:,.3f}"
        elif price >= 0.01:
            return f"${price:,.4f}"
        elif price >= 0.0001:
            return f"${price:,.6f}"
        else:
            return f"{price:,.8f}"

    def format_percent(self, p):
        return f"{p:.2f}%"

    def format_usd(self, v):
        return f"${v:,.2f}"

    def trend_icon(self, prev, last):
        return "📈" if last > prev else "📉"

    def build_message(self, chat_id, symbol, prev, last, mode, value):
        kline, malength = self.user_manager.get_config(chat_id, "kline"), self.user_manager.get_config(chat_id, "malength")

        icon = self.trend_icon(prev, last)
        price_str = self.format_price(last)
        prev_str = self.format_price(prev)

        now = (datetime.utcnow() + timedelta(hours=7)).strftime("%H:%M:%S")

        idicator = "🔴" if (last - prev) <= 0 else "🟢"

        real_change = (last - prev)
        real_change_percent = (last - prev) / prev * 100

        if mode == "percent":
            return (
                f"{icon} *{symbol}* ({kline})\n"
                f"Price: *{price_str}*\n"
                f"Change: {idicator} *{self.format_percent(real_change_percent)}*\n"
                f"MA({malength}): {prev_str}\n"
                f"Time: {now}"
            )

        elif mode == "usd":
            return (
                f"{icon} *{symbol}* ({kline})\n"
                f"Price: *{price_str}*\n"
                f"Change: {idicator} *{self.format_usd(real_change)}*\n"
                f"MA({malength}): {prev_str}\n"
                f"Time: {now}"
            )

        elif mode == "price":
            direction = "🚀 BREAK UP" if last > prev else "🔻 BREAK DOWN"
            return (
                f"{direction} *{symbol}*\n ({kline})"
                f"Price: *{price_str}*\n"
                f"Target: {self.format_price(value)}\n"
                f"Time: {now}"
            )

    # =========================
    # WS CALLBACK
    # =========================
    def on_message(self, ws, message):
        try:      
            data = json.loads(message)
            payload = data.get("data", {})

            if payload.get("e") != "kline":
                return

            symbol = payload.get("s")
            k = payload.get("k")

            if not k:
                return

            candle = self.price_store.update_kline(symbol, k)

            # ❗ chỉ xử lý khi nến đóng
            if not candle["is_closed"]:
                return

            prev_candle = self.price_store.get_all(symbol)[-2] if len(self.price_store.get_all(symbol)) >= 2 else None

            if not prev_candle:
                return

            prev = prev_candle["close"]
            last = candle["close"]

            users = self.user_manager.get_users()

            for chat_id, user in users.items():    
                coins = user.get("coins", {})

                if symbol not in coins:
                    continue

                alerts = coins[symbol]

                malength = self.user_manager.get_config(chat_id, "malength")
                log = self.user_manager.get_config(chat_id, "log")
                chart = self.user_manager.get_config(chat_id, "chart")

                # get MA15
                ma = self.price_store.get_ma(symbol,malength)
                print(f"Debug MA {symbol}: {ma}")

                if log == 1:
                    if (last - prev) <= 0:
                        idicator = "🔴"
                    elif (last - prev) > 0:
                        idicator = "🟢"
                    self.send_telegram(chat_id, f"🗒️ Log: *{symbol}*\nLast: *{self.format_price(last)}*\nPrev: *{self.format_price(prev)}*\nChange: {idicator} *{self.format_price(abs(last - prev))}*\nMA({malength}): *{self.format_price(self.price_store.get_ma(symbol, malength))}*\nTime: {(datetime.utcnow() + timedelta(hours=7)).strftime('%H:%M:%S')}")

                for cfg in alerts:
                    mode = cfg["mode"]
                    threshold = cfg["threshold"]

                    triggered = self.alert_engine.check(
                        symbol, ma, last, mode, threshold
                    )

                    if triggered:
                        msg = self.build_message(
                            chat_id, symbol, ma, last, mode, threshold
                        )

                        chart_bytes = self.generate_chart(symbol, chart)
                        self.send_photo(chat_id, chart_bytes, caption=msg)

        except Exception as e:
            print("ON_MESSAGE ERROR:", e)

    def on_error(self, ws, error):
        print("WS ERROR:", error)

    def on_close(self, ws, close_status_code, close_msg):
        print("WS CLOSED")

    def on_open(self, ws):
        print("WS CONNECTED")

    # =========================
    # CONNECT
    # =========================
    def connect(self):
        url = self.build_url()

        if not url:
            print("No symbols → waiting...")
            time.sleep(2)
            return

        if self.ws_thread and self.ws_thread.is_alive():
            return

        print("Connecting:", url)

        self.ws = websocket.WebSocketApp(
            url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )

        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()
        time.sleep(1)

    # =========================
    # RUN LOOP
    # =========================
    def run(self):
        while True:
            try:
                version = self.user_manager.get_version()

                if version != self.current_version:
                    print("Config changed → reconnect WS")
                    self.current_version = version

                    if self.ws:
                        try:
                            self.ws.close()
                        except:
                            pass

                    if self.ws_thread:
                        self.ws_thread.join(timeout=5)

                    self.ws = None
                    self.ws_thread = None
                    time.sleep(1)

                self.connect()
                time.sleep(1)

            except Exception as e:
                print("WS LOOP ERROR:", e)
                time.sleep(5)
