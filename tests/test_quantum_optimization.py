import unittest
import pandas as pd
import numpy as np
from src.portfolio_optimizer import PortfolioOptimizer

class TestQuantumOptimization(unittest.TestCase):
    def setUp(self):
        self.optimizer = PortfolioOptimizer()
        
    def test_quantum_selection_logic(self):
        """量子最適化が相関の高い銘柄を避けるかテスト"""
        # サンプルデータの作成
        # Stock_A と Stock_B は非常に高い相関を持つようにする
        # Stock_C は独立している
        np.random.seed(42)
        n_days = 252
        base = np.random.randn(n_days) * 0.02
        
        returns = pd.DataFrame({
            "Stock_A": base + np.random.randn(n_days) * 0.001,
            "Stock_B": base + np.random.randn(n_days) * 0.001,
            "Stock_C": np.random.randn(n_days) * 0.02
        })
        
        # AとBの相関を確認
        corr = returns.corr()
        print("\nCorrelation Matrix:", corr)
        self.assertGreater(corr.loc["Stock_A", "Stock_B"], 0.9)
        
        # 量子ハイブリッド最適化を実行
        # ターゲット銘柄数を2にする（A, B, Cのうち2つ選ぶ）
        # AとBは似ているので、AとC、またはBとCが選ばれるのが理想
        result = self.optimizer.quantum_hybrid_optimization(returns, risk_aversion=0.8, target_assets=2)
        
        weights = result["weights"]
        print("\nQuantum Weights:", weights)
        
        # AとBの両方に大きなウェイトが置かれていないことを確認
        # (片方が選ばれ、もう片方は排除されるはず)
        a_weight = weights["Stock_A"]
        b_weight = weights["Stock_B"]
        
        self.assertTrue(a_weight < 0.1 or b_weight < 0.1, "Quantum optimization should avoid picking highly correlated assets simultaneously.")
        self.assertGreater(weights["Stock_C"], 0.3, "Independent asset C should be selected.")

if __name__ == "__main__":
    unittest.main()