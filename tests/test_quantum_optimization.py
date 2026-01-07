
import pytest
import pandas as pd
import numpy as np
from src.optimization.quantum_engine import QuantumAnnealer, QuantumPortfolioOptimizer

def test_quantum_annealer_portfolio():
    """ポートフォリオ最適化の基本動作テスト"""
    annealer = QuantumAnnealer(steps=100)
    expected_returns = pd.Series([0.1, 0.2, 0.15], index=["A", "B", "C"])
    cov_matrix = pd.DataFrame(np.eye(3) * 0.05, index=["A", "B", "C"], columns=["A", "B", "C"])
    
    weights = annealer.solve_portfolio_optimization(expected_returns, cov_matrix)
    
    assert isinstance(weights, dict)
    assert len(weights) > 0
    assert abs(sum(weights.values()) - 1.0) < 1e-5
    for ticker in weights:
        assert ticker in ["A", "B", "C"]

def test_quantum_annealer_qubo():
    """QUBOソルバーの基本動作テスト"""
    annealer = QuantumAnnealer(steps=100)
    # 3銘柄中1銘柄を選ぶ簡単なQUBO
    # Q = [[-1, 0, 0], [0, -1, 0], [0, 0, -1]] -> 1つ選ぶのが最小
    Q = -np.eye(3)
    
    result = annealer.solve_qubo(Q, target_count=1)
    
    assert isinstance(result, np.ndarray)
    assert result.shape == (3,)
    assert sum(result) == 1

def test_hybrid_optimization_workflow():
    """ハイブリッド最適化のワークフローテスト"""
    optimizer = QuantumPortfolioOptimizer()
    
    # 疑似データ
    tickers = ["T1", "T2", "T3", "T4", "T5"]
    data_map = {}
    for t in tickers:
        data_map[t] = pd.DataFrame({
            "Close": np.linspace(100, 110, 20) + np.random.normal(0, 1, 20)
        })
        
    allocation = optimizer.solve_hybrid_optimization(data_map, target_assets=3)
    
    assert isinstance(allocation, dict)
    assert len(allocation) <= 3
    assert abs(sum(allocation.values()) - 1.0) < 1e-5
