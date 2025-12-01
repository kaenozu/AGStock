"""
Liquidity Analyzer - 市場流動性分析

最適な取引タイミングとVWAP戦略を実現
"""
import pandas as pd
from datetime import time, datetime
from typing import Dict, List, Tuple
import logging


class LiquidityAnalyzer:
    """市場流動性分析クラス"""
    
    # 時間帯別の流動性プロファイル
    LIQUIDITY_PROFILE = {
        'high': [
            (time(9, 0), time(9, 30)),    # 寄り付き
            (time(14, 30), time(15, 0))   # 引け前
        ],
        'medium': [
            (time(10, 0), time(11, 30)),
            (time(13, 0), time(14, 0))
        ],
        'low': [
            (time(11, 30), time(12, 30))  # 昼休み前後
        ]
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_optimal_trading_times(self) -> Dict[str, List[str]]:
        """
        最適な取引時間帯を取得
        
        Returns:
            時間帯の情報
        """
        return {
            'best_times': ['09:00-09:30', '14:30-15:00'],
            'good_times': ['10:00-11:30', '13:00-14:00'],
            'avoid_times': ['11:30-12:30'],
            'explanation': """
            【推奨時間帯】
            - 09:00-09:30: 寄り付き直後、出来高が最大
            - 14:30-15:00: 引け前、流動性が高い
            
            【避けるべき時間帯】
            - 11:30-12:30: 昼休み前後、板が薄い
            """
        }
    
    def is_good_timing(self, current_time: time = None) -> Tuple[bool, str]:
        """
        現在時刻が取引に適しているか判定
        
        Args:
            current_time: チェックする時刻（Noneで現在時刻）
            
        Returns:
            (適しているか, 理由)
        """
        if current_time is None:
            current_time = datetime.now().time()
        
        # 高流動性時間帯チェック
        for start, end in self.LIQUIDITY_PROFILE['high']:
            if start <= current_time <= end:
                return True, "高流動性時間帯です"
        
        # 低流動性時間帯チェック
        for start, end in self.LIQUIDITY_PROFILE['low']:
            if start <= current_time <= end:
                return False, "流動性が低い時間帯です。取引を避けることを推奨します"
        
        # 中流動性
        return True, "通常の流動性です。取引可能です"
    
    def calculate_vwap(self, ticker_data: pd.DataFrame) -> pd.Series:
        """
        VWAP（出来高加重平均価格）を計算
        
        Args:
            ticker_data: 株価データ（High, Low, Close, Volumeが必要）
            
        Returns:
            VWAPの系列
        """
        if ticker_data.empty:
            return pd.Series()
        
        # 典型価格 = (High + Low + Close) / 3
        typical_price = (ticker_data['High'] + ticker_data['Low'] + ticker_data['Close']) / 3
        
        # VWAP = Σ(典型価格 × 出来高) / Σ出来高
        vwap = (typical_price * ticker_data['Volume']).cumsum() / ticker_data['Volume'].cumsum()
        
        return vwap
    
    def get_vwap_signal(self, current_price: float, vwap: float) -> Dict:
        """
        VWAPに基づく売買シグナル
        
        Args:
            current_price: 現在価格
            vwap: VWAP価格
            
        Returns:
            シグナル情報
        """
        diff_pct = (current_price - vwap) / vwap if vwap > 0 else 0
        
        if diff_pct < -0.02:  # VWAPより2%以上安い
            return {
                'signal': 'BUY',
                'reason': f'VWAPより{abs(diff_pct)*100:.1f}%安い。割安',
                'strength': 'STRONG' if diff_pct < -0.05 else 'MEDIUM'
            }
        
        elif diff_pct > 0.02:  # VWAPより2%以上高い
            return {
                'signal': 'SELL',
                'reason': f'VWAPより{diff_pct*100:.1f}%高い。割高',
                'strength': 'STRONG' if diff_pct > 0.05 else 'MEDIUM'
            }
        
        else:
            return {
                'signal': 'HOLD',
                'reason': 'VWAPに近い価格。待機推奨',
                'strength': 'WEAK'
            }
    
    def split_large_order(self, total_quantity: int, 
                         num_splits: int = 5) -> List[Dict]:
        """
        大口注文を分割して市場への影響を最小化
        
        Args:
            total_quantity: 総注文数
            num_splits: 分割数
            
        Returns:
            分割注文のリスト
        """
        base_quantity = total_quantity // num_splits
        remainder = total_quantity % num_splits
        
        splits = []
        for i in range(num_splits):
            quantity = base_quantity + (1 if i < remainder else 0)
            
            # 時間分散（5分間隔で注文）
            delay_minutes = i * 5
            
            splits.append({
                'order_num': i + 1,
                'quantity': quantity,
                'delay_minutes': delay_minutes,
                'timing': f"{delay_minutes}分後に発注"
            })
        
        return splits
    
    def estimate_price_impact(self, order_value: float, 
                             avg_daily_volume: float) -> float:
        """
        注文による価格への影響を推定
        
        Args:
            order_value: 注文金額（円）
            avg_daily_volume: 平均日次出来高（円）
            
        Returns:
            推定価格影響（%）
        """
        if avg_daily_volume <= 0:
            return 0
        
        # 簡易モデル: 注文が日次出来高の何%かで影響を推定
        order_pct = order_value / avg_daily_volume
        
        # 10%以上で大きな影響
        if order_pct > 0.10:
            impact = order_pct * 2.0  # 20%以上の価格影響
        elif order_pct > 0.05:
            impact = order_pct * 1.5  # 7.5%程度の影響
        else:
            impact = order_pct * 0.5  # 2.5%以下の影響
        
        return min(impact, 0.50)  # 最大50%に制限


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    analyzer = LiquidityAnalyzer()
    
    print("=== Liquidity Analyzer Test ===\n")
    
    # テスト1: 最適取引時間
    times = analyzer.get_optimal_trading_times()
    print("推奨取引時間:")
    print(f"  最適: {times['best_times']}")
    print(f"  避ける: {times['avoid_times']}\n")
    
    # テスト2: タイミングチェック
    test_times = [
        time(9, 15),   # 寄り付き直後
        time(12, 0),   # 昼休み
        time(14, 45)   # 引け前
    ]
    
    for t in test_times:
        is_good, reason = analyzer.is_good_timing(t)
        print(f"{t.strftime('%H:%M')}: {'✅' if is_good else '❌'} {reason}")
    print()
    
    # テスト3: VWAPシグナル
    current_price = 1000
    vwap = 1050
    
    signal = analyzer.get_vwap_signal(current_price, vwap)
    print(f"VWAPシグナル: {signal['signal']}")
    print(f"理由: {signal['reason']}\n")
    
    # テスト4: 大口注文分割
    splits = analyzer.split_large_order(1000, num_splits=5)
    print("大口注文分割:")
    for split in splits:
        print(f"  #{split['order_num']}: {split['quantity']}株 - {split['timing']}")
