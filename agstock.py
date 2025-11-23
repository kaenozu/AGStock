import argparse
import sys
from src.config import config

def main():
    parser = argparse.ArgumentParser(description="AGStock - AI Trading System CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: run (Auto Trader)
    parser_run = subparsers.add_parser("run", help="Run the automated trading system")

    # Command: backtest (Run Backtests)
    parser_backtest = subparsers.add_parser("backtest", help="Run comprehensive backtests and generate report")

    # Command: backup (Backup Data)
    parser_backup = subparsers.add_parser("backup", help="Backup database and reports")
    parser_backup.add_argument("--list", action="store_true", help="List available backups")
    parser_backup.add_argument("--restore", type=str, help="Restore from a specific backup ID")

    args = parser.parse_args()

    if args.command == "run":
        print("🚀 Starting Auto Trader...")
        from auto_trader import run_auto_trader
        run_auto_trader()

    elif args.command == "backtest":
        print("📊 Starting Backtest Report...")
        from backtest_report import generate_backtest_report
        generate_backtest_report()

    elif args.command == "backup":
        import backup
        if args.list:
            backup.list_backups()
        elif args.restore:
            backup.restore_backup(args.restore)
        else:
            backup.backup_data()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
