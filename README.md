# AGStock - AI Trading System

グローバル株式市場（日本・米国・欧州）を対象とした、AI駆動の自動トレーディングシステム。

## 🚀 クイックスタート

### 1. セットアップ（初回のみ）
```bash
# Windows
setup.bat

# Mac/Linux
chmod +x setup.sh
./setup.sh
```

### 2. アプリ起動
```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動で開きます。

---

## 📊 主な機能

### 1. Market Scan（市場スキャン）
- 全銘柄を自動スキャンして有望なシグナルを検出
- 6つの戦略（RSI, Bollinger, Combined, ML, LightGBM）
- ワンクリックでペーパートレードに反映

### 2. Portfolio Simulation（ポートフォリオ）
- 複数銘柄の組み合わせをシミュレーション
- 相関行列で分散投資を最適化
- シャープレシオ最大化ポートフォリオ自動計算

### 3. Paper Trading（仮想取引）
- 1000万円の仮想資金でリアルタイム取引
- 全取引履歴を記録
- 日次資産推移グラフ

### 4. Dashboard（ダッシュボード）
- パフォーマンス・ヒートマップ
- トップ/ワースト銘柄
- アラート設定

---

## 🤖 自動実行

### 毎日自動でスキャン
```bash
python auto_trader.py
```

### GitHub Actionsで完全自動化
- 毎日17:00 JST に自動実行
- 結果は `reports/` フォルダに保存
- エラー時は自動でIssue作成

設定方法: `.github/ACTIONS_SETUP.md` 参照

---

## 🔔 通知設定

### Slack通知
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### メール通知
```bash
export EMAIL_ENABLED="true"
export EMAIL_FROM="your@email.com"
export EMAIL_PASSWORD="your-app-password"
export EMAIL_TO="recipient@email.com"
```

---

## 📈 バックテスト結果

**LightGBM戦略（過去2年間、グローバル20銘柄）**:
- 平均リターン: **+18.4%**
- シャープレシオ: **0.91**
- 勝率: **90%**

詳細: `python backtest_report.py` で最新レポート生成

---

## 🛠️ よく使うコマンド

```bash
# バックテストレポート生成
python backtest_report.py

# 自動トレーダー実行
python auto_trader.py

# データバックアップ
python backup.py

# アプリ起動
streamlit run app.py
```

---

## 📁 プロジェクト構成

```
AGStock/
├── app.py                  # メインアプリ
├── auto_trader.py          # 自動トレーダー
├── backtest_report.py      # レポート生成
├── backup.py               # バックアップ
├── src/
│   ├── strategies.py       # 取引戦略
│   ├── backtester.py       # バックテストエンジン
│   ├── portfolio.py        # ポートフォリオ管理
│   ├── paper_trader.py     # 仮想取引
│   ├── execution.py        # 注文実行
│   ├── notifier.py         # 通知システム
│   ├── features.py         # 特徴量エンジニアリング
│   └── data_loader.py      # データ取得
├── .github/workflows/      # GitHub Actions
└── reports/                # 実行結果（自動生成）
```

---

## 🔧 トラブルシューティング

### Q: データ取得が遅い
A: キャッシュが有効です。2回目以降は高速化されます。

### Q: LightGBMでエラー
A: `pip install --upgrade lightgbm` で最新版に更新

### Q: Paper Trading DBがリセットされた
A: `backup.py` で定期バックアップを推奨

### Q: GitHub Actionsが動かない
A: Secrets設定を確認（`.github/ACTIONS_SETUP.md` 参照）

---

## 📊 パフォーマンス追跡

月次・年次のパフォーマンスを確認:
```bash
streamlit run app.py
```
→ 「Dashboard」タブ → 「パフォーマンス追跡」

---

## 🎯 次のステップ

1. **初回セットアップ**: `setup.bat` 実行
2. **通知設定**: Slack/メール設定（任意）
3. **バックテスト確認**: `python backtest_report.py`
4. **アプリ起動**: `streamlit run app.py`
5. **自動化**: GitHub Actions設定（任意）

---

## 📝 ライセンス

個人利用のみ。
