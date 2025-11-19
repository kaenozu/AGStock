# 📈 AGStock - 日本株 AI 予測アナライザー

過去のデータから統計的に最も期待値の高い売買シグナルを検出する株式分析アプリケーション。

## ✨ 機能

- **日経225銘柄のバックテスト**: 主要銘柄の過去データを分析
- **複数の戦略**: SMA Crossover、RSI、Bollinger Bands
- **リアルタイムシグナル検出**: 現在の市場状況に基づくシグナル
- **インタラクティブなUI**: Streamlitによる直感的な操作
- **詳細な分析**: チャートとメトリクスによる可視化

## 🚀 クイックスタート

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/kaenozu/AGStock.git
cd AGStock

# 依存関係をインストール
pip install -r requirements.txt
```

### 実行

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動的に開きます。

## 🧪 テスト

```bash
# テスト用依存関係をインストール
pip install -r requirements-dev.txt

# すべてのテストを実行
pytest tests/ -v

# カバレッジ付きで実行
pytest tests/ --cov=src --cov-report=html
```

## 📁 プロジェクト構造

```
AGStock/
├── app.py                 # Streamlitメインアプリケーション
├── src/
│   ├── strategies.py      # 戦略クラス（SMA、RSI、Bollinger Bands）
│   ├── backtester.py      # バックテスタークラス
│   ├── data_loader.py     # データ取得関数
│   └── constants.py       # 定数定義（ティッカーリスト）
├── tests/
│   ├── conftest.py        # pytest共通フィクスチャ
│   ├── test_strategies.py # 戦略テスト
│   ├── test_backtester.py # バックテスターテスト
│   ├── test_data_loader.py# データローダーテスト
│   └── test_constants.py  # 定数テスト
├── pytest.ini             # pytest設定
├── requirements.txt       # 本番依存関係
└── requirements-dev.txt   # 開発依存関係
```

## 🎯 使い方

1. **市場をスキャン**: 「市場をスキャンして推奨銘柄を探す」ボタンをクリック
2. **シグナルを確認**: 買い/売りシグナルが出ている銘柄を確認
3. **詳細分析**: 銘柄を選択してチャートとメトリクスを表示

## 🔧 戦略

### SMA Crossover
短期移動平均線と長期移動平均線のクロスオーバーを検出

### RSI
相対力指数（RSI）の過買い/過売りからの反転を検出

### Bollinger Bands
ボリンジャーバンドのタッチによる平均回帰を検出

## 📊 テストカバレッジ

- **57個のテスト**: すべてパス ✅
- **主要モジュール**: 戦略、バックテスター、データローダー、定数
- **型ヒント**: 全モジュールに型アノテーション付き

## 🤝 コントリビューション

プルリクエストを歓迎します！

1. フォークする
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. コミット (`git commit -m 'Add amazing feature'`)
4. プッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## ⚠️ 免責事項

このツールは教育目的で作成されています。実際の投資判断には使用しないでください。投資は自己責任で行ってください。
