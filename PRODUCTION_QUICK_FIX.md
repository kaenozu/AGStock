# 🔧 実運用準備 - 6分で完了

**現在の評価:** 🟡 B (良好)  
**目標評価:** 🟢 A (優秀)

---

## ⚡ クイック修正 (6分)

### ステップ1: scikit-learnインストール (1分)

```bash
pip install scikit-learn
```

**または、すべてのパッケージを一括インストール:**

```bash
pip install -r requirements.txt
```

**確認:**
```bash
python -c "import sklearn; print('✅ scikit-learn OK')"
```

---

### ステップ2: 設定ファイル再作成 (3分)

```bash
python setup_wizard.py
```

**質問に答えるだけ:**
1. 投資経験は? → 選択
2. 初期資金は? → 入力
3. リスク許容度は? → 選択
4. 通知方法は? → 選択
5. 自動化レベルは? → 選択

**確認:**
```bash
python -c "import json; json.load(open('config.json')); print('✅ config.json OK')"
```

---

### ステップ3: 再チェック (1分)

```bash
python production_readiness_check.py
```

**期待される結果:**
```
🟢 総合評価: A (優秀)
✅ すべてのチェックに合格しました!
✅ 実運用に問題ありません!
```

---

### ステップ4: 起動確認 (1分)

```bash
run_unified_dashboard.bat
```

**確認項目:**
- ✅ ブラウザが開く
- ✅ ダッシュボードが表示される
- ✅ エラーが出ない

---

## 📋 チェックリスト

実行前:
- [ ] Python 3.8以上がインストールされている
- [ ] インターネット接続がある
- [ ] 管理者権限がある (パッケージインストール用)

実行後:
- [ ] scikit-learnがインストールされた
- [ ] config.jsonが作成された
- [ ] 再チェックで評価Aになった
- [ ] ダッシュボードが起動した

---

## 🎯 完了!

すべてのステップが完了したら:

```bash
# 最終確認
python production_readiness_check.py
```

**期待される出力:**
```
======================================================================
  🎉 実運用準備完了!
======================================================================
```

---

## 💡 トラブルシューティング

### Q: pip installでエラーが出る

**A:** 管理者権限で実行してください:
```bash
# Windowsの場合
# PowerShellを管理者として実行
pip install scikit-learn
```

### Q: setup_wizard.pyでエラーが出る

**A:** 既存のconfig.jsonを削除してから再実行:
```bash
del config.json
python setup_wizard.py
```

### Q: ダッシュボードが起動しない

**A:** ポートが使用中の可能性:
```bash
# 別のポートで起動
streamlit run unified_dashboard.py --server.port 8501
```

---

## 🚀 次のステップ

実運用準備が完了したら:

1. **GETTING_STARTED.md** を読む
2. **1週間お試し運用**
3. **週末に振り返り**

---

**🎉 それでは、実運用を開始しましょう!**

---

*作成日: 2025-12-02*
