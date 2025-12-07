"""
Benchmark Evolution - 進化型AIの性能検証
Buy & Hold vs Standard AI vs Evolved AI
"""
import sys
import os
import pandas as pd
import numpy as np
import logging
sys.path.insert(0, os.getcwd())

# ログ抑制
logging.basicConfig(level=logging.INFO)
logging.getLogger("src.data_loader").setLevel(logging.ERROR)

from src.data_loader import fetch_stock_data
from src.evolved_strategy import EvolvedStrategy
from src.strategies import LightGBMStrategy
from src.vector_backtester import get_vector_backtester

def calculate_metrics(returns):
    total_return = (1 + returns).cumprod().iloc[-1] - 1
    daily_sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else 0
    return total_return, daily_sharpe

def main():
    print("\n" + "="*60)
    print("🧬 Neuro-Evolution Performance Benchmark")
    print("="*60)
    
    ticker = "^N225" # 日経平均でテスト
    print(f"Target: {ticker}")
    
    # 1. データ準備 (過去2年)
    print("Fetching data...")
    data_map = fetch_stock_data([ticker], period="2y")
    df = data_map[ticker].copy()
    
    # リターン計算用
    df['Market_Ret'] = df['Close'].pct_change().fillna(0)
    
    # 2. Buy & Hold
    bh_ret = df['Market_Ret']
    bh_total, bh_sharpe = calculate_metrics(bh_ret)
    print(f"\n[1] 📉 Buy & Hold")
    print(f"    Total Return: {bh_total:+.2%}")
    print(f"    Sharpe Ratio: {bh_sharpe:.4f}")
    
    # 3. Standard AI (LightGBM - Pre-Evolution)
    # 簡易的にシグナル生成してバックテスト
    # 注: LightGBMStrategyは学習が必要だが、ここでは簡易ロジック(移動平均クロス等)で代用するか、
    # 既存のLightGBMStrategyを使う。学習済みモデルがないとランダムになるため、
    # フェアな比較として「進化前の単純ルール（SMAクロス）」を使う。
    
    print(f"\n[2] 🤖 Standard Rule (Simple SMA Cross)")
    # SMA 20/50 Cross
    df['SMA_S'] = df['Close'].rolling(20).mean()
    df['SMA_L'] = df['Close'].rolling(50).mean()
    df['Sig_Std'] = np.where(df['SMA_S'] > df['SMA_L'], 1, -1)
    std_ret = df['Market_Ret'] * df['Sig_Std'].shift(1).fillna(0)
    std_total, std_sharpe = calculate_metrics(std_ret)
    
    print(f"    Total Return: {std_total:+.2%}")
    print(f"    Sharpe Ratio: {std_sharpe:.4f}")
    
    # 4. Evolved AI (Neuro-Evolution)
    print(f"\n[3] 🧬 Evolved AI (Genetically Optimized)")
    strategy = EvolvedStrategy()
    print(f"    Params: {strategy.params}")
    
    # EvolvedStrategyのgenerate_signalsを使う
    signals = strategy.generate_signals(df)
    
    # 0(Hold)はポジション維持とみなすか、ノーポジとするか。
    # ここでは 1=Long, -1=Short, 0=Cash とする (VectorBacktesterのロジックに合わせる)
    # EvolvedStrategyは 1/-1/0 を返す。
    # 簡易バックテスト
    pos = signals.replace(0, np.nan).fillna(method='ffill').fillna(0)
    evo_ret = df['Market_Ret'] * pos.shift(1).fillna(0)
    
    evo_total, evo_sharpe = calculate_metrics(evo_ret)
    
    print(f"    Total Return: {evo_total:+.2%}")
    print(f"    Sharpe Ratio: {evo_sharpe:.4f}")
    
    # 結果出力
    with open("benchmark_result_utf8.txt", "w", encoding="utf-8") as f:
        f.write("-" * 60 + "\n")
        f.write("🧬 Neuro-Evolution Benchmark Report\n")
        f.write("-" * 60 + "\n")
        f.write(f"Target: {ticker}\n\n")
        
        f.write("[1] Buy & Hold\n")
        f.write(f"    Total Return: {bh_total:+.2%}\n")
        f.write(f"    Sharpe Ratio: {bh_sharpe:.4f}\n\n")
        
        f.write("[2] Standard AI (Simple Rule)\n")
        f.write(f"    Total Return: {std_total:+.2%}\n")
        f.write(f"    Sharpe Ratio: {std_sharpe:.4f}\n\n")
        
        f.write("[3] Evolved AI (Genetically Optimized)\n")
        f.write(f"    Total Return: {evo_total:+.2%}\n")
        f.write(f"    Sharpe Ratio: {evo_sharpe:.4f}\n\n")
        
        f.write("-" * 60 + "\n")
        if evo_total > std_total:
            f.write("🏆 Winner: Evolved AI\n") 
        elif std_total > evo_total:
             f.write("🤔 Winner: Standard Rule\n")
        else:
             f.write("Draw\n")

    # Console print
    print("Benchmark completed. Saved to benchmark_result_utf8.txt")

if __name__ == "__main__":
    main()
