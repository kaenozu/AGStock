"""
Anomaly Detector Module
Detects abnormal portfolio behavior and system errors.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
from src.paper_trader import PaperTrader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self, 
                 daily_loss_threshold: float = -0.05,
                 volatility_spike_threshold: float = 2.0):
        """
        Args:
            daily_loss_threshold: Alert if daily loss exceeds this (e.g., -0.05 = -5%)
            volatility_spike_threshold: Alert if volatility spikes by this factor
        """
        self.daily_loss_threshold = daily_loss_threshold
        self.volatility_spike_threshold = volatility_spike_threshold
        self.pt = PaperTrader()
    
    def check_daily_loss(self) -> Optional[Dict]:
        """
        Check if today's loss exceeds threshold.
        
        Returns:
            Alert dict if anomaly detected, None otherwise
        """
        try:
            balance = self.pt.get_current_balance()
            current_equity = balance['total_equity']
            
            # Get yesterday's equity
            # This requires equity history, which we should track
            # For now, use a simplified approach
            
            # TODO: Implement proper equity history tracking
            # For demonstration, we'll check against initial capital
            initial_capital = self.pt.initial_capital
            total_return = (current_equity - initial_capital) / initial_capital
            
            # Check if we lost more than threshold today
            # This is simplified - in production, track daily equity changes
            if total_return < self.daily_loss_threshold:
                return {
                    'type': 'DAILY_LOSS',
                    'severity': 'CRITICAL',
                    'message': f'Total portfolio loss: {total_return:.1%}',
                    'current_equity': current_equity,
                    'initial_capital': initial_capital
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking daily loss: {e}")
            return None
    
    def check_volatility_spike(self) -> Optional[Dict]:
        """
        Check for abnormal volatility spikes.
        
        Returns:
            Alert dict if anomaly detected, None otherwise
        """
        try:
            positions = self.pt.get_positions()
            
            if positions.empty:
                return None
            
            # Check for positions with extreme unrealized P&L
            extreme_positions = []
            for _, pos in positions.iterrows():
                pnl_pct = (pos['current_price'] - pos['entry_price']) / pos['entry_price']
                
                # Alert if any position moved >10% in a day (simplified)
                if abs(pnl_pct) > 0.10:
                    extreme_positions.append({
                        'ticker': pos['ticker'],
                        'pnl_pct': pnl_pct
                    })
            
            if extreme_positions:
                return {
                    'type': 'VOLATILITY_SPIKE',
                    'severity': 'WARNING',
                    'message': f'{len(extreme_positions)} positions with extreme moves',
                    'positions': extreme_positions
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking volatility: {e}")
            return None
    
    def check_system_health(self) -> Optional[Dict]:
        """
        Check for system errors (API failures, DB issues, etc.)
        
        Returns:
            Alert dict if anomaly detected, None otherwise
        """
        try:
            # Try to access database
            _ = self.pt.get_current_balance()
            _ = self.pt.get_positions()
            
            # If we got here, basic system is working
            return None
            
        except Exception as e:
            return {
                'type': 'SYSTEM_ERROR',
                'severity': 'CRITICAL',
                'message': f'System health check failed: {str(e)}'
            }
    
    def run_all_checks(self) -> List[Dict]:
        """
        Run all anomaly checks.
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Check daily loss
        loss_alert = self.check_daily_loss()
        if loss_alert:
            anomalies.append(loss_alert)
        
        # Check volatility
        vol_alert = self.check_volatility_spike()
        if vol_alert:
            anomalies.append(vol_alert)
        
        # Check system health
        health_alert = self.check_system_health()
        if health_alert:
            anomalies.append(health_alert)
        
        if anomalies:
            logger.warning(f"Detected {len(anomalies)} anomalies")
        
        return anomalies
    
    def send_alert(self, anomaly: Dict):
        """
        Send alert notification.
        
        Args:
            anomaly: Anomaly dict to send
        """
        # TODO: Integrate with SmartNotifier for LINE/Discord
        logger.critical(f"ALERT [{anomaly['severity']}]: {anomaly['message']}")
        
        # For now, just log
        # In production, call SmartNotifier
        try:
            from src.smart_notifier import SmartNotifier
            notifier = SmartNotifier()
            
            alert_message = f"🚨 **{anomaly['type']}**\n{anomaly['message']}"
            notifier.send_notification(alert_message)
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

if __name__ == "__main__":
    # Test
    detector = AnomalyDetector()
    anomalies = detector.run_all_checks()
    print(f"Detected {len(anomalies)} anomalies")
    for anomaly in anomalies:
        print(f"  - {anomaly['type']}: {anomaly['message']}")
