"""
統一設定管理モジュール

すべての設定を一元管理し、環境変数とconfig.jsonを統合して扱う。
APIキーなどの機密情報は環境変数から取得する。
"""

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# .envファイルを読み込み
load_dotenv()


class Config:
    """統一設定クラス"""
    
    _instance: Optional["Config"] = None
    _config: Dict[str, Any] = {}
    
    # 環境変数から取得するAPIキーのマッピング
    API_KEY_ENV_VARS = {
        "gemini_api_key": ["AGSTOCK_GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "openai_api_key": ["AGSTOCK_OPENAI_API_KEY", "OPENAI_API_KEY"],
        "rakuten_api_key": ["RAKUTEN_API_KEY"],
        "line_token": ["LINE_NOTIFY_TOKEN", "LINE_TOKEN"],
        "discord_webhook": ["DISCORD_WEBHOOK_URL"],
    }
    
    def __new__(cls, config_path: str = "config.json"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(config_path)
        return cls._instance
    
    def _initialize(self, config_path: str) -> None:
        """設定を初期化"""
        self._config_path = Path(config_path)
        self._load_config()
        self._inject_api_keys()
        logger.info("Config initialized successfully")
    
    def _load_config(self) -> None:
        """config.jsonを読み込み"""
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse config.json: {e}")
                self._config = {}
        else:
            logger.warning(f"Config file not found: {self._config_path}")
            self._config = {}
    
    def _inject_api_keys(self) -> None:
        """環境変数からAPIキーを注入"""
        for key, env_vars in self.API_KEY_ENV_VARS.items():
            value = None
            for env_var in env_vars:
                value = os.getenv(env_var)
                if value:
                    break
            
            if value:
                # ネストされたキーに対応
                if key == "gemini_api_key":
                    if "gemini" not in self._config:
                        self._config["gemini"] = {}
                    self._config["gemini"]["api_key"] = value
                    if "ai_committee" in self._config:
                        self._config["ai_committee"]["api_key"] = value
                elif key == "openai_api_key":
                    self._config["openai_api_key"] = value
                elif key == "line_token":
                    if "notifications" in self._config and "line" in self._config["notifications"]:
                        self._config["notifications"]["line"]["token"] = value
                elif key == "discord_webhook":
                    if "notifications" in self._config and "discord" in self._config["notifications"]:
                        self._config["notifications"]["discord"]["webhook_url"] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得（ドット記法対応）
        
        例: config.get("risk.max_position_size", 0.1)
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def __getitem__(self, key: str) -> Any:
        """辞書アクセス"""
        return self._config.get(key)
    
    def __contains__(self, key: str) -> bool:
        """in演算子対応"""
        return key in self._config
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書として取得"""
        return self._config.copy()
    
    def get_api_key(self, service: str) -> Optional[str]:
        """APIキーを安全に取得"""
        if service == "gemini":
            return self.get("gemini.api_key") or self.get("ai_committee.api_key")
        elif service == "openai":
            return self.get("openai_api_key")
        return None
    
    def reload(self) -> None:
        """設定を再読み込み"""
        self._load_config()
        self._inject_api_keys()
        logger.info("Config reloaded")
    
    @classmethod
    def reset(cls) -> None:
        """シングルトンをリセット（テスト用）"""
        cls._instance = None
        cls._config = {}


@lru_cache(maxsize=1)
def get_config(config_path: str = "config.json") -> Config:
    """設定インスタンスを取得"""
    return Config(config_path)


# 後方互換性のためのエイリアス
def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """後方互換性のための関数"""
    return get_config(config_path).to_dict()
