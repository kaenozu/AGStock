"""
8308.T の実データを使った動作確認
"""
import sys
from unittest.mock import MagicMock

# Streamlitをモック
st_mock = MagicMock()
st_mock.cache_data = lambda **kwargs: lambda f: f  # キャッシュを無効化
sys.modules["streamlit"] = st_mock

from src.data_loader import fetch_stock_data
from src.future_predictor import FuturePredictor

def verify_8308t():
    print("🔍 8308.T の動作確認を開始します...")
    
    # データ取得
    print("\n📥 データ取得中...")
    ticker = "8308.T"
    data_map = fetch_stock_data([ticker], period="2y")
    
    if ticker not in data_map or data_map[ticker].empty:
        print(f"❌ エラー: {ticker} のデータを取得できませんでした")
        return
    
    df = data_map[ticker]
    print(f"✅ データ取得成功: {len(df)}件")
    
    # 予測実行
    print("\n🔮 予測実行中...")
    predictor = FuturePredictor()
    result = predictor.predict_trajectory(df, days_ahead=5)
    
    if "error" in result:
        print(f"❌ 予測エラー: {result['error']}")
    else:
        print(f"✅ 予測成功!")
        print(f"   トレンド: {result['trend']}")
        print(f"   変動予想: {result['change_pct']:.2f}%")
        print(f"   現在価格: {result['current_price']:.2f}")
        print(f"   ピーク予想: {result['peak_day']}日後 @ {result['peak_price']:.2f}")
    
    print("\n✅ 動作確認完了")

if __name__ == "__main__":
    verify_8308t()
