import json
import pandas as pd
import mplfinance as mpf
import io

class CommandHandler:
    def __init__(self, user_manager, price_store):
        self.user_manager = user_manager
        self.price_store = price_store

    def format_help(self):
        return (
                "📘 *Crypto Alert Bot Guide*\n\n"

                "🚀 *1. Khởi tạo*\n"
                "/start → đăng ký bot\n\n"

                "➕ *2. Thêm alert*\n"
                "/add SYMBOL MODE VALUE\n\n"

                "Ví dụ:\n"
                "/add BTCUSDT percent 0.3\n"
                "/add BTCUSDT usd 50\n"
                "/add BTCUSDT price 70000\n\n"

                "📊 *Mode:*\n"
                "- percent → % thay đổi\n"
                "- usd → thay đổi theo USD\n"
                "- price → chạm giá\n\n"

                "🗑 *3. Xoá alert*\n"
                "/remove BTCUSDT → xoá toàn bộ coin\n"
                "/remove BTCUSDT usd 50 → xoá 1 alert\n\n"

                "📋 *4. Xem config*\n"
                "/list\n\n"

                "📊 *5. Xem chart*\n"
                "/chart SYMBOL\n\n"

                "Ví dụ:\n"
                "/chart BTCUSDT\n\n"

                "⚙️ *Ví dụ thực tế*\n"
                "Theo dõi BTC:\n"
                "- /add BTCUSDT percent 0.2\n"
                "- /add BTCUSDT usd 100\n"
                "- /add BTCUSDT price 70000\n\n"

                "💡 *Tip:*\n"
                "- Dùng percent nhỏ (0.1–0.5) để test\n"
                "- USD nhỏ (0.1–10) để thấy alert nhanh\n"
            )

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

    def format_price(self, price):
        if price >= 1000:
            return f"{price:,.2f}"     # 67,123.45
        elif price >= 1:
            return f"{price:,.3f}"     # 123.456
        elif price >= 0.01:
            return f"{price:,.4f}"     # 0.1234
        elif price >= 0.0001:
            return f"{price:,.6f}"     # 0.000123
        else:
            return f"{price:,.8f}"     # 0.00001234
        
    def format_candle(self, symbol, candle):
        return (
            f"*{symbol}*\n"
            f"Open: {self.format_price(candle['open'])}\n"
            f"High: {self.format_price(candle['high'])}\n"
            f"Low: {self.format_price(candle['low'])}\n"
            f"Close: {self.format_price(candle['close'])}\n"
            f"Volume: {self.format_price(candle['volume'])}"
        )

    def format_list(self, chat_id):
        user = self.user_manager.get_users().get(str(chat_id))

        if not user or not user.get("coins"):
            return "📭 No alerts yet.\n\nUse /add to create one."

        result = "📋 Your Alerts\n\n"

        coins = user.get("coins", {})

        for symbol, alerts in coins.items():
            result += f"🪙 {symbol}\n"

            for a in alerts:
                mode = a["mode"]
                value = a["threshold"]

                if mode == "percent":
                    result += f"  • percent ≥ {value}%\n"
                elif mode == "usd":
                    result += f"  • usd ≥ {value}$\n"
                elif mode == "price":
                    result += f"  • price = {self.format_price(value)}\n"

            result += "\n"

        return result.strip()

    def handle(self, chat_id, text):
        parts = text.split()

        if text == "📘 Help":
            return self.format_help()

        if text == "📋 List":
            
            return self.format_list(chat_id)

        if text == "➕ Add Alert":
            return (
                "➕ Add Alert\n\n"
                "Format:\n"
                "/add SYMBOL MODE VALUE\n\n"
                "Ví dụ:\n"
                "/add BTCUSDT percent 0.3"
            )

        if text == "🗑 Remove Alert":
            return (
                "🗑 Remove Alert\n\n"
                "Format:\n"
                "/remove SYMBOL\n"
                "/remove SYMBOL MODE VALUE\n\n"
                "Ví dụ:\n"
                "/remove BTCUSDT usd 50"
            )

        if text == "📊 Chart":
            return (
                "📊 Chart\n\n"
                "Format:\n"
                "/chart SYMBOL\n\n"
                "Ví dụ:\n"
                "/chart BTCUSDT"
            )

        if parts[0] == "/start":
            self.user_manager.add_user(chat_id)
            return "✅ Registered\n\nChọn menu bên dưới 👇"

        if parts[0] == "/add":
            if len(parts) == 4:
                symbol = parts[1].upper()
                mode = parts[2]
                value = float(parts[3])

                self.user_manager.add_alert(chat_id, symbol, mode, value)
                return f"✅ Added {symbol} {mode} {value}"
            
            return "Usage:\n/add BTCUSDT usd 100\n/add BTCUSDT percent 2\n/add BTCUSDT price 90000"

        if parts[0] == "/get":
            user = self.user_manager.get_users().get(str(chat_id))
            coins = user.get("coins") if user else None

            if len(parts) == 1:
                if not self.price_store.data:
                    return "❌ No candle data available yet."

                result_lines = ["📈 Latest candle(s):"]
                for symbol in sorted(self.price_store.data.keys()):
                    if symbol not in coins:
                        continue
                    candle = self.price_store.get_latest(symbol)

                    if candle:
                        result_lines.append(self.format_candle(symbol, candle))

                return "\n\n".join(result_lines)

            if len(parts) == 2:
                symbol = parts[1].upper()
                if symbol not in coins:
                    return f"❌ You don't have alerts for {symbol}"
                candle = self.price_store.get_latest(symbol)
                if not candle:
                    return f"❌ No candle for {symbol}"

                return self.format_candle(symbol, candle)

            return "Usage:\n/get\n/get BTCUSDT"
        
        if parts[0] == "/chart":
            if len(parts) == 2:
                symbol = parts[1].upper()
                if not self.price_store.get_all(symbol):
                    return f"❌ No data for {symbol}"
                # Return special indicator for chart
                return f"CHART:{symbol}"
            return "Usage:\n/chart BTCUSDT"
        
        if parts[0] == "/config":
            # Check argument count first for better flow
            if len(parts) != 3:
                return "Usage:\n/config kline 15m\n/config malength 20\n/config log 1"
    
            config = parts[1].upper()
            value = parts[2]

            # Map config names to their corresponding attributes
            config_map = {
                "KLINE": ("kline",),
                "MA": ("malength",),
                "LOG": ("log",),
                "CHART": ("chart",)
            }
    
            if config in config_map:
                # Validate value based on config type
                valid = False
        
                if config == "KLINE":
                    # kline must be string ending with "m" (e.g., "15m", "30m")
                    if isinstance(value, str) and value.endswith("m"):
                        try:
                            int(value[:-1])  # Check numeric part is valid integer
                            valid = True
                        except ValueError:
                            pass
        
                elif config == "MA":
                    # malength must be an integer
                    try:
                        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
                            int_value = int(value)
                            if 1 <= int_value <= 200:  # Reasonable range for MA length
                                valid = True
                    except ValueError:
                        pass
        
                elif config == "LOG":
                    # log must be only integer 1 or 0
                    try:
                        if value in ("1", "0"):
                            valid = True
                    except ValueError:
                        pass
                
                elif config == "CHART":
                    # chart must be only integer 1 or 0
                    try:
                        if value > 0 and value <= 100:
                            valid = True
                    except ValueError:
                        pass
        
                if not valid:
                    return f"Invalid {config} value '{value}'.\n" \
                            f"KLINE: string ending with 'm' (e.g., 15m, 30m)\n" \
                            f"MA: integer between 1-200\n" \
                            f"LOG: 1 or 0\n" \
                            f"CHART: integer between 1-100"
        
                self.user_manager.update_config(chat_id, **{config_map[config][0]: value})
                return f"✅ Update Config {config} to {value}"
    
            # Optional: handle unknown configs
            return f"Unknown config type '{config}'. Valid options: KLINE, MA, LOG"

        if parts[0] == "/remove":
            if len(parts) == 2:
                symbol = parts[1].upper()

                ok = self.user_manager.remove_alert(chat_id, symbol)

                return f"🗑 Removed {symbol}" if ok else "❌ Not found"

            elif len(parts) >= 4:
                symbol = parts[1].upper()
                mode = parts[2]
                value = float(parts[3])

                ok = self.user_manager.remove_alert(chat_id, symbol, mode, value)

                return f"🗑 Removed {symbol} {mode} {value}" if ok else "❌ Not found"

            return "Usage:\n/remove BTCUSDT\n/remove BTCUSDT usd 1"


        if parts[0] == "/list":
            return self.format_list(chat_id)
        
        if parts[0] == "/help":
            return self.format_help()

        return "❓ Unknown command\n\nGõ /help để xem hướng dẫn"