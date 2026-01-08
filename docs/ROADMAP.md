# AGStock 今後の展望（ロードマップ）

## 📊 現状分析

| 項目 | 値 | 評価 |
|------|-----|------|
| Pythonファイル数 | 533 | ⚠️ 多い |
| 総行数 | ~96,000行 | ⚠️ 複雑 |
| テストファイル数 | 151 | ✅ 良好 |
| UIタブ数 | 14 | ⚠️ 多い |
| 戦略数 | 15+ | ✅ 豊富 |

---

## 🎯 Phase 1: 安定化（1-2ヶ月）

### 1.1 依存関係の軽量化
**目的**: 起動時間とメモリ使用量の改善

```
現状の重量級依存関係:
- tensorflow>=2.13.0  (~500MB)
- torch>=2.0.0        (~2GB)
- prophet>=1.1.0      (~200MB)
- transformers>=4.30.0 (~500MB)
```

**提案**:
- [ ] 遅延インポート（lazy loading）の徹底
- [ ] 軽量版モデル（ONNX Runtime）への移行検討
- [ ] 使用頻度の低いモデルをオプション化

### 1.2 コードの整理統合
**目的**: 保守性の向上

| 現状 | 提案 |
|------|------|
| `config.py`, `config_loader.py`, `config_manager.py` | `src/core/config.py`に統一 ✅完了 |
| `performance*.py` (8ファイル) | `src/performance/`に統合 |
| `logging_config.py`, `logger_config.py`, `log_config.py` | `src/core/logger.py`に統一 ✅完了 |

### 1.3 テストカバレッジ向上
- [ ] カバレッジ目標: 80%
- [ ] 統合テストの追加
- [ ] CI/CDパイプラインの強化

---

## 🚀 Phase 2: 機能強化（2-4ヶ月）

### 2.1 リアルタイム機能の強化
```python
# 現状: 30秒ごとのポーリング
@st.fragment(run_every="30s")
def render_realtime_stream():
    ...

# 提案: WebSocketによるリアルタイム更新
class RealtimeDataStream:
    async def connect(self):
        async with websockets.connect(ws_url) as ws:
            async for message in ws:
                yield json.loads(message)
```

### 2.2 バックテストの高速化
- [ ] Rustによるコア計算の高速化
- [ ] 並列バックテストの最適化
- [ ] 結果のキャッシュ戦略改善

### 2.3 AI分析の強化
- [ ] ローカルLLM対応（Ollama/LM Studio）
- [ ] マルチモーダル分析の実用化
- [ ] 説明可能AI（XAI）の強化

---

## 🏗️ Phase 3: アーキテクチャ刷新（4-6ヶ月）

### 3.1 モジュール分離

```
現状:
AGStock/
├── src/           # 533ファイルが混在
└── ...

提案:
AGStock/
├── agstock-core/      # コアロジック（取引、リスク管理）
├── agstock-ml/        # 機械学習モデル
├── agstock-ui/        # Streamlit UI
├── agstock-data/      # データ取得・管理
└── agstock-cli/       # CLIツール
```

### 3.2 API化
```python
# FastAPI による内部API化
from fastapi import FastAPI
app = FastAPI()

@app.get("/api/v1/portfolio")
async def get_portfolio():
    return portfolio_manager.get_summary()

@app.post("/api/v1/trade")
async def execute_trade(trade: TradeRequest):
    return trader.execute(trade)
```

**メリット**:
- UI とロジックの分離
- モバイルアプリ対応可能
- 外部システム連携

### 3.3 プラグインアーキテクチャ
```python
# 戦略のプラグイン化
class StrategyPlugin(Protocol):
    name: str
    version: str
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        ...
    
    def get_config_schema(self) -> dict:
        ...

# プラグインの動的読み込み
strategy_manager.load_plugin("custom_strategy.py")
```

---

## 📱 Phase 4: ユーザー体験向上（6ヶ月以降）

### 4.1 UI/UXの刷新
- [ ] ダッシュボードのカスタマイズ機能
- [ ] モバイルレスポンシブ対応
- [ ] ダークモード/ライトモード切替

### 4.2 通知・アラートの強化
- [ ] プッシュ通知（PWA対応）
- [ ] 条件付きアラート（価格、指標、AI判断）
- [ ] 通知の優先度設定

### 4.3 レポート機能
- [ ] 週次/月次レポートの自動生成
- [ ] 税金計算レポート（確定申告対応）
- [ ] パフォーマンス分析レポート

---

## 🔒 継続的な改善

### セキュリティ
- [ ] 定期的な依存関係の脆弱性スキャン
- [ ] APIキーのローテーション対応
- [ ] 監査ログの強化

### パフォーマンス
- [ ] 起動時間: 目標 < 5秒
- [ ] メモリ使用量: 目標 < 1GB
- [ ] バックテスト: 100銘柄×1年 < 10秒

### ドキュメント
- [ ] API ドキュメントの自動生成
- [ ] チュートリアルの充実
- [ ] FAQ の拡充

---

## 📅 優先度マトリクス

| 優先度 | 項目 | 工数 | 効果 |
|--------|------|------|------|
| 🔴 高 | 依存関係の軽量化 | 中 | 高 |
| 🔴 高 | パフォーマンス関連の統合 | 低 | 中 |
| 🟡 中 | リアルタイム機能強化 | 高 | 高 |
| 🟡 中 | ローカルLLM対応 | 中 | 中 |
| 🟢 低 | モジュール分離 | 高 | 高 |
| 🟢 低 | API化 | 高 | 高 |

---

## 💡 クイックウィン（すぐにできる改善）

1. **遅延インポートの追加**
```python
# Before
import tensorflow as tf

# After
def get_model():
    import tensorflow as tf
    return tf.keras.models.load_model(...)
```

2. **未使用コードの削除**
```bash
# 未使用ファイルの検出
vulture src/ --min-confidence 80
```

3. **設定のバリデーション**
```python
from pydantic import BaseModel

class TradingConfig(BaseModel):
    max_daily_trades: int = 5
    daily_loss_limit_pct: float = -3.0
```

---

*最終更新: 2025-01-08*
