"""
Verify UI Logic Headless
Streamlitをモックして、render_moe_cockpit() がエラーなく動作するか検証する
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# モックのセットアップ
sys.modules["streamlit"] = MagicMock()
import streamlit as st

# パスの追加
sys.path.insert(0, os.getcwd())

# テスト対象のインポート
from src.auto_trader_ui import render_moe_cockpit


class TestAutoTraderUI(unittest.TestCase):
    def test_render_moe_cockpit_runs_without_error(self):
        print("🧪 Testing render_moe_cockpit logic...")
        try:
            # 関数実行
            render_moe_cockpit()
            print("✅ render_moe_cockpit executed successfully.")
        except Exception as e:
            self.fail(f"render_moe_cockpit raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
