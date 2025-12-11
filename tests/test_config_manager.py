"""config_manager.pyのユニットテスト"""

import json
import tempfile
import os
from pathlib import Path
import pytest
from src.config_manager import ConfigManager, TradingConfig
from src.errors import ConfigurationError


class TestTradingConfig:
    """TradingConfigのテスト"""
    
    def test_trading_config_initialization(self):
        """TradingConfigの初期化テスト"""
        config = TradingConfig(
            initial_capital=1000000.0,
            paper_trading_initial_capital=500000.0,
            risk_management={"daily_loss_limit_pct": -5.0},
            mini_stock={"enabled": True},
            backtest={"default_period": "2y"}
        )
        assert config.initial_capital == 1000000.0
        assert config.paper_trading_initial_capital == 500000.0
        assert config.risk_management == {"daily_loss_limit_pct": -5.0}
        assert config.mini_stock == {"enabled": True}
        assert config.backtest == {"default_period": "2y"}
    
    def test_trading_config_validation_valid_values(self):
        """TradingConfigの有効な値の検証テスト"""
        # 有効な値で初期化されることを確認
        config = TradingConfig(initial_capital=1000000.0, paper_trading_initial_capital=500000.0)
        assert config.initial_capital == 1000000.0
        assert config.paper_trading_initial_capital == 500000.0
    
    def test_trading_config_validation_invalid_initial_capital(self):
        """TradingConfigの無効な初期資本金の検証テスト"""
        with pytest.raises(ConfigurationError) as exc_info:
            TradingConfig(initial_capital=-1000.0)
        assert exc_info.value.config_key == "initial_capital"
        
        with pytest.raises(ConfigurationError) as exc_info:
            TradingConfig(initial_capital=0)
        assert exc_info.value.config_key == "initial_capital"
        
        with pytest.raises(ConfigurationError) as exc_info:
            TradingConfig(initial_capital="invalid")
        assert exc_info.value.config_key == "initial_capital"
    
    def test_trading_config_validation_invalid_paper_trading_capital(self):
        """TradingConfigの無効なペーパートレード初期資本金の検証テスト"""
        with pytest.raises(ConfigurationError) as exc_info:
            TradingConfig(initial_capital=1000000.0, paper_trading_initial_capital=-500000.0)
        assert exc_info.value.config_key == "paper_trading_initial_capital"


class TestConfigManager:
    """ConfigManagerのテスト"""
    
    def test_config_manager_initialization_with_default(self):
        """ConfigManagerの初期化とデフォルト値のテスト"""
        # 無効なパスで初期化（デフォルト設定が使用される）
        manager = ConfigManager(config_path="nonexistent_config.json")
        config = manager.load_config()
        
        assert isinstance(config, TradingConfig)
        assert config.initial_capital == 1000000.0
        assert config.paper_trading_initial_capital == 1000000.0
    
    def test_config_manager_with_valid_config_file(self):
        """有効な設定ファイルを使用したConfigManagerのテスト"""
        # 一時的な設定ファイルを作成
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            config_data = {
                "initial_capital": 2000000.0,
                "paper_trading": {
                    "initial_capital": 1500000.0
                },
                "risk_management": {
                    "daily_loss_limit_pct": -3.0
                }
            }
            json.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            manager = ConfigManager(config_path=temp_config_path)
            config = manager.load_config()
            
            assert config.initial_capital == 2000000.0
            assert config.paper_trading_initial_capital == 1500000.0
            assert config.risk_management["daily_loss_limit_pct"] == -3.0
        finally:
            # テンポラリファイルを削除
            os.unlink(temp_config_path)
    
    def test_config_manager_with_invalid_json(self):
        """無効なJSONファイルのテスト"""
        # 無効なJSONデータを持つ一時ファイルを作成
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("{ invalid json }")
            temp_config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                manager = ConfigManager(config_path=temp_config_path)
                manager.load_config()
            
            assert exc_info.value.config_key == "config_file"
        finally:
            # テンポラリファイルを削除
            os.unlink(temp_config_path)
    
    def test_config_manager_with_missing_required_key(self):
        """必須キーが欠落している設定ファイルのテスト"""
        # 初期資本金がない設定ファイルを作成
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            config_data = {
                "paper_trading": {
                    "initial_capital": 1500000.0
                }
            }
            json.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                manager = ConfigManager(config_path=temp_config_path)
                manager.load_config()
            
            assert exc_info.value.config_key == "initial_capital"
        finally:
            # テンポラリファイルを削除
            os.unlink(temp_config_path)
    
    def test_config_manager_get_method(self):
        """ConfigManagerのgetメソッドのテスト"""
        manager = ConfigManager(config_path="nonexistent_config.json")
        
        # 存在するキーの取得
        initial_capital = manager.get("initial_capital")
        assert initial_capital == 1000000.0
        
        # 存在しないキーの取得（デフォルト値）
        nonexistent = manager.get("nonexistent_key", "default_value")
        assert nonexistent == "default_value"
    
    def test_config_manager_get_nested_method(self):
        """ConfigManagerのget_nestedメソッドのテスト"""
        manager = ConfigManager(config_path="nonexistent_config.json")
        
        # ネストされたキーの取得
        daily_loss_limit = manager.get_nested("risk_management.daily_loss_limit_pct")
        assert daily_loss_limit == -5.0  # デフォルト値
        
        # 存在しないネストされたキーの取得（デフォルト値）
        nonexistent = manager.get_nested("nonexistent.nested.key", "default_value")
        assert nonexistent == "default_value"
    
    def test_config_manager_update_config(self):
        """ConfigManagerの設定更新のテスト"""
        manager = ConfigManager(config_path="nonexistent_config.json")
        
        # 設定を更新
        new_config = {"initial_capital": 3000000.0}
        manager.update_config(new_config)
        
        # 更新された値を確認
        updated_capital = manager.get("initial_capital")
        assert updated_capital == 3000000.0
    
    def test_config_manager_update_config_validation(self):
        """ConfigManagerの設定更新時の検証テスト"""
        manager = ConfigManager(config_path="nonexistent_config.json")
        
        # 無効な値で設定を更新しようとするとエラーになることを確認
        invalid_config = {"initial_capital": -1000.0}
        
        with pytest.raises(ConfigurationError):
            manager.update_config(invalid_config)
    
    def test_config_manager_save_config(self):
        """ConfigManagerの設定保存のテスト"""
        manager = ConfigManager(config_path="nonexistent_config.json")
        
        # 新しい設定を作成して保存
        new_config = {"initial_capital": 2500000.0, "test_key": "test_value"}
        manager.update_config(new_config)
        
        # 一時的な保存先を作成
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            temp_save_path = f.name
        
        try:
            manager.save_config(output_path=temp_save_path)
            
            # 保存されたファイルを読み込んで確認
            with open(temp_save_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            assert saved_data["initial_capital"] == 2500000.0
            assert saved_data["test_key"] == "test_value"
        finally:
            # テンポラリファイルを削除
            os.unlink(temp_save_path)
    
    def test_config_manager_save_config_error(self):
        """ConfigManagerの設定保存エラーのテスト"""
        manager = ConfigManager(config_path="nonexistent_config.json")
        
        # アクセス不可なパスに保存しようとするとエラーになることを確認
        invalid_path = "/invalid/path/config.json"
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.save_config(output_path=invalid_path)
        
        assert exc_info.value.config_key == "config_save"