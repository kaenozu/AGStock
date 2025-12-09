"""
The Ghostwriter (AI Weekly Reporter)
プロのヘッジファンドマネージャーのような週次レポートを自動執筆する
"""
import pandas as pd
import datetime
import os
import json
import logging
from src.paper_trader import PaperTrader
from src.llm_reasoner import LLMReasoner
from src.moe_system import MixtureOfExperts
from src.formatters import format_currency

logger = logging.getLogger(__name__)

class Ghostwriter:
    def __init__(self):
        self.pt = PaperTrader()
        self.llm = LLMReasoner() # Google Gemini or Ollama
        self.moe = MixtureOfExperts()
        self.reports_dir = "reports"
        
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)

    def generate_weekly_report(self) -> str:
        """週次レポートを生成して保存する"""
        logger.info("👻 Ghostwriter: Starting report generation...")
        
        # 1. データ収集
        data_summary = self._gather_weekly_data()
        
        # 2. LLMによる執筆
        report_content = self._write_report_with_llm(data_summary)
        
        # 3. 保存
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.reports_dir}/weekly_report_{timestamp}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        logger.info(f"👻 Ghostwriter: Report saved to {filename}")
        return filename

    def _gather_weekly_data(self) -> dict:
        """過去1週間のデータを収集"""
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=7)
        
        # 資産状況
        balance = self.pt.get_current_balance()
        history = self.pt.get_trade_history()
        
        # 週間取引
        weekly_trades = history[
            (pd.to_datetime(history['date']).dt.date >= start_date) & 
            (pd.to_datetime(history['date']).dt.date <= end_date)
        ] if not history.empty else pd.DataFrame()
        
        # 週間損益 (概算: 現在の総資産 - 1週間前の推定資産... は難しいので、確定損益の合計とする)
        realized_pnl = 0
        if not weekly_trades.empty:
            realized_pnl = weekly_trades['realized_pnl'].sum()
            
        # MoEステータス
        # 最新のレジームを取得（ダミーデータを使用せず、現在の市場データから取得すべきだが、
        # ここでは簡易的に直近の判断ロジックを呼び出すか、保存された状態があればそれを使う）
        # 今回は LLM に「現在の市場環境」として日経平均のトレンドを渡す
        from src.dashboard_utils import get_market_regime
        regime_info = get_market_regime()
        
        trades_detail = []
        if not weekly_trades.empty:
            # Timestamp対策: 日付を文字列に変換
            df_display = weekly_trades.copy()
            for col in df_display.columns:
                if pd.api.types.is_datetime64_any_dtype(df_display[col]):
                    df_display[col] = df_display[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            trades_detail = df_display.to_dict('records')
        
        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_equity": balance['total_equity'],
            "cash": balance['cash'],
            "realized_pnl": realized_pnl,
            "trade_count": len(weekly_trades),
            "trades_detail": trades_detail,
            "market_regime": regime_info
        }

    def _write_report_with_llm(self, data: dict) -> str:
        """LLMにレポートを書かせる"""
        
        prompt = f"""
あなたは世界最高峰のAIヘッジファンドマネージャーです。
投資家（ユーザー）に向けて、今週の運用報告レポート（週次レター）を執筆してください。

## 今週のデータ
- 期間: {data['start_date']} 〜 {data['end_date']}
- 総資産: {format_currency(data['total_equity'])}
- 現金余力: {format_currency(data['cash'])}
- 今週の確定損益: {format_currency(data['realized_pnl'])} ({data['trade_count']}回の取引)
- 現在の市場環境: {data['market_regime'].get('description', '不明') if data['market_regime'] else '不明'} (戦略: {data['market_regime'].get('strategy_desc', '不明') if data['market_regime'] else '不明'})

## 取引履歴
{json.dumps(data['trades_detail'], ensure_ascii=False, indent=2)}

## 執筆要件
1. **タイトル**: キャッチーでプロフェッショナルなタイトルをつけてください（例: "荒波を乗り越えて - Weekly Alpha Report"）。
2. **トーン**: 冷静かつ知性的ですが、情熱も感じさせる文体（"私" または "当ファンド" という主語を使用）。
3. **構成**:
    - **Executive Summary**: 今週の総括。市場がどう動き、我々がどう立ち回ったか。
    - **Performance Review**: 成績の分析。なぜ利益が出たか（または損失が出たか）の論理的説明。MoE（賢人会議）システムがどう機能したか（例：「強気相場のためBull Expertが指揮を執りました」など）に触れてください。
    - **Market Outlook**: 来週の展望と戦略。
4. **フォーマット**: Markdown形式で見やすく整形してください。
"""
        
        try:
            response = self.llm.ask(prompt)
            if "Error:" in response or "failed" in response:
                raise Exception(response)
            return response
        except Exception as e:
            logger.warning(f"LLM generation failed ({e}). Using template fallback.")
            return self._generate_fallback_report(data)

    def _generate_fallback_report(self, data: dict) -> str:
        """LLMが使えない場合のテンプレートレポート"""
        trend = "上昇" if data['market_regime']['regime'] == 'trending_up' else "下降" if data['market_regime']['regime'] == 'trending_down' else "横ばい"
        
        return f"""# 🌩️ Weekly Alpha Report (AI代筆モード)

## Executive Summary
今週の市場は{trend}傾向にありました。
AIシステムは市場の変動に合わせて {data['market_regime'].get('strategy_desc', '標準戦略')} を採用し、リスク管理を徹底しました。

## Performance Review
- **総資産**: {format_currency(data['total_equity'])}
- **確定損益**: {format_currency(data['realized_pnl'])}
- **取引回数**: {data['trade_count']}回

## Market Outlook
来週も市場のボラティリティに注意しつつ、MoEシステムによる最適なエキスパート割り当てで収益機会を狙います。
（※ 現在、LLM接続が利用できないため、簡易テンプレートで出力しています）
"""

if __name__ == "__main__":
    # Test run
    gw = Ghostwriter()
    print(gw.generate_weekly_report())
