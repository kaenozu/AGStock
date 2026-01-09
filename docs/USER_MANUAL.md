# 📘 AGStock ユーザーマニュアル (v2.0)

AGStockへようこそ。このシステムは、AI（機械学習、LLM、量子最適化）を駆使した次世代の株式投資支援システムです。

## 1. クイックスタート

最も簡単にシステムを利用する方法は、統合ダッシュボードを起動することです。

```bash
# Windows
bin\START_SYSTEM.bat

# または直接起動
streamlit run app.py
```

## 2. 主要コンポーネント

### 🤖 AIアシスタント (AI Committee)
複数のAIエージェント（保守的、積極的、テクニカル）が合議制で銘柄を評価します。Gemini 1.5 Proなどの最新モデルを利用可能です。

### 🏆 シャドウトーナメント (Shadow Tournament)
4つの異なる「個性」を持つAIトレーダーが、仮想資金で競い合います。
- **狂犬 (Aggressive)**: 高リスク・高リターン
- **堅実 (Conservative)**: 資産保全重視
- **逆張り王 (Mean Reversion)**: 反発狙い
- **波乗り (Trend Follower)**: トレンド追従

### 📈 予測エンジン
- **LightGBM Alpha**: 高速な勾配ブースティング決定木による価格予測
- **LSTM Future Predictor**: 時系列ディープラーニングによる推移予測
- **Prophet**: Facebook開発の時系列予測ライブラリによるトレンド分析

## 3. 設定 (`config.json`)

システムの挙動は `config.json` でカスタマイズ可能です。

- `initial_capital`: ペーパートレードの初期資金
- `risk`: 損切り（stop_loss_pct）や利確（take_profit_pct）の設定
- `auto_trading`: 自動取引の有効化/無効化

## 4. APIサーバー

外部アプリや独自スクリプトからシステムを利用するためのAPIサーバーが搭載されています。

- **起動**: `python src/api/server.py`
- **エンドポイント**: `http://localhost:8000/docs` (Swagger UI)

## 5. メンテナンスとトラブルシューティング

- **環境チェック**: `python scripts/production_readiness_check.py` を実行して、システムの健康状態を確認してください。
- **ログ**: `logs/` ディレクトリに各コンポーネントの詳細な動作記録が保存されます。

---
© 2026 AGStock Development Team
