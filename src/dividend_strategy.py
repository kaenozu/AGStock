"""
Dividend Strategy - 配当戦略

高配当株スクリーニングと配当再投資
"""
import pandas as pd
from typing import Dict, List
import logging


class DividendStrategy:
    """配当戦略クラス"""
    
    # 高配当銘柄の例（参考）
    HIGH_DIVIDEND_STOCKS = {
        '2914': {'name': 'JT', 'typical_yield': 0.06},
        '8058': {'name': '三菱商事', 'typical_yield': 0.04},
        '9432': {'name': 'NTT', 'typical_yield': 0.03},
        '9433': {'name': 'KDDI', 'typical_yield': 0.035},
        '8031': {'name': '三井物産', 'typical_yield': 0.045},
        '8306': {'name': '三菱UFJ', 'typical_yield': 0.04}
    }
    
    def __init__(self, min_yield: float = 0.03):
        """
        Args:
            min_yield: 最低配当利回り（デフォルト3%）
        """
        self.min_yield = min_yield
        self.logger = logging.getLogger(__name__)
    
    def screen_high_dividend_stocks(self, stock_data: Dict) -> List[Dict]:
        """
        高配当株をスクリーニング
        
        Args:
            stock_data: 株価・配当データ
                {ticker: {'price': float, 'dividend': float, 'payout_ratio': float}}
                
        Returns:
            スクリーニング結果のリスト
        """
        results = []
        
        for ticker, data in stock_data.items():
            price = data.get('price', 0)
            dividend = data.get('dividend', 0)
            payout_ratio = data.get('payout_ratio', 0)
            
            if price <= 0:
                continue
            
            # 配当利回り計算
            dividend_yield = dividend / price if price > 0 else 0
            
            # スクリーニング条件
            if (dividend_yield >= self.min_yield and 
                0.3 <= payout_ratio <= 0.7):  # 配当性向30-70%
                
                results.append({
                    'ticker': ticker,
                    'dividend_yield': dividend_yield,
                    'payout_ratio': payout_ratio,
                    'sustainability_score': self._calculate_sustainability(payout_ratio),
                    'recommendation': self._get_recommendation(dividend_yield, payout_ratio)
                })
        
        # 配当利回り順にソート
        results.sort(key=lambda x: x['dividend_yield'], reverse=True)
        
        return results
    
    def _calculate_sustainability(self, payout_ratio: float) -> str:
        """
        配当持続可能性スコア
        
        Args:
            payout_ratio: 配当性向
            
        Returns:
            スコア（高・中・低）
        """
        if payout_ratio < 0.4:
            return "高"  # 増配余地あり
        elif payout_ratio < 0.6:
            return "中"  # 適正
        else:
            return "低"  # 減配リスク
    
    def _get_recommendation(self, yield_val: float, payout: float) -> str:
        """
        推奨度を判定
        
        Args:
            yield_val: 配当利回り
            payout: 配当性向
            
        Returns:
            推奨度
        """
        if yield_val >= 0.05 and 0.3 <= payout <= 0.5:
            return "強く推奨"
        elif yield_val >= 0.04 and payout < 0.7:
            return "推奨"
        else:
            return "検討"
    
    def calculate_dividend_income(self, positions: pd.DataFrame) -> Dict:
        """
        年間配当収入を計算
        
        Args:
            positions: ポジション情報（ticker, quantity, dividend_per_share）
            
        Returns:
            配当収入情報
        """
        if positions.empty:
            return {'total_dividend': 0, 'yield_on_cost': 0}
        
        # 各銘柄の配当額
        positions['dividend_income'] = (
            positions['quantity'] * positions.get('dividend_per_share', 0)
        )
        
        total_dividend = positions['dividend_income'].sum()
        
        # 投資額に対する利回り
        total_investment = (positions['quantity'] * positions['entry_price']).sum()
        yield_on_cost = total_dividend / total_investment if total_investment > 0 else 0
        
        return {
            'total_dividend': total_dividend,
            'yield_on_cost': yield_on_cost,
            'by_ticker': positions[['ticker', 'dividend_income']].to_dict('records')
        }
    
    def simulate_dividend_reinvestment(self, initial_investment: float,
                                      annual_dividend_yield: float,
                                      years: int = 10) -> pd.DataFrame:
        """
        配当再投資の複利効果をシミュレーション
        
        Args:
            initial_investment: 初期投資額
            annual_dividend_yield: 年間配当利回り
            years: シミュレーション期間（年）
            
        Returns:
            年次推移のDataFrame
        """
        results = []
        total = initial_investment
        
        for year in range(1, years + 1):
            # 配当受取
            dividend = total * annual_dividend_yield
            
            # 配当再投資
            total += dividend
            
            results.append({
                'year': year,
                'total_value': total,
                'dividend_received': dividend,
                'growth_rate': ((total / initial_investment) - 1) * 100
            })
        
        return pd.DataFrame(results)
    
    def get_dividend_calendar(self, positions: List[str]) -> Dict:
        """
        配当カレンダーを取得（予定）
        
        Args:
            positions: 保有銘柄リスト
            
        Returns:
            配当予定情報
        """
        # 簡易実装（実際はyfinanceなどから取得）
        calendar = {
            'next_dividends': [],
            'total_expected': 0
        }
        
        # 日本株は通常3月・9月決算が多い
        typical_months = {
            '2914': [3, 9],   # JT
            '9432': [3, 9],   # NTT
            '9433': [3, 9],   # KDDI
        }
        
        for ticker in positions:
            if ticker in typical_months:
                calendar['next_dividends'].append({
                    'ticker': ticker,
                    'expected_months': typical_months[ticker],
                    'note': '通常3月・9月に配当'
                })
        
        return calendar


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    strategy = DividendStrategy(min_yield=0.03)
    
    print("=== Dividend Strategy Test ===\n")
    
    # テスト1: 高配当株スクリーニング
    stock_data = {
        '2914': {'price': 3000, 'dividend': 180, 'payout_ratio': 0.75},  # JT
        '9432': {'price': 150, 'dividend': 5, 'payout_ratio': 0.45},     # NTT
        '9433': {'price': 4000, 'dividend': 140, 'payout_ratio': 0.40},  # KDDI
    }
    
    results = strategy.screen_high_dividend_stocks(stock_data)
    print("高配当株スクリーニング結果:")
    for r in results:
        print(f"  {r['ticker']}: 利回り{r['dividend_yield']*100:.2f}% - {r['recommendation']}")
    print()
    
    # テスト2: 配当再投資シミュレーション
    simulation = strategy.simulate_dividend_reinvestment(
        initial_investment=1000000,
        annual_dividend_yield=0.04,
        years=10
    )
    
    print("配当再投資シミュレーション（10年間、利回り4%）:")
    print("  初期: 100万円")
    print(f"  10年後: {simulation.iloc[-1]['total_value']:,.0f}円")
    print(f"  成長率: +{simulation.iloc[-1]['growth_rate']:.1f}%")
