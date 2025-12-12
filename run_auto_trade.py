"""
自動売買実行スクリプト
Windowsタスクスケジューラーから実行されることを想定
"""
import sys
import logging
from datetime import datetime
from pathlib import Path

# ロギング設定
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"auto_trade_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """自動売買のメイン処理"""
    logger.info("=" * 60)
    logger.info("自動売買スクリプト開始")
    logger.info("=" * 60)
    
    try:
        from src.trading.fully_automated_trader import FullyAutomatedTrader
        from src.paper_trader import PaperTrader
        
        trader = FullyAutomatedTrader()
        
        # 1. 安全チェック
        logger.info("安全チェック実行中...")
        is_safe, reason = trader.is_safe_to_trade()
        if not is_safe:
            logger.warning(f"取引を中止: {reason}")
            return
        
        logger.info("✓ 安全チェック合格")
        
        # 2. ポジション評価（決済シグナル）
        logger.info("保有ポジションを評価中...")
        exit_signals = trader.evaluate_positions()
        if exit_signals:
            logger.info(f"{len(exit_signals)}件の決済シグナルを検出")
            trader.execute_signals(exit_signals)
            logger.info("✓ 決済シグナル実行完了")
        else:
            logger.info("決済シグナルなし")
        
        # 3. 市場スキャン（購入シグナル）
        logger.info("市場スキャン開始...")
        buy_signals = trader.scan_market()
        if buy_signals:
            logger.info(f"{len(buy_signals)}件の購入シグナルを検出")
            trader.execute_signals(buy_signals)
            logger.info(f"✓ {len(buy_signals)}件の取引を実行")
        else:
            logger.info("購入シグナルなし")
        
        # 4. 価格更新
        logger.info("ポジション価格を更新中...")
        pt = PaperTrader()
        pt.update_daily_equity()
        logger.info("✓ 価格更新完了")
        
        # 5. サマリー表示
        balance = pt.get_current_balance()
        positions = pt.get_positions()
        
        logger.info("-" * 60)
        logger.info("実行結果サマリー")
        logger.info("-" * 60)
        logger.info(f"総資産: ¥{balance['total_equity']:,.0f}")
        logger.info(f"現金: ¥{balance['cash']:,.0f}")
        logger.info(f"保有銘柄数: {len(positions)}")
        logger.info(f"評価損益: ¥{balance['unrealized_pnl']:+,.0f}")
        logger.info("-" * 60)
        
        pt.close()
        
        logger.info("自動売買スクリプト正常終了")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
