"""
Advanced Risk Manager - VaR/CVaRを含む高度なリスク管理

Value at Risk (VaR) と Conditional VaR (CVaR) を計算
"""
import numpy as np
import pandas as pd
from typing import Dict
from scipy import stats
import logging


class AdvancedRiskManager:
    """高度なリスク管理クラス"""
    
    def __init__(self, confidence_level: float = 0.95):
        """
        Args:
            confidence_level: 信頼水準（デフォルト95%）
        """
        self.confidence_level = confidence_level
        self.logger = logging.getLogger(__name__)
    
    def calculate_var(self, returns: pd.Series, method: str = 'historical') -> float:
        """
        VaR（Value at Risk）を計算
        
        Args:
            returns: リターンの系列
            method: 計算方法（'historical', 'parametric', 'monte_carlo'）
            
        Returns:
            VaR値（負の値）
        """
        if returns.empty:
            return 0.0
        
        if method == 'historical':
            # 歴史的シミュレーション法
            var = returns.quantile(1 - self.confidence_level)
            
        elif method == 'parametric':
            # パラメトリック法（正規分布を仮定）
            mean = returns.mean()
            std = returns.std()
            z_score = stats.norm.ppf(1 - self.confidence_level)
            var = mean + z_score * std
            
        elif method == 'monte_carlo':
            # モンテカルロシミュレーション
            mean = returns.mean()
            std = returns.std()
            simulated = np.random.normal(mean, std, 10000)
            var = np.percentile(simulated, (1 - self.confidence_level) * 100)
            
        else:
            var = returns.quantile(1 - self.confidence_level)
        
        return var
    
    def calculate_cvar(self, returns: pd.Series) -> float:
        """
        CVaR（Conditional VaR / Expected Shortfall）を計算
        
        VaRを超える損失の期待値
        
        Args:
            returns: リターンの系列
            
        Returns:
            CVaR値（負の値）
        """
        if returns.empty:
            return 0.0
        
        var = self.calculate_var(returns, method='historical')
        
        # VaRを下回るリターンの平均
        cvar = returns[returns <= var].mean()
        
        return cvar
    
    def calculate_portfolio_var(self, positions: pd.DataFrame, 
                               returns_data: Dict[str, pd.Series],
                               total_value: float) -> Dict:
        """
        ポートフォリオ全体のVaRを計算
        
        Args:
            positions: ポジション情報
            returns_data: 各銘柄のリターンデータ
            total_value: ポートフォリオ総額
            
        Returns:
            VaR情報
        """
        if positions.empty:
            return {'var': 0, 'cvar': 0, 'var_pct': 0, 'cvar_pct': 0}
        
        # ポートフォリオリターンを計算
        portfolio_returns = pd.Series(0.0, index=list(returns_data.values())[0].index)
        
        for _, pos in positions.iterrows():
            ticker = pos['ticker']
            if ticker not in returns_data:
                continue
            
            # ウェイト
            weight = pos.get('market_value', 0) / total_value if total_value > 0 else 0
            
            # 加重リターン
            portfolio_returns += returns_data[ticker] * weight
        
        # VaRとCVaRを計算
        var = self.calculate_var(portfolio_returns)
        cvar = self.calculate_cvar(portfolio_returns)
        
        # 金額換算
        var_amount = var * total_value
        cvar_amount = cvar * total_value
        
        return {
            'var': var_amount,
            'cvar': cvar_amount,
            'var_pct': var * 100,
            'cvar_pct': cvar * 100,
            'interpretation': self._interpret_var(var * 100)
        }
    
    def _interpret_var(self, var_pct: float) -> str:
        """
        VaRの解釈を返す
        
        Args:
            var_pct: VaR（%）
            
        Returns:
            解釈文
        """
        if var_pct > -1:
            return "🟢 非常に低リスク"
        elif var_pct > -3:
            return "🟡 低リスク"
        elif var_pct > -5:
            return "🟠 中リスク"
        else:
            return "🔴 高リスク"
    
    def stress_test(self, returns: pd.Series, 
                   scenarios: Dict[str, float]) -> Dict:
        """
        ストレステスト - 極端なシナリオでの損失を推定
        
        Args:
            returns: リターン系列
            scenarios: シナリオ辞書 {"名前": 下落率}
            
        Returns:
            各シナリオでの損失
        """
        results = {}
        
        mean = returns.mean()
        std = returns.std()
        
        for name, shock in scenarios.items():
            # ショックを適用
            stressed_return = mean + shock * std
            results[name] = stressed_return
        
        return results
    
    def calculate_risk_parity_weights(self, returns_data: Dict[str, pd.Series]) -> Dict[str, float]:
        """
        リスクパリティウェイトを計算
        
        各資産のリスク寄与度を均等にする
        
        Args:
            returns_data: 各銘柄のリターンデータ
            
        Returns:
            最適ウェイト
        """
        tickers = list(returns_data.keys())
        
        # 各銘柄のボラティリティ
        volatilities = {t: returns_data[t].std() for t in tickers}
        
        # 逆ボラティリティウェイト（リスクパリティの簡易版）
        total_inv_vol = sum(1/v for v in volatilities.values() if v > 0)
        
        weights = {}
        for ticker, vol in volatilities.items():
            if vol > 0:
                weights[ticker] = (1/vol) / total_inv_vol
            else:
                weights[ticker] = 0
        
        return weights


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    # ダミーデータ
    np.random.seed(42)
    returns = pd.Series(np.random.randn(252) * 0.02)
    
    rm = AdvancedRiskManager(confidence_level=0.95)
    
    print("=== Advanced Risk Manager Test ===\n")
    
    # VaR計算
    var = rm.calculate_var(returns, method='historical')
    print(f"VaR (95%): {var*100:.2f}%")
    
    # CVaR計算
    cvar = rm.calculate_cvar(returns)
    print(f"CVaR (95%): {cvar*100:.2f}%")
    print(f"解釈: {rm._interpret_var(var*100)}\n")
    
    # ストレステスト
    scenarios = {
        "軽度の調整": -1,      # -1標準偏差
        "中程度の下落": -2,    # -2標準偏差
        "市場暴落": -3         # -3標準偏差
    }
    
    stress_results = rm.stress_test(returns, scenarios)
    print("ストレステスト結果:")
    for name, result in stress_results.items():
        print(f"  {name}: {result*100:.2f}%")
