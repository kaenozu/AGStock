import os
import shutil
import datetime
from pathlib import Path

def backup_data():
    """Backup Paper Trading database and reports."""
    print("=== AGStock Backup Utility ===")
    
    # Create backup directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"backups/backup_{timestamp}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nBackup directory: {backup_dir}")
    
    # Backup database
    db_path = Path("paper_trade.db")
    if db_path.exists():
        shutil.copy2(db_path, backup_dir / "paper_trade.db")
        print(f"✓ Backed up: paper_trade.db ({db_path.stat().st_size / 1024:.1f} KB)")
    else:
        print("⚠ paper_trade.db not found")
    
    # Backup reports
    reports_dir = Path("reports")
    if reports_dir.exists():
        shutil.copytree(reports_dir, backup_dir / "reports", dirs_exist_ok=True)
        num_files = len(list((backup_dir / "reports").glob("*")))
        print(f"✓ Backed up: reports/ ({num_files} files)")
    else:
        print("⚠ reports/ directory not found")
    
    # Backup backtest results
    for file in ["backtest_summary.csv", "backtest_comparison.html"]:
        file_path = Path(file)
        if file_path.exists():
            shutil.copy2(file_path, backup_dir / file)
            print(f"✓ Backed up: {file}")
    
    # Create backup info
    info_path = backup_dir / "backup_info.txt"
    with open(info_path, 'w') as f:
        f.write(f"AGStock Backup\n")
        f.write(f"Created: {datetime.datetime.now()}\n")
        f.write(f"Backup ID: {timestamp}\n")
    
    print(f"\n✓ Backup complete: {backup_dir}")
    print(f"\nTo restore:")
    print(f"  1. Copy paper_trade.db back to project root")
    print(f"  2. Copy reports/ back to project root")
    
    # Cleanup old backups (keep last 10)
    cleanup_old_backups()

def cleanup_old_backups(keep=10):
    """Keep only the most recent N backups."""
    backups_dir = Path("backups")
    if not backups_dir.exists():
        return
    
    backups = sorted(backups_dir.glob("backup_*"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if len(backups) > keep:
        print(f"\nCleaning up old backups (keeping {keep} most recent)...")
        for old_backup in backups[keep:]:
            shutil.rmtree(old_backup)
            print(f"  Deleted: {old_backup.name}")

def restore_backup(backup_id):
    """Restore from a specific backup."""
    backup_dir = Path(f"backups/backup_{backup_id}")
    
    if not backup_dir.exists():
        print(f"Error: Backup {backup_id} not found")
        return
    
    print(f"Restoring from: {backup_dir}")
    
    # Restore database
    db_backup = backup_dir / "paper_trade.db"
    if db_backup.exists():
        shutil.copy2(db_backup, "paper_trade.db")
        print("✓ Restored: paper_trade.db")
    
    # Restore reports
    reports_backup = backup_dir / "reports"
    if reports_backup.exists():
        shutil.copytree(reports_backup, "reports", dirs_exist_ok=True)
        print("✓ Restored: reports/")
    
    print("\n✓ Restore complete")

def list_backups():
    """List all available backups."""
    backups_dir = Path("backups")
    if not backups_dir.exists():
        print("No backups found")
        return
    
    backups = sorted(backups_dir.glob("backup_*"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not backups:
        print("No backups found")
        return
    
    print("\nAvailable backups:")
    for backup in backups:
        timestamp = backup.name.replace("backup_", "")
        size = sum(f.stat().st_size for f in backup.rglob("*") if f.is_file()) / (1024 * 1024)
        print(f"  {timestamp} ({size:.1f} MB)")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "list":
            list_backups()
        elif command == "restore" and len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        else:
            print("Usage:")
            print("  python backup.py          # Create backup")
            print("  python backup.py list     # List backups")
            print("  python backup.py restore <backup_id>")
    else:
        backup_data()
