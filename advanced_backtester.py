"""
高度なバックテストシステム

複数戦略の比較、パラメータ最適化、ウォークフォワード分析を実行
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import itertools
from concurrent.futures import ProcessPoolExecutor, as_completed

from src.backtester import Backtester
from src.strategies import LightGBMStrategy, MLStrategy, CombinedStrategy
from src.data_loader import fetch_stock_data
from src.constants import NIKKEI_225_TICKERS


class AdvancedBacktester:
    """高度なバックテストシステム"""
    
    def __init__(self):
        self.results = []
    
    def compare_strategies(self, tickers: List[str], period: str = "2y") -> pd.DataFrame:
        """複数戦略を比較"""
        print("複数戦略比較バックテスト開始...")
        
        # データ取得
        data_map = fetch_stock_data(tickers, period=period)
        
        # 戦略定義
        strategies = {
            "LightGBM": LightGBMStrategy(lookback_days=365, threshold=0.005),
            "ML Random Forest": MLStrategy(),
            "Combined": CombinedStrategy()
        }
        
        results = []
        
        for strategy_name, strategy in strategies.items():
            print(f"\n=== {strategy_name} テスト中 ===")
            
            backtester = Backtester(
                strategy=strategy,
                initial_capital=1000000,
                commission=0.001
            )
            
            # バックテスト実行
            backtest_result = backtester.run_backtest(data_map)
            
            if backtest_result:
                results.append({
                    'strategy': strategy_name,
                    'total_return': backtest_result.get('total_return', 0),
                    'sharpe_ratio': backtest_result.get('sharpe_ratio', 0),
                    'max_drawdown': backtest_result.get('max_drawdown', 0),
                    'win_rate': backtest_result.get('win_rate', 0),
                    'total_trades': backtest_result.get('total_trades', 0),
                    'final_equity': backtest_result.get('final_equity', 0)
                })
        
        return pd.DataFrame(results)
    
    def optimize_parameters(self, ticker: str, strategy_class, param_grid: Dict) -> Dict:
        """パラメータ最適化（グリッドサーチ）"""
        print(f"\n{ticker} のパラメータ最適化...")
        
        # データ取得
        data_map = fetch_stock_data([ticker], period="2y")
        
        if not data_map or ticker not in data_map:
            return {}
        
        # パラメータ組み合わせ生成
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(itertools.product(*param_values))
        
        best_sharpe = -np.inf
        best_params = None
        results = []
        
        print(f"テスト組み合わせ数: {len(param_combinations)}")
        
        for i, params in enumerate(param_combinations):
            param_dict = dict(zip(param_names, params))
            
            try:
                # 戦略インスタンス作成
                strategy = strategy_class(**param_dict)
                
                # バックテスト
                backtester = Backtester(
                    strategy=strategy,
                    initial_capital=1000000,
                    commission=0.001
                )
                
                result = backtester.run_backtest(data_map)
                
                if result:
                    sharpe = result.get('sharpe_ratio', 0)
                    
                    results.append({
                        'params': param_dict,
                        'sharpe_ratio': sharpe,
                        'total_return': result.get('total_return', 0)
                    })
                    
                    if sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_params = param_dict
            
            except Exception as e:
                # エラーをログに記録
                print(f"パラメータ {param_dict} でエラー: {e}")
                continue
            
            # 進捗表示
            if (i + 1) % 10 == 0:
                print(f"進捗: {i+1}/{len(param_combinations)}")
        
        print(f"\n最適パラメータ: {best_params}")
        print(f"最高シャープレシオ: {best_sharpe:.2f}")
        
        return {
            'best_params': best_params,
            'best_sharpe': best_sharpe,
            'all_results': results
        }
    
    def walk_forward_analysis(self, ticker: str, strategy, 
                              train_days: int = 250, test_days: int = 60, 
                              n_iterations: int = 5) -> Dict:
        """ウォークフォワード分析"""
        print(f"\n{ticker} のウォークフォワード分析...")
        
        # データ取得（長期）
        total_days = train_days + (test_days * n_iterations)
        data_map = fetch_stock_data([ticker], period=f"{total_days}d")
        
        if not data_map or ticker not in data_map:
            return {}
        
        df = data_map[ticker]
        
        results = []
        
        for i in range(n_iterations):
            # 訓練期間
            train_start_idx = i * test_days
            train_end_idx = train_start_idx + train_days
            
            # テスト期間
            test_start_idx = train_end_idx
            test_end_idx = test_start_idx + test_days
            
            if test_end_idx > len(df):
                break
            
            train_data = df.iloc[train_start_idx:train_end_idx]
            test_data = df.iloc[test_start_idx:test_end_idx]
            
            print(f"\nイテレーション {i+1}/{n_iterations}")
            print(f"  訓練: {train_data.index[0]} ~ {train_data.index[-1]}")
            print(f"  テスト: {test_data.index[0]} ~ {test_data.index[-1]}")
            
            # 訓練（戦略を学習）
            # 機械学習戦略の場合は、訓練データでモデルを再学習
            if hasattr(strategy, 'fit'):
                try:
                    train_data_map = {ticker: train_data}
                    strategy.fit(train_data_map)
                    print(f"  戦略を訓練データで再学習しました")
                except Exception as e:
                    print(f"  戦略の訓練でエラー: {e}")
            
            # テスト
            backtester = Backtester(
                strategy=strategy,
                initial_capital=1000000,
                commission=0.001
            )
            
            test_data_map = {ticker: test_data}
            result = backtester.run_backtest(test_data_map)
            
            if result:
                results.append({
                    'iteration': i + 1,
                    'train_start': train_data.index[0],
                    'test_start': test_data.index[0],
                    'total_return': result.get('total_return', 0),
                    'sharpe_ratio': result.get('sharpe_ratio', 0),
                    'max_drawdown': result.get('max_drawdown', 0)
                })
        
        # 集計
        results_df = pd.DataFrame(results)
        
        summary = {
            'iterations': len(results),
            'avg_return': results_df['total_return'].mean(),
            'avg_sharpe': results_df['sharpe_ratio'].mean(),
            'avg_dd': results_df['max_drawdown'].mean(),
            'std_return': results_df['total_return'].std(),
            'results': results_df
        }
        
        print(f"\n=== ウォークフォワード分析結果 ===")
        print(f"イテレーション数: {summary['iterations']}")
        print(f"平均リターン: {summary['avg_return']:.2f}%")
        print(f"平均シャープレシオ: {summary['avg_sharpe']:.2f}")
        print(f"平均最大DD: {summary['avg_dd']:.2f}%")
        print(f"リターン標準偏差: {summary['std_return']:.2f}%")
        
        return summary
    
    def monte_carlo_simulation(self, returns: pd.Series, n_simulations: int = 1000, 
                               n_days: int = 252) -> Dict:
        """モンテカルロシミュレーション"""
        print(f"\nモンテカルロシミュレーション ({n_simulations}回)")
        
        # リターンの統計
        mean_return = returns.mean()
        std_return = returns.std()
        
        simulations = []
        
        for i in range(n_simulations):
            # ランダムリターン生成
            sim_returns = np.random.normal(mean_return, std_return, n_days)
            
            # 累積リターン
            cumulative = (1 + sim_returns).cumprod()
            final_value = cumulative[-1]
            
            simulations.append(final_value)
        
        simulations = np.array(simulations)
        
        # 統計
        percentiles = [5, 25, 50, 75, 95]
        percentile_values = np.percentile(simulations, percentiles)
        
        result = {
            'mean': simulations.mean(),
            'median': np.median(simulations),
            'std': simulations.std(),
            'percentiles': dict(zip(percentiles, percentile_values)),
            'prob_profit': (simulations > 1.0).sum() / n_simulations
        }
        
        print(f"平均最終値: {result['mean']:.2f}x")
        print(f"中央値: {result['median']:.2f}x")
        print(f"標準偏差: {result['std']:.2f}")
        print(f"利益確率: {result['prob_profit']:.1%}")
        print(f"パーセンタイル:")
        for p, v in result['percentiles'].items():
            print(f"  {p}%: {v:.2f}x")
        
        return result


def main():
    """メイン実行"""
    backtester = AdvancedBacktester()
    
    # テスト銘柄
    test_tickers = NIKKEI_225_TICKERS[:5]
    
    # 1. 戦略比較
    print("\n" + "="*60)
    print("戦略比較バックテスト")
    print("="*60)
    comparison = backtester.compare_strategies(test_tickers, period="1y")
    print("\n" + str(comparison))
    
    # 2. パラメータ最適化（例）
    # print("\n" + "="*60)
    # print("パラメータ最適化")
    # print("="*60)
    # param_grid = {
    #     'lookback_days': [200, 250, 300],
    #     'threshold': [0.003, 0.005, 0.007]
    # }
    # optimization = backtester.optimize_parameters(
    #     "7203.T", 
    #     LightGBMStrategy, 
    #     param_grid
    # )
    
    # 3. ウォークフォワード分析
    print("\n" + "="*60)
    print("ウォークフォワード分析")
    print("="*60)
    wf_result = backtester.walk_forward_analysis(
        "7203.T",
        CombinedStrategy(),
        train_days=250,
        test_days=60,
        n_iterations=3
    )


if __name__ == "__main__":
    main()
