import json
import threading

DEFAULT_KLINE = "1m"
DEFAULT_MALENGTH = 14
DEFAULT_CHART = 50
DEFAULT_LOG = 0

class UserManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.lock = threading.Lock()
        self.version = 0
        self.users = {}
        self.load()

    def load(self):
        try:
            with open(self.file_path, "r") as f:
                self.users = json.load(f)
        except:
            self.users = {}

    def save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.users, f, indent=2)
        self.version += 1

    def get_version(self):
        return self.version

    def add_user(self, chat_id):
        with self.lock:
            if str(chat_id) not in self.users:
                self.users[str(chat_id)] = {
                    "config": {"kline":DEFAULT_KLINE, "malength":DEFAULT_MALENGTH, "log": DEFAULT_LOG, "chart": DEFAULT_CHART},
                    "coins": {}
                }
                self.save()

    def get_users(self):
        return self.users

    def update_user(self, chat_id, data):
        with self.lock:
            self.users[str(chat_id)].update(data)
            self.save()

    def add_coin(self, chat_id, symbol):
        with self.lock:
            user = self.users[str(chat_id)]
            if symbol not in user["coins"]:
                user["coins"].append(symbol)
                self.save()

    def remove_coin(self, chat_id, symbol):
        with self.lock:
            user = self.users[str(chat_id)]
            if symbol in user["coins"]:
                user["coins"].remove(symbol)
                self.save()
    
    def get_config(self, chat_id, config=None):
        u_config = self.users.setdefault(str(chat_id), {"config": {}})

        kline = str(u_config.get("kline", DEFAULT_KLINE))
        malength = int(u_config.get("malength", DEFAULT_MALENGTH))
        log = u_config.get("log", DEFAULT_LOG)
        chart = u_config.get("chart", DEFAULT_CHART)
        
        if config is None:
            return u_config

        if config == "kline":
            return kline
        if config == "malength":
            return malength
        if config == "log":
            return log
        if config == "chart":
            return chart

    def update_config(self, chat_id, config=None, value=None):
        with self.lock: 
            user = self.users.setdefault(str(chat_id), {"config": {}})

            u_config = user.setdefault("config", {})
            
            if config.upper() == "KLINE":
                u_config["kline"] = str(value)
            
            if config.upper() == "MA":
                u_config["malength"] = int(value)
            
            if config.upper() == "LOG":
                u_config["log"] = int(value)

            if config.upper() == "CHART":
                u_config["chart"] = int(value)
            
            self.version += 1
            self.save()

    def add_alert(self, chat_id, symbol, mode, threshold):
        with self.lock:
            #add config default
            if str(chat_id) not in self.users:
                self.users[str(chat_id)] = {
                    "config": {"kline":DEFAULT_KLINE, "malength":DEFAULT_MALENGTH},
                    "coins": {}
                }

            user = self.users.setdefault(str(chat_id), {"coins": {}})

            coins = user.setdefault("coins", {})
            alerts = coins.setdefault(symbol, [])

            # tránh duplicate
            for a in alerts:
                if a["mode"] == mode and a["threshold"] == threshold:
                    return

            alerts.append({
                "mode": mode,
                "threshold": threshold
            })

            self.version += 1
            self.save()
    
    def remove_coin(self, chat_id, symbol):
        with self.lock:
            user = self.users.get(str(chat_id), {})
            coins = user.get("coins", {})

            if symbol in coins:
                del coins[symbol]
                self.version += 1
                self.save()

    def remove_alert(self, chat_id, symbol, mode=None, threshold=None):
        with self.lock:
            user = self.users.get(str(chat_id))
            if not user:
                return False

            coins = user.get("coins", {})

            if symbol not in coins:
                return False

            # 🔥 CASE 1: remove whole coin
            if mode is None:
                del coins[symbol]
                self.version += 1
                self.save()
                return True

            # 🔥 CASE 2: remove specific alert
            alerts = coins[symbol]

            new_alerts = [
                a for a in alerts
                if not (a["mode"] == mode and a["threshold"] == threshold)
            ]

            if len(new_alerts) == len(alerts):
                return False  # không tìm thấy

            if new_alerts:
                coins[symbol] = new_alerts
            else:
                # nếu không còn alert → xoá luôn coin
                del coins[symbol]

            self.version += 1
            self.save()
            return True