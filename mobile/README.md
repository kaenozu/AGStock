# AGStock モバイルアプリケーション

このディレクトリには、AGStockのモバイルアプリケーションが含まれています。

## 機能

- ポートフォリオサマリーの表示
- リアルタイム市場データの表示
- チャットボットとのインタラクション
- レスポンシブデザイン

## 必要条件

- Python 3.7以上
- Kivy 2.0.0以上

## インストール

```bash
pip install -r requirements.txt
```

## 実行

```bash
python main.py
```

## ビルド

### Android

```bash
# Buildozerのインストール
pip install buildozer

# specファイルの初期化
buildozer init

# Android APKのビルド
buildozer android debug
```

### iOS

```bash
# Kivy-iosのインストール
pip install kivy-ios

# ツールチェーンの設定
toolchain build python3 kivy

# Xcodeプロジェクトの生成
toolchain create agstock-mobile /path/to/mobile
```

## ディレクトリ構造

```
mobile/
├── main.py              # メインアプリケーション
├── requirements.txt     # 依存関係
├── buildozer.spec       # Androidビルド設定
├── README.md            # このファイル
└── assets/              # 画像やその他のアセット
```

## 機能詳細

### ポートフォリオ表示

- 総資産
- 現金残高
- 含み損益

### リアルタイムデータ

- 銘柄別の現在価格
- 価格変動率
- 出来高

### チャットボット

- Ghostwriterとのチャット
- ポートフォリオに関する質問
- 市場動向に関する質問

## カスタマイズ

### UIの変更

- `main.py`のBoxLayoutを編集
- 色やフォントの変更はKivyのプロパティを使用

### 機能の追加

- 新しいKivyウィジェットを追加
- AGStockの他のモジュールをインポート
- リアルタイムデータの処理を拡張

## トラブルシューティング

### Kivyのインストールエラー

```bash
# Ubuntu/Debian
sudo apt-get install python3-kivy

# macOS
brew install kivy

# Windows
pip install kivy[base]
```

### ビルドエラー

- buildozer.specファイルの設定を確認
- 必要なSDKやNDKがインストールされているか確認
