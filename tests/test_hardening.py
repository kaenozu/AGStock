import json
import os
import sys
import unittest
import unittest.mock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.helpers import retry_with_backoff
from src.schemas import AppConfig, load_config


class TestHardening(unittest.TestCase):
    def test_load_config_defaults(self):
        """設定ファイルが無い場合、デフォルト値がロードされるか"""
        config = load_config("non_existent_config.json")
        self.assertIsInstance(config, AppConfig)
        self.assertEqual(config.capital.initial_capital, 1000000.0)

    def test_load_config_valid(self):
        """有効な設定ファイルがロードされるか"""
        dummy_data = {"capital": {"initial_capital": 500.0}}
        with open("test_config.json", "w") as f:
            json.dump(dummy_data, f)

        try:
            config = load_config("test_config.json")
            self.assertEqual(config.capital.initial_capital, 500.0)
        finally:
            if os.path.exists("test_config.json"):
                os.remove("test_config.json")

    def test_retry_decorator(self):
        """リトライデコーレータが機能するか"""
        mock = unittest.mock.Mock()
        mock.side_effect = [Exception("Fail 1"), Exception("Fail 2"), "Success"]

        @retry_with_backoff(retries=3, backoff_in_seconds=0.1)
        def unreliable_func():
            return mock()

        result = unreliable_func()
        self.assertEqual(result, "Success")
        self.assertEqual(mock.call_count, 3)


if __name__ == "__main__":
    unittest.main()
