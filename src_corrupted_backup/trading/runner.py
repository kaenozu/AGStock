import sys
from src.cache_config import install_cache
from .fully_automated_trader import FullyAutomatedTrader
def run_daily_routine(force_run: bool = False):
    try:
        # キャッシュ設定
        install_cache()
# 完全自動トレーダー実行
trader = FullyAutomatedTrader()
# daily_routine を呼び出し
trader.daily_routine(force_run=force_run)
            return {"status": "success", "message": "日次ルーチンが正常に完了しました。"}
        except Exception as e:
            # エラーハンドリングをここに集約
# TODO: より詳細なエラーログや通知
return {"status": "error", "message": str(e)}
if __name__ == "__main__":
    # コマンドラインから実行された場合の処理
    force_run_arg = "--force" in sys.argv
    result = run_daily_routine(force_run=force_run_arg)
        if result["status"] == "error":
            print(f"エラーが発生しました: {result['message']}")
        sys.exit(1)
    else:
        print(result["message"])
