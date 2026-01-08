# AGStock ロードマップ

## ✅ 実装完了

### Phase 1: 安定化 ✅
| 項目 | 状態 | 内容 |
|------|------|------|
| 依存関係軽量化 | ✅ | `src/utils/lazy_imports.py` - TensorFlow/PyTorch等の遅延読み込み |
| コード整理 | ✅ | `src/performance/` - パフォーマンス関連モジュール統合 |
| 設定統一 | ✅ | `src/core/config.py` - 統一設定管理 |

### Phase 2: 機能強化 ✅
| 項目 | 状態 | 内容 |
|------|------|------|
| API化 | ✅ | `src/api/server.py` - FastAPI内部API |
| ローカルLLM | ✅ | `src/llm/provider.py` - Ollama/Gemini/OpenAI統合 |

### Phase 3: アーキテクチャ刷新 ✅
| 項目 | 状態 | 内容 |
|------|------|------|
| プラグイン化 | ✅ | `src/plugins/` - 戦略プラグインシステム |

### Phase 4: UX向上 ✅
| 項目 | 状態 | 内容 |
|------|------|------|
| PWA対応 | ✅ | `src/ui/pwa.py` - プッシュ通知・テーマ |
| 税金計算 | ✅ | `src/tax/` - 確定申告用レポート |

---

## 📁 新規追加ファイル

```
src/
├── api/
│   ├── __init__.py
│   └── server.py          # FastAPI サーバー
├── core/
│   ├── config.py          # 統一設定管理
│   ├── logger.py          # 統一ロギング
│   └── exceptions.py      # 例外処理
├── llm/
│   ├── base.py            # LLM基底クラス
│   └── provider.py        # Ollama/Gemini/OpenAI統合
├── performance/
│   ├── metrics.py         # メトリクス計算
│   ├── analyzer.py        # パフォーマンス分析
│   ├── attribution.py     # アトリビューション
│   └── monitor.py         # 監視・アラート
├── plugins/
│   ├── base.py            # プラグイン基底クラス
│   └── manager.py         # プラグイン管理
├── tax/
│   ├── calculator.py      # 税金計算
│   └── report.py          # レポート生成
├── ui/
│   └── pwa.py             # PWAサポート
└── utils/
    └── lazy_imports.py    # 遅延インポート
```

---

## 🚀 使い方

### APIサーバー起動
```bash
python run_api.py --port 8000
# API Docs: http://localhost:8000/docs
```

### ローカルLLM使用（Ollama）
```bash
# Ollamaをインストール
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama2

# AGStockで使用
from src.llm import get_llm
llm = get_llm("ollama", "llama2")
response = llm.generate("Analyze this market...")
```

### カスタム戦略プラグイン
```bash
# plugins/ ディレクトリにファイルを配置
cp plugins/sample_strategy.py plugins/my_strategy.py

# 使用
from src.plugins import PluginManager
pm = PluginManager()
pm.discover_plugins()
pm.load_plugin("my_strategy")
```

### 税金レポート生成
```python
from src.tax import TaxReportGenerator
generator = TaxReportGenerator()
generator.export_excel(trades, filename="tax_2024.xlsx")
```

---

## 🔮 今後の予定

- [ ] WebSocket リアルタイムデータストリーム
- [ ] モバイルアプリ（React Native）
- [ ] 証券会社API連携（楽天、SBI）
- [ ] 自動売買の本番対応

---

*最終更新: 2025-01-08*
