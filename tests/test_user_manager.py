import unittest
import tempfile
import os
import json
from core.user_manager import UserManager

class TestUserManager(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.manager = UserManager(self.temp_file.name)

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_add_user(self):
        self.manager.add_user(123)
        users = self.manager.get_users()
        self.assertIn("123", users)
        self.assertEqual(users["123"]["config"]["kline"], "1m")

    def test_add_user_duplicate(self):
        self.manager.add_user(123)
        initial_version = self.manager.get_version()
        self.manager.add_user(123)
        # Version should not increase for duplicate
        self.assertEqual(self.manager.get_version(), initial_version)

    def test_update_config(self):
        self.manager.update_config(123, kline="5m", malength=20, log=1)
        users = self.manager.get_users()
        self.assertEqual(users["123"]["config"]["kline"], "5m")
        self.assertEqual(users["123"]["config"]["malength"], 20)
        self.assertEqual(users["123"]["config"]["log"], 1)

    def test_add_alert(self):
        self.manager.add_alert(123, "BTCUSDT", "percent", 1.0)
        users = self.manager.get_users()
        self.assertIn("BTCUSDT", users["123"]["coins"])
        self.assertEqual(len(users["123"]["coins"]["BTCUSDT"]), 1)
        self.assertEqual(users["123"]["coins"]["BTCUSDT"][0]["mode"], "percent")

    def test_add_alert_duplicate(self):
        self.manager.add_alert(123, "BTCUSDT", "percent", 1.0)
        initial_version = self.manager.get_version()
        self.manager.add_alert(123, "BTCUSDT", "percent", 1.0)
        # Version should not increase for duplicate
        self.assertEqual(self.manager.get_version(), initial_version)

    def test_remove_alert_whole_coin(self):
        self.manager.add_alert(123, "BTCUSDT", "percent", 1.0)
        result = self.manager.remove_alert(123, "BTCUSDT")
        self.assertTrue(result)
        users = self.manager.get_users()
        self.assertNotIn("BTCUSDT", users["123"]["coins"])

    def test_remove_alert_specific(self):
        self.manager.add_alert(123, "BTCUSDT", "percent", 1.0)
        self.manager.add_alert(123, "BTCUSDT", "usd", 100)
        result = self.manager.remove_alert(123, "BTCUSDT", "percent", 1.0)
        self.assertTrue(result)
        users = self.manager.get_users()
        self.assertEqual(len(users["123"]["coins"]["BTCUSDT"]), 1)
        self.assertEqual(users["123"]["coins"]["BTCUSDT"][0]["mode"], "usd")

    def test_remove_alert_not_found(self):
        result = self.manager.remove_alert(123, "NONEXIST")
        self.assertFalse(result)

    def test_load_save(self):
        self.manager.add_user(123)
        self.manager.save()
        # Create new manager to test load
        new_manager = UserManager(self.temp_file.name)
        users = new_manager.get_users()
        self.assertIn("123", users)

if __name__ == '__main__':
    unittest.main()