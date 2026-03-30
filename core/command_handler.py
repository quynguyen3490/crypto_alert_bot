class CommandHandler:
    def __init__(self, user_manager):
        self.user_manager = user_manager

    
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

                "⚙️ *Ví dụ thực tế*\n"
                "Theo dõi BTC:\n"
                "- /add BTCUSDT percent 0.2\n"
                "- /add BTCUSDT usd 100\n"
                "- /add BTCUSDT price 70000\n\n"

                "💡 *Tip:*\n"
                "- Dùng percent nhỏ (0.1–0.5) để test\n"
                "- USD nhỏ (0.1–10) để thấy alert nhanh\n"
            )

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
        
        if parts[0] == "/config":
            if len(parts) == 3:
                config = parts[1].upper()
                value = parts[2]

                if config == "KLINE":
                    self.user_manager.update_config(chat_id, kline=value)
                
                if config == "MALENGTH":
                    self.user_manager.update_config(chat_id, malength=value)
                return f"✅ Update Config {config} to {value}"
            
            return "Usage:\n/config kline 15m\n/config malength 20"

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