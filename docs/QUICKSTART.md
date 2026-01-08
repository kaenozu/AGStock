# AGStock クイックスタートガイド

初めてAGStockを使う方向けの簡単セットアップガイドです。

## 📋 必要環境

- Python 3.10以上
- 4GB以上のメモリ
- インターネット接続

## 🚀 5分でスタート

### 1. リポジトリをクローン
```bash
git clone https://github.com/kaenozu/AGStock.git
cd AGStock
```

### 2. 仮想環境を作成（推奨）
```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. 依存関係をインストール
```bash
pip install -r requirements.txt
```

> ⚠️ 初回は5-10分かかります（TensorFlow等の大きなライブラリがあるため）

### 4. 設定ファイルを準備
```bash
cp .env.example .env
```

### 5. アプリを起動
```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動的に開きます。

---

## 🎮 基本的な使い方

### ダッシュボード
起動すると「🏠 ダッシュボード」タブが表示されます。

- **資産状況**: 現在の総資産、現金、評価損益
- **ポートフォリオ**: 保有銘柄一覧
- **市場状況**: VIX、主要指数

### ペーパートレード（仮想取引）
実際のお金を使わずに取引を練習できます。

1. 「💼 トレーディング」タブを開く
2. 銘柄を選択（例: 7203.T トヨタ）
3. 「分析」ボタンをクリック
4. AIの推奨を確認
5. 「買い」または「売り」を実行

> 初期資金は50万円（config.jsonで変更可能）

### 市場スキャン
AIが推奨銘柄を自動検出します。

1. 「🏠 ダッシュボード」タブ
2. 「市場をスキャンして推奨銘柄を探す」をクリック
3. 結果一覧から気になる銘柄を確認

---

## ⚙️ カスタマイズ

### 初期資金を変更
`config.json` を編集:
```json
{
  "paper_trading": {
    "initial_capital": 1000000
  }
}
```

### リスク設定を変更
```json
{
  "risk": {
    "max_position_size": 0.1,
    "stop_loss_pct": 0.03
  }
}
```

| 設定 | 説明 | デフォルト |
|------|------|-----------|
| max_position_size | 1銘柄の最大比率 | 10% |
| stop_loss_pct | 損切りライン | 3% |
| take_profit_pct | 利確ライン | 5% |

---

## 🔧 トラブルシューティング

### ポートが使用中
```bash
streamlit run app.py --server.port 8502
```

### メモリ不足
軽量モードで起動:
```bash
USE_DEMO_DATA=1 streamlit run app.py
```

### データが取得できない
- インターネット接続を確認
- yfinanceのレート制限の可能性（少し待ってから再試行）

---

## 📁 ディレクトリ構成

```
AGStock/
├── app.py              # メインアプリ
├── config.json         # 設定ファイル
├── .env                # 環境変数（APIキー等）
├── src/                # ソースコード
│   ├── strategies/     # 取引戦略
│   ├── ui/             # UI コンポーネント
│   └── trading/        # 取引ロジック
├── data/               # データ保存
├── logs/               # ログファイル
└── tests/              # テスト
```

---

## 🎯 次のステップ

1. **戦略を試す**: 「🧪 戦略研究所」でバックテスト
2. **AIを活用**: 「🤖 AI分析センター」で深い分析
3. **自動化**: スケジューラーで定期実行

詳細は [README.md](../README.md) を参照してください。

---

## ❓ よくある質問

**Q: 実際のお金で取引できる？**
A: 現在はペーパートレード（仮想取引）のみ対応。実取引には証券会社APIの設定が必要です。

**Q: APIキーは必要？**
A: 基本機能は不要。AI分析を使う場合はGemini APIキーを設定すると精度が上がります。

**Q: どの銘柄に対応？**
A: 日本株（.T）、米国株、一部の暗号資産・FXに対応。

---

*問題があれば [Issues](https://github.com/kaenozu/AGStock/issues) で報告してください*
