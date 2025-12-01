"""
Factor Analyzer - ファクター分析

バリュー、成長、モメンタム等のファクター分析
"""
import pandas as pd
import numpy as np
from typing import Dict, List
import logging


class FactorAnalyzer:
    """ファクター分析クラス"""
    
    FACTORS = ['value', 'growth', 'momentum', 'quality', 'size', 'volatility']
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_value_score(self, ticker_data: Dict) -> float:
        """
        バリュースコアを計算
        
        Args:
            ticker_data: {'pe_ratio': float, 'pb_ratio': float, 'dividend_yield': float}
            
        Returns:
            バリュースコア（高いほど割安）
        """
        pe = ticker_data.get('pe_ratio', 20)
        pb = ticker_data.get('pb_ratio', 2)
        div_yield = ticker_data.get('dividend_yield', 0.02)
        
        # 逆数を取る（低いほど割安）
        pe_score = max(1 / pe, 0) if pe > 0 else 0
        pb_score = max(1 / pb, 0) if pb > 0 else 0
        
        # 正規化して合成
        value_score = (pe_score * 0.4 + pb_score * 0.4 + div_yield * 10 * 0.2)
        
        return min(value_score, 1.0)  # 0-1に正規化
    
    def calculate_growth_score(self, ticker_data: Dict) -> float:
        """
        成長スコアを計算
        
        Args:
            ticker_data: {'revenue_growth': float, 'earnings_growth': float}
            
        Returns:
            成長スコア
        """
        rev_growth = ticker_data.get('revenue_growth', 0.05)
        earnings_growth = ticker_data.get('earnings_growth', 0.05)
        
        # 成長率を0-1にスケール（0-50%を想定）
        growth_score = (rev_growth * 0.5 + earnings_growth * 0.5) / 0.5
        
        return min(max(growth_score, 0), 1.0)
    
    def calculate_momentum_score(self, price_data: pd.Series) -> float:
        """
        モメンタムスコアを計算
        
        Args:
            price_data: 価格系列
            
        Returns:
            モメンタムスコア
        """
        if len(price_data) < 60:
            return 0.5
        
        # 過去3ヶ月（60営業日）のリターン
        momentum_3m = (price_data.iloc[-1] / price_data.iloc[-60]) - 1
        
        # 過去6ヶ月（120営業日）のリターン
        if len(price_data) >= 120:
            momentum_6m = (price_data.iloc[-1] / price_data.iloc[-120]) - 1
            momentum = momentum_3m * 0.6 + momentum_6m * 0.4
        else:
            momentum = momentum_3m
        
        # -20%から+20%を0-1にスケール
        score = (momentum + 0.2) / 0.4
        
        return min(max(score, 0), 1.0)
    
    def calculate_quality_score(self, ticker_data: Dict) -> float:
        """
        クオリティスコアを計算
        
        Args:
            ticker_data: {'roe': float, 'debt_to_equity': float, 'profit_margin': float}
            
        Returns:
            クオリティスコア
        """
        roe = ticker_data.get('roe', 0.10)
        debt_to_equity = ticker_data.get('debt_to_equity', 1.0)
        profit_margin = ticker_data.get('profit_margin', 0.05)
        
        # ROEスコア（0-30%を想定）
        roe_score = min(roe / 0.3, 1.0)
        
        # 負債スコア（低いほど良い、0-2を想定）
        debt_score = max(1 - debt_to_equity / 2, 0)
        
        # 利益率スコア（0-20%を想定）
        margin_score = min(profit_margin / 0.2, 1.0)
        
        quality_score = roe_score * 0.4 + debt_score * 0.3 + margin_score * 0.3
        
        return quality_score
    
    def calculate_size_score(self, market_cap: float) -> float:
        """
        サイズスコアを計算
        
        Args:
            market_cap: 時価総額（百万円）
            
        Returns:
            サイズスコア（小さいほど高スコア）
        """
        # 時価総額を対数変換（小型株優位）
        # 1000億円を基準
        if market_cap <= 0:
            return 0.5
        
        log_cap = np.log10(market_cap)
        log_base = np.log10(100000)  # 1000億円
        
        # 大きいほどスコアが低い
        score = max(1 - (log_cap - log_base) / 2, 0)
        
        return min(score, 1.0)
    
    def calculate_volatility_score(self, returns: pd.Series) -> float:
        """
        ボラティリティスコアを計算
        
        Args:
            returns: リターン系列
            
        Returns:
            ボラティリティスコア（低いほど高スコア）
        """
        if returns.empty:
            return 0.5
        
        # 年率ボラティリティ
        annual_vol = returns.std() * np.sqrt(252)
        
        # 0-50%を想定、低いほど高スコア
        score = max(1 - annual_vol / 0.5, 0)
        
        return score
    
    def calculate_composite_score(self, ticker: str,
                                  price_data: pd.Series,
                                  fundamental_data: Dict,
                                  factor_weights: Dict = None) -> Dict:
        """
        総合ファクタースコアを計算
        
        Args:
            ticker: 銘柄コード
            price_data: 価格データ
            fundamental_data: ファンダメンタルデータ
            factor_weights: ファクターのウェイト
            
        Returns:
            ファクター分析結果
        """
        if factor_weights is None:
            factor_weights = {
                'value': 0.20,
                'growth': 0.20,
                'momentum': 0.20,
                'quality': 0.20,
                'size': 0.10,
                'volatility': 0.10
            }
        
        # 各ファクタースコア計算
        returns = price_data.pct_change().dropna()
        
        scores = {
            'value': self.calculate_value_score(fundamental_data),
            'growth': self.calculate_growth_score(fundamental_data),
            'momentum': self.calculate_momentum_score(price_data),
            'quality': self.calculate_quality_score(fundamental_data),
            'size': self.calculate_size_score(fundamental_data.get('market_cap', 100000)),
            'volatility': self.calculate_volatility_score(returns)
        }
        
        # 加重平均
        composite = sum(scores[f] * factor_weights[f] for f in self.FACTORS)
        
        return {
            'ticker': ticker,
            'composite_score': composite,
            'factor_scores': scores,
            'dominant_factor': max(scores.items(), key=lambda x: x[1])[0],
            'interpretation': self._interpret_factors(scores)
        }
    
    def _interpret_factors(self, scores: Dict) -> str:
        """
        ファクタースコアの解釈
        
        Args:
            scores: ファクタースコア辞書
            
        Returns:
            解釈文
        """
        strengths = [f for f, s in scores.items() if s > 0.7]
        weaknesses = [f for f, s in scores.items() if s < 0.3]
        
        interpretation = []
        
        if strengths:
            interpretation.append(f"✅ 強み: {', '.join(strengths)}")
        
        if weaknesses:
            interpretation.append(f"⚠️ 弱み: {', '.join(weaknesses)}")
        
        if not strengths and not weaknesses:
            interpretation.append("➡️ バランス型")
        
        return " | ".join(interpretation)


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    analyzer = FactorAnalyzer()
    
    print("=== Factor Analyzer Test ===\n")
    
    # ダミーデータ
    fundamental_data = {
        'pe_ratio': 15,
        'pb_ratio': 1.5,
        'dividend_yield': 0.03,
        'revenue_growth': 0.10,
        'earnings_growth': 0.12,
        'roe': 0.15,
        'debt_to_equity': 0.8,
        'profit_margin': 0.08,
        'market_cap': 500000  # 5000億円
    }
    
    price_data = pd.Series(np.random.randn(252).cumsum() + 1000)
    
    result = analyzer.calculate_composite_score('TEST.T', price_data, fundamental_data)
    
    print(f"銘柄: {result['ticker']}")
    print(f"総合スコア: {result['composite_score']:.2f}")
    print(f"主要ファクター: {result['dominant_factor']}\n")
    
    print("ファクター別スコア:")
    for factor, score in result['factor_scores'].items():
        print(f"  {factor}: {score:.2f}")
    
    print(f"\n{result['interpretation']}")
