"""保有銘柄の詳細分析"""
import pandas as pd
from src.paper_trader import PaperTrader
from src.data_loader import fetch_fundamental_data
import yfinance as yf

pt = PaperTrader()
positions = pt.get_positions()

if positions.empty:
    print("ポジションがありません")
    exit()

print("=" * 80)
print("📊 保有銘柄の詳細分析")
print("=" * 80)

# 銘柄リストを取得
tickers = positions['ticker'].tolist()

print(f"\n保有銘柄数: {len(tickers)}")
print("\n銘柄一覧:")
for i, ticker in enumerate(tickers, 1):
    print(f"{i:2d}. {ticker}")

# 業種分散を確認
print("\n" + "=" * 80)
print("📈 業種分散分析")
print("=" * 80)

sectors = {}
market_caps = {}
regions = {}

for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        sector = info.get('sector', '不明')
        market_cap = info.get('marketCap', 0)
        country = info.get('country', '不明')
        
        # 業種
        sectors[sector] = sectors.get(sector, 0) + 1
        
        # 時価総額カテゴリ
        if market_cap > 10**12:  # 1兆円以上
            cap_cat = '超大型株'
        elif market_cap > 10**11:  # 1000億円以上
            cap_cat = '大型株'
        elif market_cap > 10**10:  # 100億円以上
            cap_cat = '中型株'
        else:
            cap_cat = '小型株'
        
        market_caps[cap_cat] = market_caps.get(cap_cat, 0) + 1
        
        # 地域
        if country == 'Japan':
            region = '日本'
        elif country == 'United States':
            region = '米国'
        elif country in ['Germany', 'France', 'United Kingdom']:
            region = '欧州'
        else:
            region = 'その他'
        
        regions[region] = regions.get(region, 0) + 1
        
    except Exception as e:
        print(f"⚠️ {ticker}: データ取得エラー")

print("\n業種別内訳:")
for sector, count in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
    pct = (count / len(tickers)) * 100
    print(f"  {sector}: {count}銘柄 ({pct:.1f}%)")

print("\n時価総額別内訳:")
for cap, count in sorted(market_caps.items(), key=lambda x: x[1], reverse=True):
    pct = (count / len(tickers)) * 100
    print(f"  {cap}: {count}銘柄 ({pct:.1f}%)")

print("\n地域別内訳:")
for region, count in sorted(regions.items(), key=lambda x: x[1], reverse=True):
    pct = (count / len(tickers)) * 100
    print(f"  {region}: {count}銘柄 ({pct:.1f}%)")

# 集中度チェック
print("\n" + "=" * 80)
print("⚠️ リスク評価")
print("=" * 80)

# 業種集中度
if sectors:
    max_sector = max(sectors.values())
    max_sector_pct = (max_sector / len(tickers)) * 100
    
    print(f"\n最大業種集中度: {max_sector_pct:.1f}%")
    if max_sector_pct > 40:
        print("  ❌ 特定業種に偏りすぎています（40%超）")
    elif max_sector_pct > 30:
        print("  ⚠️ やや偏りがあります（30-40%）")
    else:
        print("  ✅ 適切な分散です（30%以下）")

# 地域集中度
if regions:
    max_region = max(regions.values())
    max_region_pct = (max_region / len(tickers)) * 100
    
    print(f"\n最大地域集中度: {max_region_pct:.1f}%")
    if max_region_pct > 80:
        print("  ❌ 特定地域に偏りすぎています（80%超）")
    elif max_region_pct > 60:
        print("  ⚠️ やや偏りがあります（60-80%）")
    else:
        print("  ✅ 適切な分散です（60%以下）")

print("\n" + "=" * 80)
