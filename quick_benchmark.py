"""
簡易版 予測精度ベンチマーク
"""
import sys, os
sys.path.insert(0, os.getcwd())
import warnings
warnings.filterwarnings('ignore')

print("="*50)
print("📊 予測精度 簡易ベンチマーク")
print("="*50)

# データ取得
from src.data_loader import fetch_stock_data
print("\n📥 データ取得...")
data = fetch_stock_data(["7203.T"], period="1y")
df = data.get("7203.T")
print(f"データ: {len(df)}行")

# 1. 基本LightGBM
print("\n1️⃣ 基本 LightGBM テスト...")
from src.lgbm_predictor import LGBMPredictor
basic = LGBMPredictor()
result = basic.predict_trajectory(df, days_ahead=5)
print(f"   予測: {result.get('trend', 'N/A')}, {result.get('change_pct', 0):+.1f}%")

# 精度は過去20日で計算
correct = 0
total = 0
for i in range(20, 5, -1):
    try:
        train = df.iloc[:-i]
        res = basic.predict_trajectory(train, days_ahead=5)
        pred_up = res.get('trend') == 'UP' or res.get('change_pct', 0) > 0
        
        actual_i = len(df) - i
        actual_up = df['Close'].iloc[actual_i + 4] > df['Close'].iloc[actual_i]
        
        if pred_up == actual_up:
            correct += 1
        total += 1
    except:
        pass

basic_acc = correct / total if total > 0 else 0
print(f"   方向精度: {basic_acc:.0%} ({correct}/{total})")

# 2. アンサンブル
print("\n2️⃣ アンサンブル (5モデル) テスト...")
from src.ensemble_predictor import EnsemblePredictor
ensemble = EnsemblePredictor()
result = ensemble.predict_trajectory(df, days_ahead=5, ticker="7203.T")
print(f"   予測: {result.get('trend', 'N/A')}, {result.get('change_pct', 0):+.1f}%")

correct = 0
total = 0
for i in range(15, 5, -1):
    try:
        train = df.iloc[:-i]
        res = ensemble.predict_trajectory(train, days_ahead=5, ticker="TEST")
        pred_up = res.get('trend') == 'UP'
        
        actual_i = len(df) - i
        actual_up = df['Close'].iloc[actual_i + 4] > df['Close'].iloc[actual_i]
        
        if pred_up == actual_up:
            correct += 1
        total += 1
    except:
        pass

ensemble_acc = correct / total if total > 0 else 0
print(f"   方向精度: {ensemble_acc:.0%} ({correct}/{total})")

# 3. インテリジェントセレクター
print("\n3️⃣ インテリジェントセレクター テスト...")
from src.intelligent_auto_selector import get_auto_selector
selector = get_auto_selector()
result = selector.get_best_prediction(df, "7203.T")
auto_info = result.get('auto_selector', {})
print(f"   予測: {result.get('trend', 'N/A')}")
print(f"   信頼度: {auto_info.get('confidence_score', 0):.0%}")
print(f"   レベル: {auto_info.get('confidence_level', 'N/A')}")

# サマリー
print("\n" + "="*50)
print("📈 結果サマリー")
print("="*50)
print(f"\n{'モデル':<25} {'精度':>8}")
print("-"*35)
print(f"{'基本 LightGBM':<25} {basic_acc:>8.0%}")
print(f"{'アンサンブル (5モデル)':<25} {ensemble_acc:>8.0%}")

if basic_acc > 0:
    improvement = (ensemble_acc - basic_acc) / basic_acc * 100
    print(f"\n📊 アンサンブルによる改善: {improvement:+.0f}%")

print("\n✅ 完了")
