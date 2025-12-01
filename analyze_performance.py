"""ペーパートレード実績分析"""
from src.paper_trader import PaperTrader

pt = PaperTrader()
history = pt.get_trade_history()
balance = pt.get_current_balance()
positions = pt.get_positions()

print("=" * 60)
print("📊 ペーパートレード実績")
print("=" * 60)

# 基本情報
print(f"\n💰 総資産: ¥{balance['total_equity']:,.0f}")
print(f"💵 現金: ¥{balance['cash']:,.0f}")
if 'invested_amount' in balance:
    print(f"📈 投資額: ¥{balance['invested_amount']:,.0f}")
if 'unrealized_pnl' in balance:
    print(f"📊 含み損益: ¥{balance['unrealized_pnl']:,.0f}")

# ポジション情報
print(f"\n📋 保有銘柄数: {len(positions)}")

# 取引実績
if 'realized_pnl' in history.columns:
    closed_trades = history[history['realized_pnl'] != 0]
    total_trades = len(closed_trades)
    
    if total_trades > 0:
        profitable = len(closed_trades[closed_trades['realized_pnl'] > 0])
        unprofitable = len(closed_trades[closed_trades['realized_pnl'] < 0])
        win_rate = (profitable / total_trades) * 100
        
        total_pnl = closed_trades['realized_pnl'].sum()
        avg_win = closed_trades[closed_trades['realized_pnl'] > 0]['realized_pnl'].mean() if profitable > 0 else 0
        avg_loss = closed_trades[closed_trades['realized_pnl'] < 0]['realized_pnl'].mean() if unprofitable > 0 else 0
        
        print(f"\n🎯 取引実績:")
        print(f"  総取引数: {total_trades}")
        print(f"  勝ちトレード: {profitable}")
        print(f"  負けトレード: {unprofitable}")
        print(f"  勝率: {win_rate:.1f}%")
        print(f"  総損益: ¥{total_pnl:,.0f}")
        print(f"  平均勝ち: ¥{avg_win:,.0f}")
        print(f"  平均負け: ¥{avg_loss:,.0f}")
        
        if avg_loss != 0:
            profit_factor = abs(avg_win * profitable / (avg_loss * unprofitable))
            print(f"  プロフィットファクター: {profit_factor:.2f}")
    else:
        print("\n⚠️ まだ決済された取引がありません")
else:
    print("\n⚠️ realized_pnlカラムが存在しません")

print("\n" + "=" * 60)
