import sqlite3
import os
from types import SimpleNamespace
from datetime import datetime

class CommunityDatabase:
    def __init__(self, db_path=None):
        self.db_path = db_path or "data/community.db"
        self._init_db()

    def _init_db(self):
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, email TEXT, join_date TEXT, reputation INTEGER DEFAULT 0)")
        cursor.execute("CREATE TABLE IF NOT EXISTS strategies (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, author TEXT, author_id INTEGER, title TEXT, description TEXT, code TEXT, category TEXT, tags TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, strategy_id INTEGER, user_id INTEGER, content TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS votes (id INTEGER PRIMARY KEY AUTOINCREMENT, strategy_id INTEGER, user_id INTEGER, vote INTEGER, UNIQUE(strategy_id, user_id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS follows (id INTEGER PRIMARY KEY AUTOINCREMENT, follower_id INTEGER, followed_id INTEGER)")
        conn.commit()
        conn.close()

    def create_user(self, username, email):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        join_date = datetime.now().isoformat()
        try:
            cursor.execute("INSERT INTO users (username, email, join_date, reputation) VALUES (?, ?, ?, ?)", (username, email, join_date, 0))
            uid = cursor.lastrowid
            conn.commit()
            return SimpleNamespace(user_id=uid, username=username, email=email, join_date=datetime.now(), reputation=0)
        except sqlite3.IntegrityError:
            conn.close()
            return self.get_user(username)
        finally:
            try: conn.close()
            except: pass

    def get_user(self, username=None, user_id=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if user_id:
            cursor.execute("SELECT id, username, email, reputation FROM users WHERE id = ?", (user_id,))
        else:
            cursor.execute("SELECT id, username, email, reputation FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        return SimpleNamespace(user_id=row[0], username=row[1], email=row[2], join_date=datetime.now(), reputation=row[3]) if row else None

    def create_strategy(self, **kwargs):
        name = kwargs.get('name') or kwargs.get('title') or "Untitled"
        author = kwargs.get('author') or "Unknown"
        author_id = kwargs.get('author_id') or 1
        tags = kwargs.get('tags') or []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO strategies (name, author, author_id, title, description, code, category, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                       (name, author, author_id, name, kwargs.get('description'), kwargs.get('code'), kwargs.get('category'), ",".join(tags) if isinstance(tags, list) else str(tags)))
        sid = cursor.lastrowid
        conn.commit()
        conn.close()
        return SimpleNamespace(strategy_id=sid, name=name, title=name, author=author, author_id=author_id, upvotes=0, downvotes=0, reputation=1, category=kwargs.get('category'), tags=tags)

    def get_strategies(self, category=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, author, author_id, category, tags FROM strategies")
        rows = cursor.fetchall()
        strategies = []
        for r in rows:
            sid = r[0]
            cursor.execute("SELECT COUNT(*) FROM votes WHERE strategy_id = ? AND vote > 0", (sid,))
            upvotes = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM votes WHERE strategy_id = ? AND vote < 0", (sid,))
            downvotes = cursor.fetchone()[0]
            tags_str = r[5] or ""
            tags = tags_str.split(",") if tags_str else []
            strategies.append(SimpleNamespace(strategy_id=sid, name=r[1], title=r[1], author=r[2], author_id=r[3], category=r[4], tags=tags, upvotes=upvotes, downvotes=downvotes))
        conn.close()
        return strategies

    def vote_strategy(self, strategy_id, user_id, vote):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Get original vote to adjust reputation correctly
        cursor.execute("SELECT vote FROM votes WHERE strategy_id = ? AND user_id = ?", (strategy_id, user_id))
        old_vote_row = cursor.fetchone()
        old_vote = old_vote_row[0] if old_vote_row else 0
        
        cursor.execute("INSERT OR REPLACE INTO votes (strategy_id, user_id, vote) VALUES (?, ?, ?)", (strategy_id, user_id, vote))
        
        # Reputation adjustment
        cursor.execute("SELECT author_id FROM strategies WHERE id = ?", (strategy_id,))
        aid_row = cursor.fetchone()
        if aid_row:
            aid = aid_row[0]
            # Simple logic: if new vote is positive and old wasn't, +1. If new is 0/neg and old was positive, -1.
            if vote > 0 and old_vote <= 0:
                cursor.execute("UPDATE users SET reputation = reputation + 1 WHERE id = ?", (aid,))
            elif vote <= 0 and old_vote > 0:
                cursor.execute("UPDATE users SET reputation = MAX(0, reputation - 1) WHERE id = ?", (aid,))
        
        conn.commit()
        conn.close()
        return True

class CommunityDashboard:
    def __init__(self, db_path=None):
        self.db = CommunityDatabase(db_path)