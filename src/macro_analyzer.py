"""
Macro Analyzer - マクロ経済分析

経済指標を分析して市場環境を判定
"""
import yfinance as yf
from typing import Dict
from enum import Enum
import logging


class MarketRegime(Enum):
    """市場環境"""
    RISK_ON = "リスクオン"        # 攻めの相場
    NEUTRAL = "中立"              # 通常相場
    RISK_OFF = "リスクオフ"       # 守りの相場


class MacroAnalyzer:
    """マクロ経済分析クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_vix(self) -> float:
        """
        VIX指数（恐怖指数）を取得
        
        Returns:
            VIX値
        """
        try:
            vix = yf.Ticker("^VIX")
            data = vix.history(period="1d")
            
            if not data.empty:
                return data['Close'].iloc[-1]
        except Exception as e:
            self.logger.error(f"Failed to fetch VIX: {e}")
        
        return 20.0  # デフォルト値
    
    def get_interest_rate(self) -> float:
        """
        日本の政策金利を取得（簡易版）
        
        Returns:
            金利（%）
        """
        # 実際のAPIから取得すべきだが、簡易実装
        # 2024年現在は約0.1%
        return 0.1
    
    def get_usd_jpy(self) -> float:
        """
        USD/JPY為替レートを取得
        
        Returns:
            為替レート
        """
        try:
            forex = yf.Ticker("USDJPY=X")
            data = forex.history(period="1d")
            
            if not data.empty:
                return data['Close'].iloc[-1]
        except Exception as e:
            self.logger.error(f"Failed to fetch USD/JPY: {e}")
        
        return 150.0  # デフォルト値
    
    def get_nikkei_225(self) -> float:
        """
        日経225を取得
        
        Returns:
            日経225の値
        """
        try:
            nikkei = yf.Ticker("^N225")
            data = nikkei.history(period="1d")
            
            if not data.empty:
                return data['Close'].iloc[-1]
        except Exception as e:
            self.logger.error(f"Failed to fetch Nikkei: {e}")
        
        return 30000.0  # デフォルト値
    
    def get_market_regime(self) -> MarketRegime:
        """
        現在の市場環境を判定
        
        Returns:
            市場環境
        """
        vix = self.get_vix()
        
        if vix < 15:
            return MarketRegime.RISK_ON     # 低ボラティリティ → 攻め
        elif vix > 25:
            return MarketRegime.RISK_OFF    # 高ボラティリティ → 守り
        else:
            return MarketRegime.NEUTRAL     # 中間
    
    def get_comprehensive_analysis(self) -> Dict:
        """
        包括的なマクロ分析を実施
        
        Returns:
            分析結果
        """
        vix = self.get_vix()
        interest_rate = self.get_interest_rate()
        usd_jpy = self.get_usd_jpy()
        nikkei = self.get_nikkei_225()
        regime = self.get_market_regime()
        
        # 為替が150円以上なら円安
        fx_trend = "円安" if usd_jpy > 145 else "円高" if usd_jpy < 135 else "中立"
        
        # 推奨戦略
        if regime == MarketRegime.RISK_ON:
            recommended_strategy = "成長株・IT株中心の攻めの戦略"
            recommended_sectors = ["IT・通信", "消費", "テクノロジー"]
        elif regime == MarketRegime.RISK_OFF:
            recommended_strategy = "ディフェンシブ株中心の守りの戦略"
            recommended_sectors = ["生活必需品", "医薬品", "公益"]
        else:
            recommended_strategy = "バランス型戦略"
            recommended_sectors = ["金融", "IT・通信", "医薬品"]
        
        # FX影響
        if fx_trend == "円安":
            fx_beneficiaries = ["自動車", "電機（輸出企業）"]
        else:
            fx_beneficiaries = ["内需関連", "不動産"]
        
        return {
            'indicators': {
                'vix': vix,
                'interest_rate': interest_rate,
                'usd_jpy': usd_jpy,
                'nikkei_225': nikkei
            },
            'regime': regime.value,
            'fx_trend': fx_trend,
            'recommended_strategy': recommended_strategy,
            'recommended_sectors': recommended_sectors,
            'fx_beneficiaries': fx_beneficiaries,
            'summary': self._generate_summary(vix, regime, fx_trend)
        }
    
    def _generate_summary(self, vix: float, regime: MarketRegime, fx_trend: str) -> str:
        """
        サマリーを生成
        
        Args:
            vix: VIX値
            regime: 市場環境
            fx_trend: 為替トレンド
            
        Returns:
            サマリー文
        """
        summary = f"""
【マクロ環境分析】
- VIX: {vix:.1f} （{"低" if vix < 15 else "高" if vix > 25 else "中"}ボラティリティ）
- 市場環境: {regime.value}
- 為替: {fx_trend}

【投資戦略】
"""
        
        if regime == MarketRegime.RISK_ON:
            summary += "- 低リスク環境。成長株への投資が有効\n"
            summary += "- ハイリスク・ハイリターンの銘柄も検討可"
        elif regime == MarketRegime.RISK_OFF:
            summary += "- 高リスク環境。ディフェンシブ銘柄を重視\n"
            summary += "- 現金比率を高めに保つことを推奨"
        else:
            summary += "- 通常環境。バランスの良い配分を維持"
        
        return summary


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    analyzer = MacroAnalyzer()
    
    print("=== Macro Analyzer Test ===\n")
    
    # 包括分析
    analysis = analyzer.get_comprehensive_analysis()
    
    print(f"VIX: {analysis['indicators']['vix']:.1f}")
    print(f"USD/JPY: {analysis['indicators']['usd_jpy']:.2f}")
    print(f"日経225: {analysis['indicators']['nikkei_225']:.2f}\n")
    
    print(f"市場環境: {analysis['regime']}")
    print(f"為替トレンド: {analysis['fx_trend']}\n")
    
    print(f"推奨戦略: {analysis['recommended_strategy']}")
    print(f"推奨セクター: {', '.join(analysis['recommended_sectors'])}\n")
    
    print(analysis['summary'])
