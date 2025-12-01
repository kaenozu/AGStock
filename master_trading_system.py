"""
Master Trading System - 全機能統合システム

31機能を統合し、ワンクリックで最適な取引を実行
"""
import pandas as pd
from datetime import datetime
from typing import Dict, List
import logging

# 既存機能
from src.paper_trader import PaperTrader
from src.smart_notifier import SmartNotifier

# Phase 48機能
from src.backup_manager import BackupManager
from src.performance_monitor import get_performance_monitor
from src.mpt_optimizer import MPTOptimizer

# 利益改善機能
from src.psychological_guard import PsychologicalGuard
from src.macro_analyzer import MacroAnalyzer
from src.liquidity_analyzer import LiquidityAnalyzer
from src.dividend_strategy import DividendStrategy

# 高度な機能
from src.advanced_risk import AdvancedRiskManager
from src.auto_rebalancer import AutoRebalancer
from src.benchmark_comparator import BenchmarkComparator
from src.execution_optimizer import ExecutionOptimizer
from src.factor_analyzer import FactorAnalyzer


class MasterTradingSystem:
    """マスタートレーディングシステム - 全機能統合"""
    
    def __init__(self, config_path: str = "config.json"):
        self.logger = logging.getLogger(__name__)
        
        # コア機能
        self.pt = PaperTrader()
        self.notifier = SmartNotifier(config_path)
        
        # Phase 48
        self.backup_manager = BackupManager()
        self.performance_monitor = get_performance_monitor()
        self.mpt_optimizer = MPTOptimizer()
        
        # 利益改善
        self.psych_guard = PsychologicalGuard()
        self.macro_analyzer = MacroAnalyzer()
        self.liquidity_analyzer = LiquidityAnalyzer()
        self.dividend_strategy = DividendStrategy()
        
        # 高度な機能
        self.risk_manager = AdvancedRiskManager()
        self.rebalancer = AutoRebalancer()
        self.benchmark_comparator = BenchmarkComparator()
        self.execution_optimizer = ExecutionOptimizer()
        self.factor_analyzer = FactorAnalyzer()
        
        self.logger.info("Master Trading System initialized with 31 features")
    
    def daily_routine(self) -> Dict:
        """
        デイリールーチン - 毎日自動実行
        
        Returns:
            実行結果
        """
        self.logger.info("=== Daily Routine Started ===")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'steps': []
        }
        
        try:
            # 1. バックアップ
            backup_path = self.backup_manager.auto_backup()
            results['steps'].append({'step': 'backup', 'status': 'success', 'path': backup_path})
            
            # 2. マクロ分析
            macro_analysis = self.macro_analyzer.get_comprehensive_analysis()
            results['macro'] = macro_analysis
            results['steps'].append({'step': 'macro_analysis', 'status': 'success'})
            
            # 3. 市場環境チェック
            regime = macro_analysis['regime']
            if regime == 'リスクオフ':
                results['action'] = 'SKIP'
                results['reason'] = '市場環境が悪いため取引見送り'
                self.logger.warning("Market regime is RISK_OFF, skipping trades")
                return results
            
            # 4. 流動性チェック
            is_good_timing, timing_reason = self.liquidity_analyzer.is_good_timing()
            if not is_good_timing:
                results['action'] = 'WAIT'
                results['reason'] = timing_reason
                return results
            
            # 5. ポートフォリオ分析
            positions = self.pt.get_positions()
            balance = self.pt.get_current_balance()
            total_equity = balance['total_equity']
            
            # 6. VaR/CVaRチェック
            if not positions.empty:
                # ダミーのリターンデータ（実際は過去データから計算）
                returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02])
                var_info = self.risk_manager.calculate_portfolio_var(
                    positions, 
                    {'dummy': returns},
                    total_equity
                )
                results['risk'] = var_info
                results['steps'].append({'step': 'risk_analysis', 'status': 'success'})
            
            # 7. 心理的ガードチェック
            for _, pos in positions.iterrows():
                check = self.psych_guard.comprehensive_check(
                    pos.to_dict(),
                    peak_price=pos.get('entry_price', 0) * 1.1,
                    total_equity=total_equity
                )
                
                if check['action'] == 'SELL_NOW':
                    results['steps'].append({
                        'step': 'psychological_guard',
                        'ticker': pos['ticker'],
                        'action': 'SELL',
                        'reason': check['reason']
                    })
            
            # 8. リバランスチェック
            if not positions.empty:
                current_weights = {}
                for _, pos in positions.iterrows():
                    current_weights[pos['ticker']] = pos.get('market_value', 0) / total_equity
                
                target_weights = {
                    # 簡易的なターゲット（実際はMPTで計算）
                    pos['ticker']: 1 / len(positions) 
                    for _, pos in positions.iterrows()
                }
                
                should_rebal = self.rebalancer.should_rebalance(current_weights, target_weights)
                if should_rebal:
                    results['steps'].append({
                        'step': 'rebalance_check',
                        'action': 'REBALANCE_NEEDED'
                    })
            
            # 9. パフォーマンス記録
            self.performance_monitor.track_execution_time('daily_routine', 0)
            
            results['action'] = 'COMPLETED'
            results['status'] = 'success'
            
        except Exception as e:
            self.logger.error(f"Daily routine error: {e}")
            results['status'] = 'error'
            results['error'] = str(e)
        
        return results
    
    def get_today_recommendations(self) -> Dict:
        """
        今日のおすすめを取得
        
        Returns:
            推奨銘柄・アクション
        """
        recommendations = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'recommendations': []
        }
        
        # マクロ分析
        macro = self.macro_analyzer.get_comprehensive_analysis()
        recommendations['market_regime'] = macro['regime']
        recommendations['recommended_strategy'] = macro['recommended_strategy']
        recommendations['recommended_sectors'] = macro['recommended_sectors']
        
        # リスク状態
        positions = self.pt.get_positions()
        if not positions.empty:
            balance = self.pt.get_current_balance()
            returns = pd.Series([0.01, -0.02, 0.015])  # ダミー
            var_info = self.risk_manager.calculate_portfolio_var(
                positions,
                {'dummy': returns},
                balance['total_equity']
            )
            recommendations['risk_level'] = var_info.get('interpretation', 'Unknown')
        
        return recommendations
    
    def execute_smart_trade(self, ticker: str, action: str, quantity: int) -> Dict:
        """
        スマート取引実行 - 心理的ガード・流動性・実行最適化を適用
        
        Args:
            ticker: 銘柄コード
            action: BUY or SELL
            quantity: 数量
            
        Returns:
            実行結果
        """
        result = {
            'ticker': ticker,
            'action': action,
            'quantity': quantity,
            'checks': []
        }
        
        # 1. 流動性チェック
        is_good_timing, reason = self.liquidity_analyzer.is_good_timing()
        result['checks'].append({
            'check': 'liquidity',
            'passed': is_good_timing,
            'reason': reason
        })
        
        if not is_good_timing:
            result['executed'] = False
            result['reason'] = 'Bad liquidity timing'
            return result
        
        # 2. マクロチェック
        macro = self.macro_analyzer.get_market_regime()
        if macro.value == 'リスクオフ' and action == 'BUY':
            result['checks'].append({
                'check': 'macro',
                'passed': False,
                'reason': 'Risk-off environment'
            })
            result['executed'] = False
            result['reason'] = 'Market regime is risk-off'
            return result
        
        # 3. 心理的ガードチェック（売却時）
        if action == 'SELL':
            positions = self.pt.get_positions()
            if ticker in positions['ticker'].values:
                pos = positions[positions['ticker'] == ticker].iloc[0]
                balance = self.pt.get_current_balance()
                
                guard_check = self.psych_guard.comprehensive_check(
                    pos.to_dict(),
                    peak_price=pos.get('entry_price', 0) * 1.1,
                    total_equity=balance['total_equity']
                )
                
                result['checks'].append({
                    'check': 'psychological_guard',
                    'action': guard_check['action'],
                    'reason': guard_check.get('reason', 'OK')
                })
        
        # 4. 実行（ペーパートレード）
        try:
            price = 1000  # ダミー価格（実際はyfinanceから取得）
            
            if action == 'BUY':
                self.pt.execute_trade(ticker, 'BUY', quantity, price)
            else:
                self.pt.execute_trade(ticker, 'SELL', quantity, price)
            
            result['executed'] = True
            result['price'] = price
            result['timestamp'] = datetime.now().isoformat()
            
        except Exception as e:
            result['executed'] = False
            result['error'] = str(e)
        
        return result
    
    def generate_daily_report(self) -> str:
        """
        日次レポート生成
        
        Returns:
            レポート文字列
        """
        balance = self.pt.get_current_balance()
        positions = self.pt.get_positions()
        
        macro = self.macro_analyzer.get_comprehensive_analysis()
        
        report = f"""
📊 **AGStock 日次レポート**
日付: {datetime.now():%Y-%m-%d %H:%M}

【資産状況】
総資産: ¥{balance['total_equity']:,.0f}
現金: ¥{balance['cash']:,.0f}
投資額: ¥{balance.get('invested_amount', 0):,.0f}
含み損益: ¥{balance.get('unrealized_pnl', 0):+,.0f}

【市場環境】
{macro['regime']}
推奨戦略: {macro['recommended_strategy']}

【ポジション】
保有銘柄数: {len(positions)}
"""
        
        if not positions.empty:
            report += "\n銘柄:\n"
            for _, pos in positions.head(5).iterrows():
                report += f"  - {pos['ticker']}: {pos['quantity']}株\n"
        
        return report


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    system = MasterTradingSystem()
    
    print("=== Master Trading System Test ===\n")
    
    # デイリールーチン
    results = system.daily_routine()
    print(f"Daily routine: {results['status']}")
    print(f"Steps completed: {len(results['steps'])}\n")
    
    # 今日のおすすめ
    recommendations = system.get_today_recommendations()
    print(f"Market regime: {recommendations['market_regime']}")
    print(f"Strategy: {recommendations['recommended_strategy']}\n")
    
    # レポート生成
    report = system.generate_daily_report()
    print(report)
