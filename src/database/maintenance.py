"""
Database maintenance and optimization utilities.
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


def apply_indexes(db_path: str = "paper_trading.db") -> bool:
    """Apply performance indexes to database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        logger.info("Applying database indexes...")

        # Read and execute SQL file
        sql_file = Path(__file__).parent.parent / "database" / "add_indexes.sql"

        if sql_file.exists():
            with open(sql_file, "r") as f:
                sql_script = f.read()

            cursor.executescript(sql_script)
            conn.commit()
            logger.info("✅ Database indexes applied successfully")
        else:
            # Fallback: apply indexes directly
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON orders(timestamp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_trades_ticker ON orders(ticker)",
                "CREATE INDEX IF NOT EXISTS idx_positions_ticker ON positions(ticker)",
            ]

            for idx_sql in indexes:
                cursor.execute(idx_sql)

            conn.commit()
            logger.info("✅ Database indexes applied (fallback mode)")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"Failed to apply database indexes: {e}")
        return False


def vacuum_database(db_path: str = "paper_trading.db") -> bool:
    """Run VACUUM to optimize database file."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        logger.info("Running VACUUM on database...")
        cursor.execute("VACUUM")

        conn.close()
        logger.info("✅ Database VACUUM completed")
        return True

    except Exception as e:
        logger.error(f"Failed to vacuum database: {e}")
        return False


def get_database_stats(db_path: str = "paper_trading.db") -> dict:
    """Get database statistics."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        stats = {}

        # Get table sizes
        tables = ["orders", "positions", "balance"]
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            stats[f"{table}_count"] = count

        # Get database file size
        db_file = Path(db_path)
        if db_file.exists():
            stats["file_size_mb"] = db_file.stat().st_size / (1024 * 1024)

        conn.close()
        return stats

    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}


if __name__ == "__main__":
    # Run maintenance
    logging.basicConfig(level=logging.INFO)

    print("Applying indexes...")
    apply_indexes()

    print("\nDatabase stats:")
    stats = get_database_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nRunning VACUUM...")
    vacuum_database()
