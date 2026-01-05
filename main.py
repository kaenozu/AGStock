#!/usr/bin/env python3
"""
AGStock v3.0 - Main Entry Point
===============================
All-in-one investment trading system with AI-powered features.

Features:
- Multi-Agent AI Trading System
- Global Market Integration
- DeFi & Blockchain Support
- Hyper-Personalization
- Quantum-Security Defense

Usage:
    python main.py              # Run with default settings
    python main.py --demo       # Run in demo mode
    python main.py --dashboard  # Launch unified dashboard
    python main.py --test       # Run system tests
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from typing import Dict, Any
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/agstock.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Version info
VERSION = "3.0.0"
BUILD_DATE = "2024-01-04"
AUTHOR = "AGStock Development Team"


class AGStockConfig:
    """システム設定管理"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        default_config = {
            "version": VERSION,
            "mode": "production",  # production, demo, test
            "market": {
                "default_market": "TSE",
                "supported_markets": ["TSE", "NYSE", "LSE", "HKEX"],
                "trading_hours": {
                    "TSE": {"start": "09:00", "end": "15:00"},
                    "NYSE": {"start": "09:30", "end": "16:00"},
                },
            },
            "ai": {
                "model": "ensemble",  # ensemble, single, multi_agent
                "prediction_horizon": 5,
                "confidence_threshold": 0.7,
            },
            "risk": {
                "max_position_size": 0.2,
                "stop_loss": 0.05,
                "take_profit": 0.10,
                "max_daily_loss": 0.10,
            },
            "notifications": {
                "enabled": True,
                "channels": ["line", "discord", "email"],
                "alert_threshold": "high",
            },
            "security": {
                "encryption": "quantum",
                "mfa_required": False,
                "audit_logging": True,
            },
            "performance": {
                "cache_enabled": True,
                "cache_ttl": 300,
                "max_concurrent_requests": 10,
            },
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                # マージ（デフォルト設定を優先）
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Config load failed, using defaults: {e}")
        else:
            logger.info("Using default configuration")

        return default_config

    def save(self):
        """設定保存"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        logger.info(f"Configuration saved to {self.config_path}")

    def get(self, key: str, default: Any = None) -> Any:
        """設定値取得（ドット記法対応）"""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


class SystemManager:
    """システム管理クラス"""

    def __init__(self, config: AGStockConfig):
        self.config = config
        self.start_time = datetime.now()
        self.components = {}

    def initialize_components(self):
        """コンポーネント初期化"""
        logger.info("Initializing AGStock v3.0 components...")

        try:
            # AI Components
            from src.multi_agent_trading import MultiAgentConsensusSystem

            self.components["ai_agents"] = MultiAgentConsensusSystem()
            logger.info("  [OK] Multi-Agent AI System")
        except ImportError as e:
            logger.warning(f"  [SKIP] AI Agents: {e}")
            self.components["ai_agents"] = None

        try:
            # Market Data
            from simple_global_market import SimpleGlobalMonitor

            self.components["market"] = SimpleGlobalMonitor()
            logger.info("  [OK] Global Market Monitor")
        except ImportError as e:
            logger.warning(f"  [SKIP] Market Monitor: {e}")
            self.components["market"] = None

        try:
            # DeFi Manager
            from demo_defi_system import DeFiProtocolManager

            self.components["defi"] = DeFiProtocolManager()
            logger.info("  [OK] DeFi Portfolio Manager")
        except ImportError as e:
            logger.warning(f"  [SKIP] DeFi Manager: {e}")
            self.components["defi"] = None

        try:
            # Personalization
            from hyper_personalization_system import HyperPersonalizationEngine

            self.components["personalization"] = HyperPersonalizationEngine()
            logger.info("  [OK] Hyper-Personalization Engine")
        except ImportError as e:
            logger.warning(f"  [SKIP] Personalization: {e}")
            self.components["personalization"] = None

        try:
            # Security
            from quantum_security_defense import QuantumSecurityManager

            self.components["security"] = QuantumSecurityManager()
            logger.info("  [OK] Quantum Security Defense")
        except ImportError as e:
            logger.warning(f"  [SKIP] Security: {e}")
            self.components["security"] = None

    def get_system_status(self) -> Dict[str, Any]:
        """システムステータス取得"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "version": VERSION,
            "uptime_seconds": uptime,
            "components_active": len([c for c in self.components.values() if c]),
            "components_total": len(self.components),
            "config_mode": self.config.get("mode", "unknown"),
            "timestamp": datetime.now().isoformat(),
        }

    def run_diagnostic(self) -> Dict[str, Any]:
        """システム診断実行"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "overall_status": "healthy",
        }

        # 各コンポーネントのヘルスチェック
        for name, component in self.components.items():
            check = {
                "component": name,
                "status": "healthy" if component else "not_initialized",
                "latency_ms": 0,
            }
            results["checks"].append(check)

        # 全コンポーネントがhealthyか確認
        unhealthy = [c for c in results["checks"] if c["status"] != "healthy"]
        if len(unhealthy) > len(results["checks"]) / 2:
            results["overall_status"] = "degraded"
        elif unhealthy:
            results["overall_status"] = "warning"

        return results


def run_demo_mode():
    """デモモード実行"""
    print("\n" + "=" * 60)
    print("AGStock v3.0 Demo Mode")
    print("=" * 60)

    # Initialize configuration
    config = AGStockConfig()
    config.config["mode"] = "demo"

    # Initialize system
    system = SystemManager(config)
    system.initialize_components()

    # Demo market data
    print("\n[1] Global Market Overview")
    if system.components.get("market"):
        system.components["market"].display_overview()

    # Demo AI prediction
    print("\n[2] AI Trading Signals")
    if system.components.get("ai_agents"):
        print("Multi-Agent System: Active")
        print("Agents: Technical, Fundamental, Sentiment, Risk")

    # Demo DeFi
    print("\n[3] DeFi Portfolio")
    if system.components.get("defi"):
        positions = system.components["defi"].get_portfolio_positions()
        for pos in positions:
            print(f"  {pos.protocol}: ${pos.value_usd:,.2f} (APY: {pos.apy:.1%})")

    # Demo Personalization
    print("\n[4] User Personalization")
    if system.components.get("personalization"):
        print("Genetic Algorithm: Active")
        print("Behavioral Analysis: Active")

    # Demo Security
    print("\n[5] Security Status")
    if system.components.get("security"):
        status = system.components["security"].get_security_status()
        print(f"  Encryption: {status['encryption']['algorithm']}")
        print("  Anomaly Detection: Active")

    # System status
    print("\n[6] System Status")
    status = system.get_system_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


def run_dashboard():
    """ダッシュボード起動"""
    print("\nLaunching AGStock Unified Dashboard...")
    print("Please open: http://localhost:8501")

    try:
        import subprocess

        subprocess.run([sys.executable, "simple_unified_dashboard.py"], check=True)
    except Exception as e:
        print(f"Dashboard launch failed: {e}")
        print("Try running: streamlit run simple_unified_dashboard.py")


def run_tests():
    """テスト実行"""
    print("\nRunning AGStock v3.0 System Tests...")

    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "passed": 0,
        "failed": 0,
    }

    # Basic import tests
    test_cases = [
        ("Config Module", "from main import AGStockConfig"),
        ("System Manager", "from main import SystemManager"),
        ("Global Market", "import simple_global_market"),
        ("DeFi System", "import demo_defi_system"),
        ("Personalization", "import hyper_personalization_system"),
        ("Security System", "import quantum_security_defense"),
    ]

    for name, import_stmt in test_cases:
        try:
            exec(import_stmt)
            results["tests"].append({"test": name, "status": "PASS"})
            results["passed"] += 1
        except Exception as e:
            results["tests"].append(
                {"test": name, "status": "FAIL", "error": str(e)[:100]}
            )
            results["failed"] += 1

    # Print results
    print(f"\nTest Results: {results['passed']} passed, {results['failed']} failed")

    for test in results["tests"]:
        status_icon = "[PASS]" if test["status"] == "PASS" else "[FAIL]"
        print(f"  {status_icon} {test['test']}")
        if "error" in test:
            print(f"         Error: {test['error']}")

    return results["failed"] == 0


def show_help():
    """ヘルプ表示"""
    help_text = f"""
