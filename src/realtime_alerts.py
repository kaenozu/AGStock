"""
リアルタイムアラートシステム

価格変動、シグナル発生、ポートフォリオ変動などを監視し、
設定した条件でリアルタイム通知を送信します。
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """アラートタイプ"""
    PRICE_CHANGE = "price_change"        # 価格変動
    STRONG_SIGNAL = "strong_signal"      # 強いシグナル
    PORTFOLIO_CHANGE = "portfolio_change"  # ポートフォリオ変動
    RISK_WARNING = "risk_warning"        # リスク警告
    PROFIT_TARGET = "profit_target"      # 利益目標達成
    STOP_LOSS = "stop_loss"              # 損切りライン到達


class AlertPriority(Enum):
    """アラート優先度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AlertCondition:
    """アラート条件"""
    name: str
    alert_type: AlertType
    priority: AlertPriority
    condition_func: Callable[[Dict[str, Any]], bool]
    message_template: str
    enabled: bool = True
    cooldown_minutes: int = 60  # 同じアラートの再通知までの待機時間


@dataclass
class Alert:
    """アラート"""
    condition_name: str
    alert_type: AlertType
    priority: AlertPriority
    message: str
    timestamp: datetime
    data: Dict[str, Any]


class AlertManager:
    """アラート管理クラス"""
    
    def __init__(self, config_file: str = "config/alerts.json"):
        """
        Args:
            config_file: アラート設定ファイルのパス
        """
        self.config_file = config_file
        self.conditions: List[AlertCondition] = []
        self.alert_history: List[Alert] = []
        self.last_alert_time: Dict[str, datetime] = {}
        self.notification_services = []
        
        # デフォルト条件を登録
        self._register_default_conditions()
        
        # 設定ファイルから読み込み
        self.load_config()
    
    def _register_default_conditions(self):
        """デフォルトのアラート条件を登録"""
        
        # 1. 価格急騰・急落
        self.add_condition(AlertCondition(
            name="price_surge",
            alert_type=AlertType.PRICE_CHANGE,
            priority=AlertPriority.HIGH,
            condition_func=lambda data: data.get('price_change_pct', 0) > 5.0,
            message_template="🚀 {ticker} が {price_change_pct:.1f}% 急騰しました！現在価格: ¥{current_price:,.0f}"
        ))
        
        self.add_condition(AlertCondition(
            name="price_drop",
            alert_type=AlertType.PRICE_CHANGE,
            priority=AlertPriority.HIGH,
            condition_func=lambda data: data.get('price_change_pct', 0) < -5.0,
            message_template="⚠️ {ticker} が {price_change_pct:.1f}% 急落しました。現在価格: ¥{current_price:,.0f}"
        ))
        
        # 2. 強い買いシグナル
        self.add_condition(AlertCondition(
            name="strong_buy_signal",
            alert_type=AlertType.STRONG_SIGNAL,
            priority=AlertPriority.CRITICAL,
            condition_func=lambda data: (
                data.get('signal') == 'BUY' and
                data.get('confidence', 0) > 0.8 and
                data.get('expected_return', 0) > 10.0
            ),
            message_template="💰 強い買いシグナル！{ticker} ({name})\n期待リターン: {expected_return:.1f}%\n信頼度: {confidence:.0f}%"
        ))
        
        # 3. ポートフォリオ大幅変動
        self.add_condition(AlertCondition(
            name="portfolio_large_gain",
            alert_type=AlertType.PORTFOLIO_CHANGE,
            priority=AlertPriority.MEDIUM,
            condition_func=lambda data: data.get('portfolio_change_pct', 0) > 5.0,
            message_template="📈 ポートフォリオが {portfolio_change_pct:.1f}% 上昇！\n総資産: ¥{total_equity:,.0f}"
        ))
        
        self.add_condition(AlertCondition(
            name="portfolio_large_loss",
            alert_type=AlertType.PORTFOLIO_CHANGE,
            priority=AlertPriority.HIGH,
            condition_func=lambda data: data.get('portfolio_change_pct', 0) < -3.0,
            message_template="📉 ポートフォリオが {portfolio_change_pct:.1f}% 下落。\n総資産: ¥{total_equity:,.0f}\n対策を検討してください。"
        ))
        
        # 4. リスク警告
        self.add_condition(AlertCondition(
            name="max_drawdown_warning",
            alert_type=AlertType.RISK_WARNING,
            priority=AlertPriority.CRITICAL,
            condition_func=lambda data: data.get('max_drawdown', 0) < -10.0,
            message_template="🚨 リスク警告！最大ドローダウン: {max_drawdown:.1f}%\n即座にリスク管理を実施してください。"
        ))
        
        # 5. 利益目標達成
        self.add_condition(AlertCondition(
            name="profit_target_reached",
            alert_type=AlertType.PROFIT_TARGET,
            priority=AlertPriority.MEDIUM,
            condition_func=lambda data: (
                data.get('position_pnl_pct', 0) > 10.0 and
                data.get('has_position', False)
            ),
            message_template="🎯 {ticker} が利益目標達成！\n含み益: {position_pnl_pct:.1f}% (¥{position_pnl:,.0f})\n利確を検討してください。"
        ))
        
        # 6. 損切りライン接近
        self.add_condition(AlertCondition(
            name="stop_loss_approaching",
            alert_type=AlertType.STOP_LOSS,
            priority=AlertPriority.HIGH,
            condition_func=lambda data: (
                data.get('position_pnl_pct', 0) < -4.0 and
                data.get('has_position', False)
            ),
            message_template="⛔ {ticker} が損切りライン接近\n含み損: {position_pnl_pct:.1f}% (¥{position_pnl:,.0f})\n損切りを検討してください。"
        ))
    
    def add_condition(self, condition: AlertCondition):
        """アラート条件を追加"""
        self.conditions.append(condition)
        logger.info(f"Alert condition added: {condition.name}")
    
    def check_conditions(self, data: Dict[str, Any]) -> List[Alert]:
        """
        条件チェックとアラート生成
        
        Args:
            data: チェック対象のデータ
            
        Returns:
            発火したアラートのリスト
        """
        triggered_alerts = []
        current_time = datetime.now()
        
        for condition in self.conditions:
            if not condition.enabled:
                continue
            
            # クールダウンチェック
            last_time = self.last_alert_time.get(condition.name)
            if last_time:
                elapsed = (current_time - last_time).total_seconds() / 60
                if elapsed < condition.cooldown_minutes:
                    continue
            
            # 条件チェック
            try:
                if condition.condition_func(data):
                    # アラート生成
                    message = condition.message_template.format(**data)
                    alert = Alert(
                        condition_name=condition.name,
                        alert_type=condition.alert_type,
                        priority=condition.priority,
                        message=message,
                        timestamp=current_time,
                        data=data
                    )
                    
                    triggered_alerts.append(alert)
                    self.alert_history.append(alert)
                    self.last_alert_time[condition.name] = current_time
                    
                    logger.info(f"Alert triggered: {condition.name}")
                    
            except Exception as e:
                logger.error(f"Error checking condition {condition.name}: {e}")
        
        return triggered_alerts
    
    def send_alerts(self, alerts: List[Alert]):
        """アラートを送信"""
        for alert in alerts:
            for service in self.notification_services:
                try:
                    service.send(alert)
                except Exception as e:
                    logger.error(f"Failed to send alert via {service.__class__.__name__}: {e}")
    
    def add_notification_service(self, service):
        """通知サービスを追加"""
        self.notification_services.append(service)
        logger.info(f"Notification service added: {service.__class__.__name__}")
    
    def load_config(self):
        """設定ファイルから読み込み"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 条件の有効/無効を更新
            for cond_name, enabled in config.get('enabled_conditions', {}).items():
                for condition in self.conditions:
                    if condition.name == cond_name:
                        condition.enabled = enabled
                        
            logger.info(f"Alert config loaded from {self.config_file}")
            
        except FileNotFoundError:
            logger.warning(f"Alert config file not found: {self.config_file}")
            self.save_config()
        except Exception as e:
            logger.error(f"Error loading alert config: {e}")
    
    def save_config(self):
        """設定ファイルに保存"""
        try:
            config = {
                'enabled_conditions': {
                    cond.name: cond.enabled for cond in self.conditions
                }
            }
            
            import os
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Alert config saved to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error saving alert config: {e}")
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """過去のアラート履歴を取得"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp > cutoff]


# グローバルインスタンス
_alert_manager = None

def get_alert_manager() -> AlertManager:
    """AlertManagerのシングルトンインスタンスを取得"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


if __name__ == "__main__":
    # テスト
    logging.basicConfig(level=logging.INFO)
    
    manager = AlertManager()
    
    # テストデータ
    test_data = {
        'ticker': '7203.T',
        'name': 'トヨタ自動車',
        'price_change_pct': 6.5,
        'current_price': 2500,
        'signal': 'BUY',
        'confidence': 0.85,
        'expected_return': 12.5
    }
    
    # 条件チェック
    alerts = manager.check_conditions(test_data)
    
    print(f"\n発火したアラート数: {len(alerts)}")
    for alert in alerts:
        print(f"\n{alert.priority.value.upper()}: {alert.message}")
