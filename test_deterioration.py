"""
予測悪化チェックの動作確認スクリプト
"""
import sys
from unittest.mock import MagicMock
import pandas as pd

# Streamlitをモック
sys.modules["streamlit"] = MagicMock()

from src.advanced_risk import AdvancedRiskManager

def verify_deterioration_check():
    print("🔍 予測悪化チェックの動作確認を開始します...")
    
    # 1. 設定とマネージャーの初期化
    config = {"auto_trading": {}}
    risk_manager = AdvancedRiskManager(config)
    
    # 2. PaperTraderのモック
    pt_mock = MagicMock()
    
    # 保有ポジション: 8308.T (含み損あり)
    positions = pd.DataFrame({
        'current_price': [1563.0],
        'quantity': [100],
        'average_price': [1583.0],
        'unrealized_pnl_pct': [-1.26]
    }, index=['8308.T'])
    pt_mock.get_positions.return_value = positions
    
    # 3. FuturePredictorのモック
    # ここで予測結果を「悪化」させる
    predictor_instance = MagicMock()
    predictor_instance.predict_trajectory.return_value = {
        'change_pct': -3.5,  # -2.0%以下なので売却対象になるはず
        'trend': 'DOWN',
        'peak_price': 1500,
        'peak_day': 1
    }
    
    # モジュールをモック
    future_predictor_module = MagicMock()
    future_predictor_module.FuturePredictor = MagicMock(return_value=predictor_instance)
    sys.modules["src.future_predictor"] = future_predictor_module
    
    # すでにインポートされている場合はリロードが必要かもしれないが、
    # このスクリプト内ではまだインポートされていないはず。
    # 念のため src.advanced_risk 内でのインポートに影響するようにする。
    import src.advanced_risk
    
    # fetch_stock_dataのモック
    data_mock = pd.DataFrame({
        'Close': [100]*100,
        'Volume': [1000]*100,
        'High': [105]*100,
        'Low': [95]*100,
        'Open': [100]*100
    }) # ダミーデータ
    src.advanced_risk.fetch_stock_data = MagicMock(return_value={'8308.T': data_mock})
    
    # 4. チェック実行
    print("\n🧪 テスト実行: 予測が -3.5% に悪化した場合")
    logger = lambda msg, level="INFO": print(f"[{level}] {msg}")
    
    signals = risk_manager.check_prediction_deterioration(pt_mock, logger)
    
    # 5. 結果検証
    if signals:
        print(f"\n✅ シグナル検出: {len(signals)}件")
        for sig in signals:
            print(f"  - {sig['action']} {sig['ticker']}: {sig['reason']}")
            
        if signals[0]['ticker'] == '8308.T' and signals[0]['action'] == 'SELL':
            print("\n🎉 成功: 8308.T の売却シグナルが正しく生成されました")
        else:
            print("\n❌ 失敗: 期待されるシグナルと異なります")
    else:
        print("\n❌ 失敗: シグナルが生成されませんでした")

if __name__ == "__main__":
    verify_deterioration_check()
