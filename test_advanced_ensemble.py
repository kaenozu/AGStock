"""
統合アンサンブル予測の動作確認
LSTM + LightGBM + Prophet + SMA + Fundamentals
"""
import sys
from unittest.mock import MagicMock

# Streamlitをモック
st_mock = MagicMock()
st_mock.cache_data = lambda **kwargs: lambda f: f
sys.modules['streamlit'] = st_mock

from src.data_loader import fetch_stock_data, fetch_fundamental_data
from src.ensemble_predictor import EnsemblePredictor

def verify_advanced_ensemble():
    print("🔍 統合アンサンブル予測の動作確認を開始します...")
    
    # データ取得
    print("\n📥 データ取得中...")
    ticker = "8308.T"
    data_map = fetch_stock_data([ticker], period="2y")
    
    if ticker not in data_map or data_map[ticker].empty:
        print(f"❌ エラー: {ticker} のデータを取得できませんでした")
        return
    
    df = data_map[ticker]
    print(f"✅ データ取得成功: {len(df)}件")
    
    # ファンダメンタルズデータ取得
    print("\n📊 ファンダメンタルズデータ取得中...")
    fundamentals = fetch_fundamental_data(ticker)
    if fundamentals:
        print(f"✅ ファンダメンタルズ取得成功")
        print(f"   P/E: {fundamentals.get('trailingPE', 'N/A')}")
        print(f"   P/B: {fundamentals.get('priceToBook', 'N/A')}")
    else:
        print("⚠️ ファンダメンタルズデータなし（予測は実行可能）")
    
    # 統合アンサンブル予測実行
    print("\n🔮 統合アンサンブル予測実行中...")
    predictor = EnsemblePredictor()
    result = predictor.predict_trajectory(
        df, 
        days_ahead=5,
        ticker=ticker,
        fundamentals=fundamentals
    )
    
    if "error" in result:
        print(f"❌ 予測エラー: {result['error']}")
    else:
        print(f"\n✅ 予測成功!")
        print(f"   トレンド: {result['trend']}")
        print(f"   変動予想: {result['change_pct']:.2f}%")
        print(f"   現在価格: ¥{result['current_price']:.2f}")
        print(f"   ピーク予想: {result['peak_day']}日後 @ ¥{result['peak_price']:.2f}")
        
        # 詳細情報
        if 'details' in result:
            details = result['details']
            print(f"\n📊 詳細:")
            print(f"   使用モデル: {', '.join(details.get('models_used', []))}")
            print(f"\n   各モデルの予測:")
            print(f"   - LSTM: {details.get('lstm_trend', 'N/A')}")
            print(f"   - LightGBM: {details.get('lgbm_trend', 'N/A')}")
            print(f"   - Prophet: {details.get('prophet_trend', 'N/A')}")
            print(f"   - SMA: {details.get('sma_trend', 'N/A')}")
            
            print(f"\n   投票結果: {details.get('trend_votes', {})}")
            
            if details.get('fundamental'):
                fund = details['fundamental']
                print(f"\n   ファンダメンタルズ評価:")
                print(f"   - 評価: {fund.get('valuation', 'N/A')}")
                print(f"   - スコア: {fund.get('score', 'N/A')}/100")
                print(f"   - 信頼度乗数: {fund.get('confidence_multiplier', 1.0):.2f}")
    
    print("\n✅ 動作確認完了")

if __name__ == "__main__":
    verify_advanced_ensemble()
