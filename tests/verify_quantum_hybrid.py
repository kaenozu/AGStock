import pandas as pd
import numpy as np
from src.optimization.quantum_engine import QuantumPortfolioOptimizer
import logging

logging.basicConfig(level=logging.INFO)

def test_hybrid_optimization():
    # 1. 疑似データの生成 (20銘柄)
    np.random.seed(42)
    tickers = [f"STK_{i}" for i in range(20)]
    dates = pd.date_range(start="2023-01-01", periods=100)
    
    data_map = {}
    for ticker in tickers:
        # ランダムな株価生成
        returns = np.random.normal(0.001, 0.02, 100)
        price = 100 * (1 + returns).cumprod()
        data_map[ticker] = pd.DataFrame({"Close": price}, index=dates)
        
    # 2. ハイブリッド最適化の実行
    optimizer = QuantumPortfolioOptimizer()
    
    print("--- Running Hybrid Optimization (Target 5 assets) ---")
    allocation = optimizer.solve_hybrid_optimization(data_map, target_assets=5)
    
    print("\nResult Allocation:")
    for ticker, weight in sorted(allocation.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ticker}: {weight:.2%}")
        
    # 3. 検証
    assert len(allocation) <= 5, f"Selected {len(allocation)} assets, expected <= 5"
    assert abs(sum(allocation.values()) - 1.0) < 1e-5, "Weights do not sum to 1"
    print("\nVerification Passed!")

if __name__ == "__main__":
    test_hybrid_optimization()
