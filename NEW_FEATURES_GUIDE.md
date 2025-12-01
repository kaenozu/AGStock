# 🚀 新機能活用ガイド - Phase 11-18

このガイドでは、Phase 11-18で実装した新機能を実際に活用する方法を説明します。

## 📚 目次

1. [動的アンサンブルの使用](#1-動的アンサンブルの使用)
2. [高度な特徴量の活用](#2-高度な特徴量の活用)
3. [外部データの統合](#3-外部データの統合)
4. [Transformer最適化](#4-transformer最適化)
5. [クロスバリデーション](#5-クロスバリデーション)
6. [GRU/Attention-LSTMモデル](#6-gruattention-lstmモデル)
7. [メタラーニング](#7-メタラーニング)

---

## 1. 動的アンサンブルの使用

### コード例

```python
from src.dynamic_ensemble import DynamicEnsemble
from src.strategies import LightGBMStrategy, DeepLearningStrategy

# 戦略を定義
strategies = {
    'LightGBM': LightGBMStrategy(),
    'LSTM': DeepLearningStrategy()
}

# 動的アンサンブルを初期化
ensemble = DynamicEnsemble(strategies, window_size=30, learning_rate=0.1)

# 予測を実行
predictions = ensemble.predict(strategies_predictions)

# パフォーマンスを更新（実際の結果が判明したら）
ensemble.update_performance(actual_value, predictions)
```

### ダッシュボードでの使用

1. `app.py` を起動
2. サイドバーで戦略に「Ensemble」を選択
3. 自動的に複数モデルの予測がウェイト付けされます

### 確認方法

```python
# 現在のウェイトを確認
print(ensemble.weights)
# 出力例: {'LightGBM': 0.6, 'LSTM': 0.4}

# パフォーマンス履歴を確認
print(ensemble.history[-5:])  # 直近5件
```

---

## 2. 高度な特徴量の活用

### 使用可能な特徴量

```python
from src.advanced_features import generate_all_advanced_features

# 全ての高度な特徴量を生成
df_enhanced = generate_all_advanced_features(df)

# 利用可能な特徴量:
# - lag_1, lag_3, lag_5, lag_10, lag_20 (ラグ特徴量)
# - log_return_1, log_return_5, log_return_10 (対数リターン)
# - rolling_std_5, rolling_std_10, rolling_std_20 (ローリング標準偏差)
# - skewness_20, kurtosis_20 (歪度、尖度)
# - zscore_20 (Zスコア)
# - ADX_14, CCI_14, RSI_14, MACD_12_26_9 (トレンド指標)
```

### カスタマイズ

```python
from src.advanced_features import add_lag_features, add_trend_features

# ラグ特徴量のみ追加
df = add_lag_features(df, lags=[1, 3, 5])

# トレンド指標のみ追加
df = add_trend_features(df)
```

---

## 3. 外部データの統合

### 利用可能なデータ

```python
from src.data_loader import fetch_external_data

# 外部データを取得
external_data = fetch_external_data(period='1y')

# 利用可能なデータ:
# - VIX: 恐怖指数
# - USDJPY: 為替レート
# - US10Y: 米国債10年利回り
# - SP500: S&P500指数
# - NIKKEI: 日経平均
# - GOLD: 金価格
# - OIL: 原油価格
```

### 特徴量への統合

```python
# 特徴量生成時に自動的に統合されます
from src.features import add_advanced_features

df_with_external = add_advanced_features(df)
# 外部データが自動的にマージされます
```

---

## 4. Transformer最適化

### 最適化の実行

```python
from src.optimization import HyperparameterOptimizer

optimizer = HyperparameterOptimizer()

# Transformerのハイパーパラメータを最適化
best_params = optimizer.optimize_transformer(df, n_trials=20)

print(best_params)
# 出力例:
# {
#   'hidden_size': 64,
#   'num_attention_heads': 4,
#   'learning_rate': 0.001,
#   'dropout': 0.2
# }
```

### 最適化されたパラメータの使用

```python
from src.transformer_model import TemporalFusionTransformer

# 最適化されたパラメータでモデル作成
model = TemporalFusionTransformer(
    input_size=10,
    **best_params
)
```

---

## 5. クロスバリデーション

### TimeSeriesSplitの使用

```python
from src.cross_validation import TimeSeriesCV
from sklearn.metrics import mean_squared_error

# クロスバリデーション初期化
tscv = TimeSeriesCV(n_splits=5)

# モデル評価
results = tscv.evaluate_model(
    model=your_model,
    X=features,
    y=target,
    metric_func=mean_squared_error
)

print(f"平均スコア: {results['mean_score']:.4f}")
print(f"標準偏差: {results['std_score']:.4f}")
```

### Walk-forward Validationの使用

```python
from src.cross_validation import walk_forward_validation

results = walk_forward_validation(
    model=your_model,
    X=features,
    y=target,
    train_window=200,
    test_window=50,
    step=10,
    metric_func=mean_squared_error
)

print(f"平均スコア: {results['mean_score']:.4f}")
```

---

## 6. GRU/Attention-LSTMモデル

### GRUStrategyの使用

```python
from src.strategies import GRUStrategy

# GRU戦略を初期化
gru_strategy = GRUStrategy(name="GRU_Advanced")

# 学習データで訓練
gru_strategy.train(train_df)

# シグナル生成
signal = gru_strategy.generate_signal(current_df)
print(f"シグナル: {signal}")  # 'BUY', 'SELL', または 'HOLD'
```

### Attention-LSTMStrategyの使用

```python
from src.strategies import AttentionLSTMStrategy

# Attention-LSTM戦略を初期化
attention_strategy = AttentionLSTMStrategy(name="AttentionLSTM")

# 学習
attention_strategy.train(train_df)

# 予測
signal = attention_strategy.generate_signal(current_df)
```

---

## 7. メタラーニング

### メタラーニングの設定

```python
from src.meta_learner import MetaLearner
import pandas as pd

# ベースモデルの予測を準備
base_predictions = pd.DataFrame({
    'LightGBM': lgbm_predictions,
    'LSTM': lstm_predictions,
    'GRU': gru_predictions,
    'Transformer': transformer_predictions
})

# メタラーナーを初期化
meta_learner = MetaLearner()

# 訓練
meta_learner.train(
    base_predictions=base_predictions_train,
    y_true=y_train
)

# 予測
final_predictions = meta_learner.predict(
    base_predictions=base_predictions_test
)
```

### ダッシュボードでの確認

メタラーニングは自動的に以下のタブで使用されます：
- **市場スキャン**: 複数戦略の予測を統合
- **バックテスト**: メタラーニング戦略として選択可能

---

## 🎯 実践例：完全なワークフロー

```python
# 1. データ取得
from src.data_loader import fetch_stock_data, fetch_external_data

stock_data = fetch_stock_data(['^N225'], period='2y')['^N225']
external_data = fetch_external_data(period='2y')

# 2. 高度な特徴量生成
from src.advanced_features import generate_all_advanced_features

enhanced_data = generate_all_advanced_features(stock_data)

# 3. データ分割
train_size = int(len(enhanced_data) * 0.8)
train_df = enhanced_data[:train_size]
test_df = enhanced_data[train_size:]

# 4. 複数モデルで訓練
from src.strategies import LightGBMStrategy, GRUStrategy, TransformerStrategy

strategies = {
    'LightGBM': LightGBMStrategy(),
    'GRU': GRUStrategy(),
    'Transformer': TransformerStrategy()
}

for name, strategy in strategies.items():
    strategy.train(train_df)
    print(f"{name} 訓練完了")

# 5. 動的アンサンブルで統合
from src.dynamic_ensemble import DynamicEnsemble

ensemble = DynamicEnsemble(strategies)

# 6. 予測とバックテスト
# (ダッシュボードで実行)
```

---

## 📊 バックテストでの検証

### Streamlitダッシュボードでの手順

1. **起動**:
   ```bash
   streamlit run app.py
   ```

2. **バックテストタブを開く**

3. **新戦略を選択**:
   - Ensemble（動的アンサンブル）
   - MetaLearner（メタラーニング）
   - GRU
   - AttentionLSTM

4. **パフォーマンス比較**:
   - シャープレシオ
   - 年間リターン
   - 最大ドローダウン
   - 勝率

---

## 🔧 トラブルシューティング

### よくある問題

1. **メモリ不足**:
   ```python
   # バッチサイズを小さくする
   model.fit(X, y, batch_size=16)  # デフォルト: 32
   ```

2. **学習時間が長い**:
   ```python
   # エポック数を減らす
   model.fit(X, y, epochs=10)  # デフォルト: 50
   
   # Optunaのトライアル数を減らす
   optimizer.optimize_transformer(df, n_trials=5)  # デフォルト: 10
   ```

3. **精度が低い**:
   ```python
   # より多くの特徴量を使用
   df = generate_all_advanced_features(df)
   
   # クロスバリデーションで評価
   results = tscv.evaluate_model(model, X, y, metric_func)
   ```

---

## 📈 次のステップ

1. **効果測定**: バックテストで実際の精度向上を確認
2. **パラメータ調整**: 自分のデータに最適なパラメータを探索
3. **本番適用**: ペーパートレードで実運用テスト

---

*最終更新: 2025-11-27*
