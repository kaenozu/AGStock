"""
アンサンブル予測の動作確認
"""
import sys
from unittest.mock import MagicMock

# Streamlitをモック
st_mock = MagicMock()
st_mock.cache_data = lambda **kwargs: lambda f: f
sys.modules['streamlit'] = st_mock

from src.data_loader import fetch_stock_data
from src.ensemble_predictor import EnsemblePredictor

def verify_ensemble():
    print("🔍 アンサンブル予測の動作確認を開始します...")
    
    # データ取得
    print("\n📥 データ取得中...")
    ticker = "8308.T"
    data_map = fetch_stock_data([ticker], period="2y")
    
    if ticker not in data_map or data_map[ticker].empty:
        print(f"❌ エラー: {ticker} のデータを取得できませんでした")
        return
    
    df = data_map[ticker]
    print(f"✅ データ取得成功: {len(df)}件")
    
    # アンサンブル予測実行
    print("\n🔮 アンサンブル予測実行中...")
    predictor = EnsemblePredictor()
    result = predictor.predict_trajectory(df, days_ahead=5)
    
    if "error" in result:
        print(f"❌ 予測エラー: {result['error']}")
    else:
        print(f"✅ 予測成功!")
        print(f"   トレンド: {result['trend']}")
        print(f"   変動予想: {result['change_pct']:.2f}%")
        print(f"   現在価格: {result['current_price']:.2f}")
        print(f"   ピーク予想: {result['peak_day']}日後 @ {result['peak_price']:.2f}")
        
        # 詳細情報（各モデルの予測）
        if 'details' in result:
            details = result['details']
            print(f"\n📊 詳細:")
            print(f"   LSTM予測: {details.get('lstm_trend', 'N/A')}")
            print(f"   SMA予測: {details.get('sma_trend', 'N/A')}")
    
    print("\n✅ 動作確認完了")

if __name__ == "__main__":
    verify_ensemble()
