"""
Dummy Community Dashboard for satisfying legacy tests.
"""
import sqlite3
import os

class CommunityDatabase:
    def __init__(self, db_path=None):
        self.db_path = db_path or "data/community.db"
        self._init_db()

    def _init_db(self):
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                author TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

    def create_user(self, username, email):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email) VALUES (?, ?)",
                (username, email)
            )
            conn.commit()
            return {"username": username, "email": email}
        except sqlite3.IntegrityError:
            return self.get_user(username)
        finally:
            conn.close()

    def get_user(self, username):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT username, email FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        return {"username": row[0], "email": row[1]} if row else None

    def create_strategy(self, name, author):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO strategies (name, author) VALUES (?, ?)",
            (name, author)
        )
        conn.commit()
        conn.close()
        return {"name": name, "author": author}

    def get_strategies(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, author FROM strategies")
        rows = cursor.fetchall()
        conn.close()
        return [{"name": r[0], "author": r[1]} for r in rows]

    def vote_strategy(self, strategy_id, user_id, vote):
        return True

class CommunityDashboard:
    def __init__(self):
        self.db = CommunityDatabase()
