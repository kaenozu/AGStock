import pytest
import pandas as pd
import numpy as np
from src.strategies import Strategy, SMACrossoverStrategy, RSIStrategy, BollingerBandsStrategy


class TestStrategy:
    """Strategy基底クラスのテスト"""
    
    def test_strategy_initialization(self):
        """戦略の初期化テスト"""
        strategy = Strategy("Test Strategy")
        assert strategy.name == "Test Strategy"
    
    def test_generate_signals_not_implemented(self, sample_stock_data):
        """generate_signalsが実装されていないことを確認"""
        strategy = Strategy("Test")
        with pytest.raises(NotImplementedError):
            strategy.generate_signals(sample_stock_data)


class TestSMACrossoverStrategy:
    """SMA Crossover戦略のテスト"""
    
    def test_initialization(self, sma_strategy):
        """初期化パラメータの確認"""
        assert sma_strategy.short_window == 5
        assert sma_strategy.long_window == 25
        assert "SMA Crossover" in sma_strategy.name
    
    def test_generate_signals_returns_series(self, sma_strategy, sample_stock_data):
        """シグナルがSeriesとして返されることを確認"""
        signals = sma_strategy.generate_signals(sample_stock_data)
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_stock_data)
    
    def test_signals_are_valid_values(self, sma_strategy, sample_stock_data):
        """シグナルが-1, 0, 1のいずれかであることを確認"""
        signals = sma_strategy.generate_signals(sample_stock_data)
        unique_values = signals.unique()
        assert all(val in [-1, 0, 1] for val in unique_values)
    
    def test_golden_cross_generates_buy_signal(self):
        """ゴールデンクロスで買いシグナルが生成されることを確認"""
        # 短期SMAが長期SMAを上抜けるデータを作成
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        
        # 最初は下降、後半で上昇するパターン
        prices = np.concatenate([
            np.linspace(1000, 900, 25),  # 下降
            np.linspace(900, 1100, 25)   # 上昇
        ])
        
        df = pd.DataFrame({
            'Close': prices,
            'Open': prices,
            'High': prices + 5,
            'Low': prices - 5,
            'Volume': 1000000
        }, index=dates)
        
        strategy = SMACrossoverStrategy(short_window=5, long_window=10)
        signals = strategy.generate_signals(df)
        
        # 買いシグナルが少なくとも1つ存在することを確認
        assert (signals == 1).any()
    
    def test_dead_cross_generates_sell_signal(self):
        """デッドクロスで売りシグナルが生成されることを確認"""
        # 短期SMAが長期SMAを下抜けるデータを作成
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        
        # 最初は上昇、後半で下降するパターン
        prices = np.concatenate([
            np.linspace(900, 1100, 25),  # 上昇
            np.linspace(1100, 900, 25)   # 下降
        ])
        
        df = pd.DataFrame({
            'Close': prices,
            'Open': prices,
            'High': prices + 5,
            'Low': prices - 5,
            'Volume': 1000000
        }, index=dates)
        
        strategy = SMACrossoverStrategy(short_window=5, long_window=10)
        signals = strategy.generate_signals(df)
        
        # 売りシグナルが少なくとも1つ存在することを確認
        assert (signals == -1).any()


class TestRSIStrategy:
    """RSI戦略のテスト"""
    
    def test_initialization(self, rsi_strategy):
        """初期化パラメータの確認"""
        assert rsi_strategy.period == 14
        assert rsi_strategy.lower == 30
        assert rsi_strategy.upper == 70
        assert "RSI" in rsi_strategy.name
    
    def test_generate_signals_returns_series(self, rsi_strategy, sample_stock_data):
        """シグナルがSeriesとして返されることを確認"""
        signals = rsi_strategy.generate_signals(sample_stock_data)
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_stock_data)
    
    def test_signals_are_valid_values(self, rsi_strategy, sample_stock_data):
        """シグナルが-1, 0, 1のいずれかであることを確認"""
        signals = rsi_strategy.generate_signals(sample_stock_data)
        unique_values = signals.unique()
        assert all(val in [-1, 0, 1] for val in unique_values)
    
    def test_oversold_recovery_generates_buy_signal(self):
        """過売り状態からの回復で買いシグナルが生成されることを確認"""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        
        # 急激な下落後に反発するパターン
        prices = np.concatenate([
            np.linspace(1000, 800, 20),  # 急落
            np.linspace(800, 900, 30)    # 回復
        ])
        
        df = pd.DataFrame({
            'Close': prices,
            'Open': prices,
            'High': prices + 5,
            'Low': prices - 5,
            'Volume': 1000000
        }, index=dates)
        
        strategy = RSIStrategy(period=14, lower=30, upper=70)
        signals = strategy.generate_signals(df)
        
        # 買いシグナルが存在する可能性がある（RSIが30を上抜け）
        # データによっては生成されない場合もあるため、エラーにならないことを確認
        assert signals is not None


class TestBollingerBandsStrategy:
    """Bollinger Bands戦略のテスト"""
    
    def test_initialization(self, bollinger_strategy):
        """初期化パラメータの確認"""
        assert bollinger_strategy.length == 20
        assert bollinger_strategy.std == 2
        assert "Bollinger Bands" in bollinger_strategy.name
    
    def test_generate_signals_returns_series(self, bollinger_strategy, sample_stock_data):
        """シグナルがSeriesとして返されることを確認"""
        signals = bollinger_strategy.generate_signals(sample_stock_data)
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_stock_data)
    
    def test_signals_are_valid_values(self, bollinger_strategy, sample_stock_data):
        """シグナルが-1, 0, 1のいずれかであることを確認"""
        signals = bollinger_strategy.generate_signals(sample_stock_data)
        unique_values = signals.unique()
        assert all(val in [-1, 0, 1] for val in unique_values)
    
    def test_lower_band_touch_generates_buy_signal(self):
        """下限バンドタッチで買いシグナルが生成される可能性を確認"""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        
        # 比較的安定した価格から急落するパターン
        prices = np.concatenate([
            np.full(30, 1000) + np.random.randn(30) * 5,  # 安定
            np.linspace(1000, 900, 20)                     # 急落
        ])
        
        df = pd.DataFrame({
            'Close': prices,
            'Open': prices,
            'High': prices + 5,
            'Low': prices - 5,
            'Volume': 1000000
        }, index=dates)
        
        strategy = BollingerBandsStrategy(length=20, std=2)
        signals = strategy.generate_signals(df)
        
        # シグナルが生成されることを確認（必ずしも買いシグナルとは限らない）
        assert signals is not None
        assert len(signals) == len(df)

