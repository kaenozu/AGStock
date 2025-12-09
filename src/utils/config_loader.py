import yaml
import json
import os

def load_config_from_yaml(config_path: str = "config.yaml") -> dict:
    """
    指定されたYAMLファイルから設定を読み込みます。
    ファイルが見つからない場合は、デフォルト設定を返します。
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # デフォルト設定 (config.yamlとconfig.jsonの両方に対応できるようにしておく)
        # config.jsonもチェックする
        if config_path.endswith(".yaml"):
            json_config_path = config_path.replace(".yaml", ".json")
            if os.path.exists(json_config_path):
                try:
                    with open(json_config_path, "r", encoding="utf-8") as f_json:
                        return json.load(f_json)
                except Exception:
                    pass

        return {
            "paper_trading": {"initial_capital": 1000000},
            "auto_trading": {
                "max_daily_trades": 5,
                "daily_loss_limit_pct": -5.0,
                "max_vix": 40.0
            },
            "notifications": {"line": {"enabled": False}},
            "paths": {
                "log_dir": "logs",
                "auto_trader_log_file": "auto_trader.log"
            },
            "market_indices": {
                "vix": "^VIX",
                "japan_benchmark": "^N225"
            },
            "risk_management": {
                "min_cash_balance": 10000
            }
        }