AGStock v{VERSION} - AI-Powered Investment Trading System
{"=" * 50}

Usage: python main.py [OPTIONS]

Options:
    --demo       Run in demo mode (no real trading)
    --dashboard  Launch web dashboard
    --test       Run system tests
    --status     Show system status
    --config     Show current configuration
    --help       Show this help message

Examples:
    python main.py              # Run with default settings
    python main.py --demo       # Run demo mode
    python main.py --dashboard  # Launch dashboard
    python main.py --test       # Run tests

Files:
    config.json   - System configuration
    logs/         - System logs
    data/         - Data files

Documentation:
    See docs/ directory for detailed documentation.

Version: {VERSION} ({BUILD_DATE})
Author: {AUTHOR}
"""
    print(help_text)


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    parser.add_argument("--dashboard", action="store_true", help="Launch dashboard")
    parser.add_argument("--test", action="store_true", help="Run tests")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--config", action="store_true", help="Show configuration")
    parser.add_argument("--help", action="store_true", help="Show help")

    args = parser.parse_args()

    # Handle arguments
    if args.help:
        show_help()
        return 0

    if args.config:
        config = AGStockConfig()
        print("\nCurrent Configuration (config.json):")
        print(json.dumps(config.config, indent=2, ensure_ascii=False))
        return 0

    if args.status:
        config = AGStockConfig()
        system = SystemManager(config)
        system.initialize_components()
        status = system.get_system_status()
        print("\nAGStock System Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        return 0

    if args.test:
        success = run_tests()
        return 0 if success else 1

    if args.dashboard:
        run_dashboard()
        return 0

    if args.demo:
        run_demo_mode()
        return 0

    # Default: Run demo mode
    run_demo_mode()
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nShutting down AGStock...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"System error: {e}", exc_info=True)
        sys.exit(1)
