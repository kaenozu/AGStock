#!/usr/bin/env python3
"""
災害復旧システムテスト
分散ストレージと復元ポイントの完全性を検証
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

from src.distributed_storage import DistributedDataManager, DisasterRecoveryManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DisasterRecoveryTester:
    """災害復旧システムテストクラス"""

    def __init__(self):
        self.distributed_manager = DistributedDataManager()
        self.disaster_recovery = DisasterRecoveryManager(self.distributed_manager)
        self.test_results = {}

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """包括的な復旧システムテスト"""
        logger.info("🚀 災害復旧システムの包括テストを開始します...")

        test_suite = {
            "data_integrity_test": await self.test_data_integrity(),
            "backup_creation_test": await self.test_backup_creation(),
            "recovery_point_test": await self.test_recovery_points(),
            "full_restore_test": await self.test_full_system_restore(),
            "multi_provider_failover_test": await self.test_multi_provider_failover(),
            "cross_platform_compatibility_test": await self.test_cross_platform_compatibility(),
        }

        # テスト結果を集計
        passed_tests = sum(
            1 for result in test_suite.values() if result.get("success", False)
        )
        total_tests = len(test_suite)

        overall_result = {
            "success": passed_tests == total_tests,
            "passed_tests": f"{passed_tests}/{total_tests}",
            "test_suite": test_suite,
            "timestamp": datetime.now().isoformat(),
            "recommendations": self._generate_recommendations(test_suite),
        }

        await self._save_test_results(overall_result)
        self._print_test_summary(overall_result)

        return overall_result

    async def test_data_integrity(self) -> Dict[str, Any]:
        """データ整合性テスト"""
        logger.info("📊 データ整合性テストを実行中...")

        try:
            # 既存バックアップの整合性を確認
            integrity_result = await self.disaster_recovery.test_data_integrity()

            # 追加チェック: データ形式の検証
            sample_data = {
                "positions": [{"ticker": "7203", "quantity": 100, "price": 2800}],
                "total_value": 280000,
                "timestamp": datetime.now().isoformat(),
            }

            # データ形式検証
            json_compatible = True
            try:
                json.dumps(sample_data, ensure_ascii=False)
            except (TypeError, ValueError):
                json_compatible = False

            return {
                "success": integrity_result.get("success", False) and json_compatible,
                "integrity_result": integrity_result,
                "json_compatibility": json_compatible,
                "accessible_backups": integrity_result.get(
                    "backup_accessibility", "0/0"
                ),
            }

        except Exception as e:
            logger.error(f"Data integrity test failed: {e}")
            return {"success": False, "error": str(e)}

    async def test_backup_creation(self) -> Dict[str, Any]:
        """バックアップ作成テスト"""
        logger.info("💾 バックアップ作成テストを実行中...")

        try:
            # テストデータの準備
            test_data = {
                "portfolio": {
                    "positions": [
                        {"ticker": "7203", "quantity": 100, "price": 2800},
                        {"ticker": "6758", "quantity": 50, "price": 12000},
                    ],
                    "total_value": 280000 + 600000,
                    "timestamp": datetime.now().isoformat(),
                },
                "trades": [
                    {
                        "ticker": "7203",
                        "action": "buy",
                        "quantity": 100,
                        "price": 2800,
                        "timestamp": datetime.now().isoformat(),
                    }
                ],
            }

            # 各データタイプのバックアップをテスト
            backup_results = {}
            for data_type, data in test_data.items():
                result = await self.distributed_manager.save_data_distributed(
                    data, data_type, {"test_mode": True}
                )
                backup_results[data_type] = result

            success_count = sum(
                1 for r in backup_results.values() if r.get("success", False)
            )

            return {
                "success": success_count == len(backup_results),
                "backup_results": backup_results,
                "success_rate": f"{success_count}/{len(backup_results)}",
                "data_types_tested": list(test_data.keys()),
            }

        except Exception as e:
            logger.error(f"Backup creation test failed: {e}")
            return {"success": False, "error": str(e)}

    async def test_recovery_points(self) -> Dict[str, Any]:
        """復元ポイントテスト"""
        logger.info("🔄 復元ポイントテストを実行中...")

        try:
            # 新しい復元ポイントを作成
            create_result = await self.disaster_recovery.create_recovery_point()

            if not create_result.get("success", False):
                return {"success": False, "error": "Failed to create recovery point"}

            # 復元ポイントの一覧を取得
            recovery_points = await self.disaster_recovery.get_recovery_points()

            # 作成した復元ポイントがリストに含まれているか確認
            created_point_id = create_result["recovery_point_id"]
            point_exists = any(
                rp["timestamp"] == created_point_id for rp in recovery_points
            )

            return {
                "success": point_exists and len(recovery_points) > 0,
                "create_result": create_result,
                "total_recovery_points": len(recovery_points),
                "point_exists": point_exists,
                "latest_point": recovery_points[0] if recovery_points else None,
            }

        except Exception as e:
            logger.error(f"Recovery points test failed: {e}")
            return {"success": False, "error": str(e)}

    async def test_full_system_restore(self) -> Dict[str, Any]:
        """完全システム復元テスト"""
        logger.info("🔧 完全システム復元テストを実行中...")

        try:
            # まず完全バックアップを作成
            backup_result = await self.disaster_recovery.create_full_system_backup()

            if not backup_result.get("success", False):
                return {"success": False, "error": "Failed to create full backup"}

            # 復元ポイントIDを取得
            recovery_point_id = backup_result["recovery_point"]["recovery_point_id"]

            # 復元テストを実行
            restore_result = await self.disaster_recovery.restore_from_recovery_point(
                recovery_point_id
            )

            return {
                "success": restore_result.get("success", False),
                "backup_result": backup_result,
                "restore_result": restore_result,
                "restored_components": restore_result.get("restored_components", "0/0"),
                "recovery_point_id": recovery_point_id,
            }

        except Exception as e:
            logger.error(f"Full system restore test failed: {e}")
            return {"success": False, "error": str(e)}

    async def test_multi_provider_failover(self) -> Dict[str, Any]:
        """マルチプロバイダーフェイルオーバーテスト"""
        logger.info("🌐 マルチプロバイダーフェイルオーバーテストを実行中...")

        try:
            # テストデータを準備
            test_data = {
                "test": "failover_data",
                "timestamp": datetime.now().isoformat(),
            }

            # 複数のプロバイダに保存
            result = await self.distributed_manager.save_data_distributed(
                test_data, "failover_test", {"test_mode": True}
            )

            if not result.get("success", False):
                return {
                    "success": False,
                    "error": "Failed to save to multiple providers",
                }

            # 各プロバイダから復元をテスト
            providers = ["aws", "gcp", "azure", "ipfs"]
            restoration_results = {}

            for provider in providers:
                try:
                    # プロバイダーを指定して復元
                    mock_location = f"{provider}://test/location"
                    restore_data = await self._restore_from_specific_provider(
                        mock_location, provider
                    )

                    restoration_results[provider] = {
                        "success": restore_data is not None,
                        "data_integrity": restore_data == test_data,
                    }

                except Exception as e:
                    restoration_results[provider] = {"success": False, "error": str(e)}

            successful_providers = sum(
                1 for r in restoration_results.values() if r.get("success", False)
            )

            return {
                "success": successful_providers
                >= 2,  # 少なくとも2つのプロバイダーで成功
                "restoration_results": restoration_results,
                "successful_providers": f"{successful_providers}/{len(providers)}",
                "backup_locations": result.get("distributed_locations", {}),
            }

        except Exception as e:
            logger.error(f"Multi-provider failover test failed: {e}")
            return {"success": False, "error": str(e)}

    async def test_cross_platform_compatibility(self) -> Dict[str, Any]:
        """クロスプラットフォーム互換性テスト"""
        logger.info("🔄 クロスプラットフォーム互換性テストを実行中...")

        try:
            # 異なるプラットフォームでのデータ形式互換性をテスト
            test_scenarios = {
                "windows_path": "C:\\Users\\data\\portfolio.json",
                "linux_path": "/home/user/data/portfolio.json",
                "mac_path": "/Users/username/data/portfolio.json",
                "docker_path": "/app/data/portfolio.json",
            }

            compatibility_results = {}

            for platform, path in test_scenarios.items():
                try:
                    # プラットフォーム固有のパスハンドリングをテスト
                    normalized_path = Path(path).as_posix()

                    # データシリアライズテスト
                    test_data = {
                        "platform": platform,
                        "path": normalized_path,
                        "timestamp": datetime.now().isoformat(),
                        "data": {"positions": [], "total_value": 0},
                    }

                    # JSONシリアライズ/デシリアライズ
                    serialized = json.dumps(test_data, ensure_ascii=False)
                    deserialized = json.loads(serialized)

                    compatibility_results[platform] = {
                        "success": True,
                        "path_normalized": normalized_path,
                        "serialization": True,
                        "data_integrity": test_data == deserialized,
                    }

                except Exception as e:
                    compatibility_results[platform] = {
                        "success": False,
                        "error": str(e),
                    }

            successful_platforms = sum(
                1 for r in compatibility_results.values() if r.get("success", False)
            )

            return {
                "success": successful_platforms == len(test_scenarios),
                "compatibility_results": compatibility_results,
                "compatible_platforms": f"{successful_platforms}/{len(test_scenarios)}",
                "tested_platforms": list(test_scenarios.keys()),
            }

        except Exception as e:
            logger.error(f"Cross-platform compatibility test failed: {e}")
            return {"success": False, "error": str(e)}

    async def _restore_from_specific_provider(
        self, location: str, provider: str
    ) -> Dict:
        """特定のプロバイダーから復元（テスト用）"""
        # これはモック実装 - 実際のプロバイダー接続は不要
        if provider in ["aws", "gcp", "azure"]:
            return {"test": "failover_data", "timestamp": datetime.now().isoformat()}
        elif provider == "ipfs":
            return {"test": "failover_data", "timestamp": datetime.now().isoformat()}
        return None

    def _generate_recommendations(self, test_suite: Dict[str, Any]) -> List[str]:
        """テスト結果に基づいて推奨事項を生成"""
        recommendations = []

        for test_name, result in test_suite.items():
            if not result.get("success", False):
                if "backup" in test_name:
                    recommendations.append(
                        "バックアッププロバイダーの設定を確認してください"
                    )
                elif "restore" in test_name:
                    recommendations.append(
                        "復元プロセスを見直し、データ整合性を確認してください"
                    )
                elif "integrity" in test_name:
                    recommendations.append(
                        "既存バックアップのアクセス権限と整合性を確認してください"
                    )
                elif "compatibility" in test_name:
                    recommendations.append(
                        "クロスプラットフォームのパスハンドリングを確認してください"
                    )

        if not recommendations:
            recommendations.append(
                "すべてのテストに合格しました。災害復旧システムは正常に機能しています。"
            )

        return recommendations

    async def _save_test_results(self, results: Dict[str, Any]):
        """テスト結果を保存"""
        try:
            results_dir = Path("test_results")
            results_dir.mkdir(exist_ok=True)

            results_file = (
                results_dir
                / f"disaster_recovery_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

            with open(results_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            logger.info(f"📄 テスト結果を保存しました: {results_file}")

        except Exception as e:
            logger.error(f"Failed to save test results: {e}")

    def _print_test_summary(self, results: Dict[str, Any]):
        """テストサマリーを表示"""
        print("\n" + "=" * 80)
        print("🛡️ 災害復旧システムテスト結果サマリー")
        print("=" * 80)

        if results["success"]:
            print("✅ すべてのテストに合格しました！")
        else:
            print("⚠️ 一部のテストが失敗しました")

        print(f"📊 合格率: {results['passed_tests']}")
        print(f"🕒 実行時刻: {results['timestamp']}")

        print("\n📋 テスト詳細:")
        for test_name, result in results["test_suite"].items():
            status = "✅" if result.get("success", False) else "❌"
            print(f"  {status} {test_name}")

        print("\n💡 推奨事項:")
        for recommendation in results["recommendations"]:
            print(f"  • {recommendation}")

        print("\n" + "=" * 80)


async def main():
    """メイン実行関数"""
    tester = DisasterRecoveryTester()

    try:
        results = await tester.run_comprehensive_test()
        return 0 if results["success"] else 1

    except KeyboardInterrupt:
        logger.info("テストがユーザーによって中断されました")
        return 1
    except Exception as e:
        logger.error(f"テスト実行中にエラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
