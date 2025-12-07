"""
Config Manager - 環境変数とアプリケーション設定の管理
"""
import os
from dotenv import load_dotenv
from typing import Optional
import json

# .envファイルを読み込み
load_dotenv()


class Config:
    """アプリケーション設定"""
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    RAKUTEN_API_KEY: str = os.getenv('RAKUTEN_API_KEY', '')
    
    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///data/agstock.db')
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # Security
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET: str = os.getenv('JWT_SECRET', 'dev-jwt-secret-change-in-production')
    ENCRYPTION_KEY: bytes = os.getenv('ENCRYPTION_KEY', 'dev-encryption-key-32-bytes!!').encode()
    
    # App Settings
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    
    # Trading Settings
    PAPER_TRADING: bool = os.getenv('PAPER_TRADING', 'True').lower() == 'true'
    AUTO_TRADING_ENABLED: bool = os.getenv('AUTO_TRADING_ENABLED', 'False').lower() == 'true'
    
    # Notification Settings
    ENABLE_NOTIFICATIONS: bool = os.getenv('ENABLE_NOTIFICATIONS', 'True').lower() == 'true'
    NOTIFICATION_EMAIL: str = os.getenv('NOTIFICATION_EMAIL', '')
    
    # Performance
    CACHE_TTL: int = int(os.getenv('CACHE_TTL', '3600'))
    MAX_WORKERS: int = int(os.getenv('MAX_WORKERS', '4'))
    
    # Monitoring
    SENTRY_DSN: Optional[str] = os.getenv('SENTRY_DSN')
    PROMETHEUS_PORT: int = int(os.getenv('PROMETHEUS_PORT', '9090'))
    
    @classmethod
    def validate(cls) -> bool:
        """設定の検証"""
        errors = []
        
        if cls.ENVIRONMENT == 'production':
            if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
                errors.append("SECRET_KEY must be changed in production")
            
            if cls.JWT_SECRET == 'dev-jwt-secret-change-in-production':
                errors.append("JWT_SECRET must be changed in production")
            
            if not cls.OPENAI_API_KEY:
                errors.append("OPENAI_API_KEY is required in production")
        
        if errors:
            for error in errors:
                print(f"Configuration Error: {error}")
            return False
        
        return True
    
    @classmethod
    def to_dict(cls) -> dict:
        """設定を辞書として取得（機密情報を除く）"""
        return {
            'environment': cls.ENVIRONMENT,
            'debug': cls.DEBUG,
            'log_level': cls.LOG_LEVEL,
            'paper_trading': cls.PAPER_TRADING,
            'auto_trading_enabled': cls.AUTO_TRADING_ENABLED,
            'enable_notifications': cls.ENABLE_NOTIFICATIONS,
            'cache_ttl': cls.CACHE_TTL,
            'max_workers': cls.MAX_WORKERS
        }


# 設定の検証
if __name__ == "__main__":
    if Config.validate():
        print("✅ Configuration is valid")
        print(json.dumps(Config.to_dict(), indent=2))
    else:
        print("❌ Configuration validation failed")
