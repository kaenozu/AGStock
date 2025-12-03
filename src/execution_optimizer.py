"""
Execution Optimizer - 実行最適化

TWAP、VWAP、スマートオーダールーティング
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
import logging


class ExecutionOptimizer:
    """実行最適化クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_twap_schedule(self, total_quantity: int,
                                duration_minutes: int = 60,
                                slices: int = 12) -> List[Dict]:
        """
        TWAP（Time Weighted Average Price）スケジュールを計算
        
        Args:
            total_quantity: 総注文数
            duration_minutes: 実行期間（分）
            slices: 分割数
            
        Returns:
            実行スケジュール
        """
        quantity_per_slice = total_quantity // slices
        remainder = total_quantity % slices
        
        interval = duration_minutes / slices
        
        schedule = []
        cumulative = 0
        
        for i in range(slices):
            quantity = quantity_per_slice + (1 if i < remainder else 0)
            execution_time = datetime.now() + timedelta(minutes=i * interval)
            
            cumulative += quantity
            
            schedule.append({
                'slice': i + 1,
                'quantity': quantity,
                'execution_time': execution_time,
                'cumulative': cumulative,
                'progress_pct': (cumulative / total_quantity) * 100
            })
        
        return schedule
    
    def calculate_vwap_schedule(self, total_quantity: int,
                               volume_profile: List[float]) -> List[Dict]:
        """
        VWAP（Volume Weighted Average Price）スケジュールを計算
        
        出来高プロファイルに基づいて注文を配分
        
        Args:
            total_quantity: 総注文数
            volume_profile: 時間帯別の出来高比率
            
        Returns:
            実行スケジュール
        """
        total_volume = sum(volume_profile)
        
        schedule = []
        cumulative = 0
        
        for i, vol_pct in enumerate(volume_profile):
            quantity = int(total_quantity * (vol_pct / total_volume))
            cumulative += quantity
            
            schedule.append({
                'slice': i + 1,
                'quantity': quantity,
                'volume_pct': (vol_pct / total_volume) * 100,
                'cumulative': cumulative
            })
        
        # 端数調整
        diff = total_quantity - cumulative
        if diff != 0 and schedule:
            schedule[-1]['quantity'] += diff
            schedule[-1]['cumulative'] = total_quantity
        
        return schedule
    
    def calculate_implementation_shortfall(self, 
                                          decision_price: float,
                                          execution_prices: List[float],
                                          quantities: List[int]) -> Dict:
        """
        実装ショートフォールを計算
        
        意思決定時の価格と実際の執行価格の差
        
        Args:
            decision_price: 意思決定時の価格
            execution_prices: 各スライスの執行価格
            quantities: 各スライスの数量
            
        Returns:
            ショートフォール情報
        """
        total_quantity = sum(quantities)
        
        # 実際の平均執行価格
        weighted_price = sum(p * q for p, q in zip(execution_prices, quantities)) / total_quantity
        
        # ショートフォール
        shortfall = weighted_price - decision_price
        shortfall_pct = (shortfall / decision_price) * 100
        
        # コスト
        cost = shortfall * total_quantity
        
        return {
            'decision_price': decision_price,
            'average_execution_price': weighted_price,
            'shortfall': shortfall,
            'shortfall_pct': shortfall_pct,
            'total_cost': cost,
            'cost_per_share': shortfall
        }
    
    def optimize_order_routing(self, ticker: str,
                              quantity: int,
                              venues: Dict[str, Dict]) -> str:
        """
        スマートオーダールーティング
        
        複数の取引所から最良価格を選択
        
        Args:
            ticker: 銘柄コード
            quantity: 数量
            venues: 取引所情報 {name: {'bid': float, 'ask': float, 'size': int}}
            
        Returns:
            最適な取引所名
        """
        best_venue = None
        best_price = float('inf')
        
        for venue_name, info in venues.items():
            ask_price = info.get('ask', float('inf'))
            available_size = info.get('size', 0)
            
            # 数量が足りるか、価格が良いか
            if available_size >= quantity and ask_price < best_price:
                best_price = ask_price
                best_venue = venue_name
        
        return best_venue or list(venues.keys())[0]  # フォールバック
    
    def calculate_optimal_order_size(self, ticker_data: pd.DataFrame,
                                    target_participation_rate: float = 0.10) -> int:
        """
        最適注文サイズを計算
        
        市場への影響を最小化
        
        Args:
            ticker_data: 株価データ
            target_participation_rate: 目標参加率（出来高の何%か）
            
        Returns:
            推奨注文サイズ
        """
        if ticker_data.empty or 'Volume' not in ticker_data.columns:
            return 100  # デフォルト
        
        # 平均出来高
        avg_volume = ticker_data['Volume'].tail(20).mean()
        
        # 推奨サイズ
        recommended_size = int(avg_volume * target_participation_rate)
        
        return max(recommended_size, 100)  # 最低100株


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    optimizer = ExecutionOptimizer()
    
    print("=== Execution Optimizer Test ===\n")
    
    # TWAP
    twap_schedule = optimizer.calculate_twap_schedule(1000, duration_minutes=60, slices=10)
    print("TWAP スケジュール:")
    for s in twap_schedule[:3]:
        print(f"  スライス{s['slice']}: {s['quantity']}株 @ {s['execution_time']:%H:%M}")
    print(f"  ... (全{len(twap_schedule)}スライス)\n")
    
    # 実装ショートフォール
    shortfall = optimizer.calculate_implementation_shortfall(
        decision_price=1000,
        execution_prices=[1001, 1002, 1000.5, 999],
        quantities=[250, 250, 250, 250]
    )
    
    print("実装ショートフォール:")
    print(f"  意思決定価格: ¥{shortfall['decision_price']}")
    print(f"  平均執行価格: ¥{shortfall['average_execution_price']:.2f}")
    print(f"  ショートフォール: {shortfall['shortfall_pct']:.3f}%")
