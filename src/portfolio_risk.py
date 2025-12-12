"""
繝昴・繝医ヵ繧ｩ繝ｪ繧ｪ繝ｪ繧ｹ繧ｯ蛻・梵繝｢繧ｸ繝･繝ｼ繝ｫ
Portfolio Risk Analysis Module

髮・ｸｭ蠎ｦ縲√そ繧ｯ繧ｿ繝ｼ蛻・淵縲√Μ繧ｹ繧ｯ隴ｦ蜻翫ｒ險育ｮ・
"""
import pandas as pd
from typing import Dict, List, Tuple
import yfinance as yf
from functools import lru_cache

class PortfolioRiskAnalyzer:
    """繝昴・繝医ヵ繧ｩ繝ｪ繧ｪ縺ｮ繝ｪ繧ｹ繧ｯ謖・ｨ吶ｒ險育ｮ・""
    
    def __init__(self):
        self.concentration_threshold = 0.30  # 30%
        self.sector_threshold = 0.50  # 50%
    
    def calculate_concentration(self, positions: pd.DataFrame) -> Dict:
        """
        繝昴・繝医ヵ繧ｩ繝ｪ繧ｪ縺ｮ髮・ｸｭ蠎ｦ繧定ｨ育ｮ・
        
        Args:
            positions: PaperTrader.get_positions()縺ｮ謌ｻ繧雁､
            
        Returns:
            dict: {
                'herfindahl_index': float,  # 0-1, 1縺ｫ霑代＞縺ｻ縺ｩ髮・ｸｭ
                'top_position_pct': float,  # 譛螟ｧ繝昴ず繧ｷ繝ｧ繝ｳ縺ｮ蜑ｲ蜷・
                'top_ticker': str,          # 譛螟ｧ繝昴ず繧ｷ繝ｧ繝ｳ縺ｮ驫俶氛
                'is_concentrated': bool     # 髢ｾ蛟､雜・℃繝輔Λ繧ｰ
            }
        """
        if positions.empty:
            return {
                'herfindahl_index': 0.0,
                'top_position_pct': 0.0,
                'top_ticker': None,
                'is_concentrated': False
            }
        
        # 譎ゆｾ｡隧穂ｾ｡鬘阪〒險育ｮ・
        if 'market_value' not in positions.columns:
            positions['market_value'] = positions['current_price'] * positions['quantity']
        
        total_value = positions['market_value'].sum()
        
        if total_value == 0:
            return {
                'herfindahl_index': 0.0,
                'top_position_pct': 0.0,
                'top_ticker': None,
                'is_concentrated': False
            }
        
        # 蜷・・繧ｸ繧ｷ繝ｧ繝ｳ縺ｮ蜑ｲ蜷・
        positions['weight'] = positions['market_value'] / total_value
        
        # Herfindahl Index (HHI) = ﾎ｣(weight^2)
        hhi = (positions['weight'] ** 2).sum()
        
        # 譛螟ｧ繝昴ず繧ｷ繝ｧ繝ｳ
        top_idx = positions['market_value'].idxmax()
        top_position = positions.loc[top_idx]
        top_pct = top_position['weight']
        
        return {
            'herfindahl_index': hhi,
            'top_position_pct': top_pct,
            'top_ticker': top_position['ticker'],
            'is_concentrated': top_pct > self.concentration_threshold
        }
    
    @lru_cache(maxsize=128)
    def _get_sector(self, ticker: str) -> str:
        """
        驫俶氛縺ｮ繧ｻ繧ｯ繧ｿ繝ｼ繧貞叙蠕暦ｼ医く繝｣繝・す繝･莉倥″・・
        
        Args:
            ticker: 驫俶氛繧ｳ繝ｼ繝・
            
        Returns:
            str: 繧ｻ繧ｯ繧ｿ繝ｼ蜷搾ｼ亥叙蠕怜､ｱ謨玲凾縺ｯ'Unknown'・・
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info.get('sector', 'Unknown')
        except Exception:
            return 'Unknown'
    
    def check_sector_diversification(self, positions: pd.DataFrame) -> Dict:
        """
        繧ｻ繧ｯ繧ｿ繝ｼ蛻・淵繧貞・譫・
        
        Args:
            positions: PaperTrader.get_positions()縺ｮ謌ｻ繧雁､
            
        Returns:
            dict: {
                'sector_distribution': dict,  # {sector: percentage}
                'top_sector': str,
                'top_sector_pct': float,
                'is_sector_concentrated': bool,
                'num_sectors': int
            }
        """
        if positions.empty:
            return {
                'sector_distribution': {},
                'top_sector': None,
                'top_sector_pct': 0.0,
                'is_sector_concentrated': False,
                'num_sectors': 0
            }
        
        # 譎ゆｾ｡隧穂ｾ｡鬘阪〒險育ｮ・
        if 'market_value' not in positions.columns:
            positions['market_value'] = positions['current_price'] * positions['quantity']
        
        total_value = positions['market_value'].sum()
        
        if total_value == 0:
            return {
                'sector_distribution': {},
                'top_sector': None,
                'top_sector_pct': 0.0,
                'is_sector_concentrated': False,
                'num_sectors': 0
            }
        
        # 繧ｻ繧ｯ繧ｿ繝ｼ諠・ｱ繧貞叙蠕・
        positions['sector'] = positions['ticker'].apply(self._get_sector)
        
        # 繧ｻ繧ｯ繧ｿ繝ｼ蛻･髮・ｨ・
        sector_values = positions.groupby('sector')['market_value'].sum()
        sector_distribution = (sector_values / total_value).to_dict()
        
        # 譛螟ｧ繧ｻ繧ｯ繧ｿ繝ｼ
        top_sector = sector_values.idxmax()
        top_sector_pct = sector_values.max() / total_value
        
        return {
            'sector_distribution': sector_distribution,
            'top_sector': top_sector,
            'top_sector_pct': top_sector_pct,
            'is_sector_concentrated': top_sector_pct > self.sector_threshold,
            'num_sectors': len(sector_distribution)
        }
    
    def get_risk_alerts(self, positions: pd.DataFrame) -> List[Dict]:
        """
        繝ｪ繧ｹ繧ｯ隴ｦ蜻翫ｒ逕滓・
        
        Args:
            positions: PaperTrader.get_positions()縺ｮ謌ｻ繧雁､
            
        Returns:
            list: [{'level': 'warning'|'info', 'message': str}, ...]
        """
        alerts = []
        
        if positions.empty:
            return alerts
        
        # 髮・ｸｭ蠎ｦ繝√ぉ繝・け
        concentration = self.calculate_concentration(positions)
        if concentration['is_concentrated']:
            alerts.append({
                'level': 'warning',
                'message': f"笞・・{concentration['top_ticker']} 縺・{concentration['top_position_pct']:.1%} 繧貞頃繧√※縺・∪縺呻ｼ域耳螂ｨ: 30%莉･荳具ｼ・
            })
        
        # 繧ｻ繧ｯ繧ｿ繝ｼ蛻・淵繝√ぉ繝・け
        sector_div = self.check_sector_diversification(positions)
        if sector_div['is_sector_concentrated']:
            alerts.append({
                'level': 'warning',
                'message': f"笞・・{sector_div['top_sector']} 繧ｻ繧ｯ繧ｿ繝ｼ縺・{sector_div['top_sector_pct']:.1%} 繧貞頃繧√※縺・∪縺呻ｼ域耳螂ｨ: 50%莉･荳具ｼ・
            })
        
        # 繝昴ず繧ｷ繝ｧ繝ｳ謨ｰ繝√ぉ繝・け
        num_positions = len(positions)
        if num_positions == 1:
            alerts.append({
                'level': 'warning',
                'message': "笞・・繝昴ず繧ｷ繝ｧ繝ｳ縺・驫俶氛縺ｮ縺ｿ縺ｧ縺吶ょ・謨｣謚戊ｳ・ｒ謗ｨ螂ｨ縺励∪縺・
            })
        elif num_positions >= 2 and num_positions <= 3:
            alerts.append({
                'level': 'info',
                'message': f"邃ｹ・・繝昴ず繧ｷ繝ｧ繝ｳ謨ｰ: {num_positions}驫俶氛・域耳螂ｨ: 5-10驫俶氛・・
            })
        
        return alerts
    
    def calculate_concentration_score(self, positions: pd.DataFrame) -> float:
        """
        髮・ｸｭ蠎ｦ繧ｹ繧ｳ繧｢繧定ｨ育ｮ暦ｼ・-100縲・ｫ倥＞縺ｻ縺ｩ蛻・淵縺輔ｌ縺ｦ縺・ｋ・・
        
        Args:
            positions: PaperTrader.get_positions()縺ｮ謌ｻ繧雁､
            
        Returns:
            float: 0-100縺ｮ繧ｹ繧ｳ繧｢
        """
        if positions.empty or len(positions) == 0:
            return 0.0
        
        concentration = self.calculate_concentration(positions)
        hhi = concentration['herfindahl_index']
        
        # HHI繧・-100繧ｹ繧ｳ繧｢縺ｫ螟画鋤
        # HHI = 1.0 (螳悟・髮・ｸｭ) -> Score = 0
        # HHI = 1/N (螳悟・蛻・淵) -> Score = 100
        
        n = len(positions)
        min_hhi = 1.0 / n  # 螳悟・蛻・淵譎ゅ・HHI
        max_hhi = 1.0      # 螳悟・髮・ｸｭ譎ゅ・HHI
        
        # 豁｣隕丞喧・磯・ｻ｢: HHI縺御ｽ弱＞縺ｻ縺ｩ繧ｹ繧ｳ繧｢縺碁ｫ倥＞・・
        if max_hhi - min_hhi == 0:
            return 100.0
        
        score = ((max_hhi - hhi) / (max_hhi - min_hhi)) * 100
        return max(0.0, min(100.0, score))
