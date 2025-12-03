import pandas as pd
import numpy as np
from src.backtester import Backtester
from src.strategies import SMACrossoverStrategy


class TestBacktester:
    """Backtesterクラスのテスト"""
    
    def test_initialization(self):
        """初期資金の設定を確認"""
        backtester = Backtester(initial_capital=1000000)
        assert backtester.initial_capital == 1000000
    
    def test_default_initial_capital(self):
        """デフォルトの初期資金を確認"""
        backtester = Backtester()
        assert backtester.initial_capital == 100000  # Updated from 1000000
    
    def test_run_returns_dict(self, backtester, sample_stock_data, sma_strategy):
        """runメソッドが辞書を返すことを確認"""
        result = backtester.run(sample_stock_data, sma_strategy)
        assert isinstance(result, dict)
    
    def test_run_result_contains_required_keys(self, backtester, sample_stock_data, sma_strategy):
        """結果に必要なキーが含まれることを確認"""
        result = backtester.run(sample_stock_data, sma_strategy)
        
        required_keys = ['total_return', 'final_value', 'signals', 'positions', 'equity_curve']
        for key in required_keys:
            assert key in result
    
    def test_run_with_empty_dataframe(self, backtester, empty_dataframe, sma_strategy):
        """空のデータフレームでNoneを返すことを確認"""
        result = backtester.run(empty_dataframe, sma_strategy)
        assert result is None
    
    def test_run_with_none_dataframe(self, backtester, sma_strategy):
        """Noneのデータフレームで適切に処理することを確認"""
        result = backtester.run(None, sma_strategy)
        assert result is None
    
    def test_total_return_is_numeric(self, backtester, sample_stock_data, sma_strategy):
        """total_returnが数値であることを確認"""
        result = backtester.run(sample_stock_data, sma_strategy)
        assert isinstance(result['total_return'], (int, float, np.number))
    
    def test_final_value_calculation(self, backtester, sample_stock_data, sma_strategy):
        """final_valueが正しく計算されることを確認"""
        result = backtester.run(sample_stock_data, sma_strategy)
        
        expected_final_value = backtester.initial_capital * (1 + result['total_return'])
        assert abs(result['final_value'] - expected_final_value) < 0.01
    
    def test_signals_length_matches_data(self, backtester, sample_stock_data, sma_strategy):
        """シグナルの長さがデータと一致することを確認"""
        result = backtester.run(sample_stock_data, sma_strategy)
        assert len(result['signals']) == len(sample_stock_data)
    
    def test_positions_length_matches_data(self, backtester, sample_stock_data, sma_strategy):
        """ポジションの長さがデータと一致することを確認"""
        result = backtester.run(sample_stock_data, sma_strategy)
        assert len(result['positions']) == len(sample_stock_data)
    
    def test_positions_are_binary(self, backtester, sample_stock_data, sma_strategy):
        """ポジションが0または1であることを確認"""
        result = backtester.run(sample_stock_data, sma_strategy)
        positions = result['positions']
        assert all(pos in [0, 1] for pos in positions.unique())
    
    def test_equity_curve_is_series(self, backtester, sample_stock_data, sma_strategy):
        """equity_curveがSeriesであることを確認"""
        result = backtester.run(sample_stock_data, sma_strategy)
        assert isinstance(result['equity_curve'], pd.Series)
    
    def test_equity_curve_starts_at_one(self, backtester, sample_stock_data, sma_strategy):
        """equity_curveが1付近から始まることを確認（最初のリターンがNaNの場合）"""
        result = backtester.run(sample_stock_data, sma_strategy)
        equity_curve = result['equity_curve']
        
        # 最初の有効な値を確認（NaNをスキップ）
        first_valid_idx = equity_curve.first_valid_index()
        if first_valid_idx is not None:
            first_value = equity_curve[first_valid_idx]
            # 最初の値は1に近いはず（累積リターンの開始点）
            assert 0.5 <= first_value <= 2.0
    
    def test_buy_and_hold_strategy(self, backtester):
        """買い持ち戦略のシンプルなテスト"""
        # 上昇トレンドのデータを作成
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        prices = np.linspace(1000, 1500, 30)  # 50%上昇
        
        df = pd.DataFrame({
            'Close': prices,
            'Open': prices,
            'High': prices + 5,
            'Low': prices - 5,
            'Volume': 1000000
        }, index=dates)
        
        # 常に買いシグナルを出す戦略をシミュレート
        strategy = SMACrossoverStrategy(short_window=2, long_window=3)
        result = backtester.run(df, strategy)
        
        # 結果が返されることを確認
        assert result is not None
        assert 'total_return' in result
    
    def test_no_trading_strategy(self, backtester, sample_stock_data):
        """取引しない戦略のテスト"""
        # シグナルを生成しない戦略を作成
        from src.strategies import Strategy
        
        class NoTradeStrategy(Strategy):
            def __init__(self):
                super().__init__("No Trade")
            
            def generate_signals(self, df):
                return pd.Series(0, index=df.index)
        
        strategy = NoTradeStrategy()
        result = backtester.run(sample_stock_data, strategy)
        
        # リターンは0に近いはず
        assert abs(result['total_return']) < 0.01
        # すべてのポジションが0のはず
        assert (result['positions'] == 0).all()
    
    def test_multiple_strategies_same_data(self, backtester, sample_stock_data):
        """同じデータで複数の戦略を実行できることを確認"""
        from src.strategies import SMACrossoverStrategy, RSIStrategy
        
        sma_strategy = SMACrossoverStrategy(5, 25)
        rsi_strategy = RSIStrategy(14, 30, 70)
        
        result1 = backtester.run(sample_stock_data, sma_strategy)
        result2 = backtester.run(sample_stock_data, rsi_strategy)
        
        # 両方の結果が返されることを確認
        assert result1 is not None
        assert result2 is not None
        
        # 異なる戦略なので、通常は異なるリターンになる
        # （ただし、データによっては同じになる可能性もある）
        assert 'total_return' in result1
        assert 'total_return' in result2
