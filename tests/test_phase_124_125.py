import pytest
import os
import json
from unittest.mock import MagicMock, patch
import pandas as pd

from src.agents.neuromancer import Neuromancer
from src.trading.fully_automated_trader import FullyAutomatedTrader
from src.ui.dashboard_router import DashboardRouter

class TestPhase124_125:
    
    def test_neuromancer_perception(self):
        """Neuromancerが市場データに応じて感情を変えるかテスト"""
        ai = Neuromancer()
        
        # Case 1: Panic (VIX > 30)
        market_data_panic = {"vix": 35.0, "daily_pnl": 0}
        msg = ai.perceive_world(market_data_panic)
        assert ai.indices.mood == "Panic"
        assert "ザワついています" in msg
        
        # Case 2: Excited (Profit > 5000)
        market_data_happy = {"vix": 15.0, "daily_pnl": 10000}
        msg = ai.perceive_world(market_data_happy)
        assert ai.indices.mood == "Excited"
        assert "素晴らしい流れ" in msg
        
        # Case 3: Idle Talk
        msg_idle = ai.respond_to_user("調子はどう？")
        assert f"気分は「{ai.indices.mood}」" in msg_idle

    def test_dashboard_router_tabs(self):
        """ダッシュボードのタブ構成が正しいかテスト"""
        tabs = DashboardRouter.get_tabs(signal_count=5)
        titles = [t[0] for t in tabs]
        
        # Neuromancerが含まれているか
        assert "🧠 Neuromancer" in titles
        # トレーディングに通知バッジがついているか
        assert any("トレーディング (5)" in t for t in titles)

    @patch('src.trading.fully_automated_trader.FullyAutomatedTrader.log')
    @patch('src.trading.fully_automated_trader.fetch_stock_data')
    @patch('src.trading.fully_automated_trader.PaperTrader') # Mock PaperTrader too
    def test_neural_link_injection(self, mock_pt, mock_fetch, mock_log):
        """Neural Linkがパラメータをロードするかテスト"""
        
        # ダミーの進化パラメータファイルを作成
        dummy_params = {
            "name": "Test_Genotype_Alpha",
            "rsi_period": 9,
            "bb_window": 15,
            "bb_dev": 1.5,
            "stop_loss_pct": 0.03,
            "take_profit_pct": 0.08,
            "fitness": 99.9
        }
        
        config_dir = "models/config"
        os.makedirs(config_dir, exist_ok=True)
        param_path = os.path.join(config_dir, "evolved_strategy_params.json")
        
        with open(param_path, "w") as f:
            json.dump(dummy_params, f)
            
        try:
            # Trader初期化
            trader = FullyAutomatedTrader()
            
            # scan_market実行（の中でロードが行われる）
            # データ取得をモックして空で返す
            mock_fetch.return_value = {}
            
            trader.scan_market()
            
            # ログを確認してロードされたか検証
            # logメソッドが "overriding with 'Test_Genotype_Alpha'" のようなメッセージを受け取ったか
            found_log = False
            for call in mock_log.call_args_list:
                args, _ = call
                if "Neural Link" in args[0] and "Test_Genotype_Alpha" in args[0]:
                    found_log = True
                    break
            
            assert found_log, "Neural Link activation log not found!"
            
        finally:
            # クリーンアップ
            if os.path.exists(param_path):
                os.remove(param_path)

