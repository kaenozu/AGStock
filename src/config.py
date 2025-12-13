import os
from pathlib import Path
from typing import Any, Dict

import yaml


class Config:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from config.yaml and environment variables."""
        config_path = Path("config.yaml")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        else:
            # Fallback defaults if file missing
            self._config = {
                "system": {"initial_capital": 10000000},
                "risk_management": {"max_position_size": 0.2},
                "notifications": {"slack": {}, "email": {}, "discord": {}},
                "paths": {"db_path": "paper_trade.db"},
            }

        # Override with Environment Variables
        self._override_from_env()

    def _override_from_env(self):
        """Override specific settings with environment variables."""
        # Slack
        if os.getenv("SLACK_WEBHOOK_URL"):
            self._config.setdefault("notifications", {}).setdefault("slack", {})["webhook_url"] = os.getenv(
                "SLACK_WEBHOOK_URL"
            )

        # Discord
        if os.getenv("DISCORD_WEBHOOK_URL"):
            self._config.setdefault("notifications", {}).setdefault("discord", {})["webhook_url"] = os.getenv(
                "DISCORD_WEBHOOK_URL"
            )

        # Pushover
        if os.getenv("PUSHOVER_USER_KEY"):
            self._config.setdefault("notifications", {}).setdefault("pushover", {})["user_key"] = os.getenv(
                "PUSHOVER_USER_KEY"
            )
        if os.getenv("PUSHOVER_API_TOKEN"):
            self._config.setdefault("notifications", {}).setdefault("pushover", {})["api_token"] = os.getenv(
                "PUSHOVER_API_TOKEN"
            )

        # Email
        if os.getenv("EMAIL_ENABLED"):
            self._config.setdefault("notifications", {}).setdefault("email", {})["enabled"] = (
                os.getenv("EMAIL_ENABLED").lower() == "true"
            )
        if os.getenv("EMAIL_FROM"):
            self._config.setdefault("notifications", {}).setdefault("email", {})["from_address"] = os.getenv(
                "EMAIL_FROM"
            )
        if os.getenv("EMAIL_PASSWORD"):
            self._config.setdefault("notifications", {}).setdefault("email", {})["password"] = os.getenv(
                "EMAIL_PASSWORD"
            )  # Not in yaml for security
        if os.getenv("EMAIL_TO"):
            self._config.setdefault("notifications", {}).setdefault("email", {})["to_address"] = os.getenv("EMAIL_TO")

    def get(self, path: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'system.initial_capital')."""
        keys = path.split(".")
        value = self._config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default


# Global instance
config = Config()
