"""
Authentication Manager - 隱崎ｨｼ繝ｻ隱榊庄繧ｷ繧ｹ繝・Β
JWT 繝医・繧ｯ繝ｳ繝吶・繧ｹ縺ｮ隱崎ｨｼ
"""

import base64
import hashlib
import hmac
import json
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import bcrypt

try:
    import jwt  # type: ignore
except ImportError:  # pragma: no cover - optional dependency fallback
    jwt = None


@dataclass
class User:
    """繝ｦ繝ｼ繧ｶ繝ｼ"""

    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    is_active: bool = True
    is_admin: bool = False
    created_at: Optional[str] = None


class AuthManager:
    """隱崎ｨｼ繝槭ロ繝ｼ繧ｸ繝｣繝ｼ"""

    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=15)

    def __init__(self, secret_key: str, db_path: str = "users.db"):
        self.secret_key = secret_key
        self.db_path = db_path
        self._init_database()

    # --- JWT helpers (PyJWT蜆ｪ蜈医∵悴蟆主・縺ｪ繧臥ｰ｡譏滴MAC鄂ｲ蜷阪↓繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ) ---
    def _encode_token(self, payload: Dict) -> str:
        """JWT繧ｨ繝ｳ繧ｳ繝ｼ繝会ｼ・yJWT縺檎┌縺代ｌ縺ｰ邁｡譏灘ｮ溯｣・ｒ菴ｿ逕ｨ・・""
        if jwt:
            return jwt.encode(payload, self.secret_key, algorithm="HS256")

        # Fallback: HS256繝ｩ繧､繧ｯ縺ｪ鄂ｲ蜷堺ｻ倥″繝医・繧ｯ繝ｳ繧堤函謌・        header = {"alg": "HS256", "typ": "JWT"}

        def _b64(data: Dict) -> str:
            raw = json.dumps(data, default=str).encode("utf-8")
            return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

        header_b64 = _b64(header)
        payload_copy = dict(payload)
        # datetime繧旦NIX繧ｿ繧､繝縺ｫ蟇・○繧具ｼ域､懆ｨｼ縺ｧ縺ｯ謨ｰ蛟､豈碑ｼ・☆繧九◆繧・ｼ・        for key in ("exp", "iat"):
            if isinstance(payload_copy.get(key), datetime):
                payload_copy[key] = int(payload_copy[key].timestamp())
        payload_b64 = _b64(payload_copy)

        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        signature = hmac.new(self.secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def _decode_token(self, token: str) -> Optional[Dict]:
        """JWT繝・さ繝ｼ繝会ｼ・yJWT縺檎┌縺代ｌ縺ｰ邁｡譏灘ｮ溯｣・ｒ菴ｿ逕ｨ・・""
        if jwt:
            try:
                return jwt.decode(token, self.secret_key, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return None
            except jwt.InvalidTokenError:
                return None

        try:
            header_b64, payload_b64, signature_b64 = token.split(".")
            signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
            expected_sig = hmac.new(self.secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
            expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).rstrip(b"=")

            if not hmac.compare_digest(expected_sig_b64, signature_b64.encode("ascii")):
                return None

            # Padding繧定｣懊≧
            def _b64decode(segment: str) -> Dict:
                padded = segment + "=" * (-len(segment) % 4)
                return json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))

            payload = _b64decode(payload_b64)

            exp = payload.get("exp")
            if isinstance(exp, (int, float)) and exp < time.time():
                return None

            return payload
        except Exception:
            return None

    def _init_database(self):
        """繝・・繧ｿ繝吶・繧ｹ蛻晄悄蛹・""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    is_admin INTEGER DEFAULT 0,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
            )

            # 繧､繝ｳ繝・ャ繧ｯ繧ｹ霑ｽ蜉
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)")

            conn.commit()

    def hash_password(self, password: str) -> str:
        """繝代せ繝ｯ繝ｼ繝峨ｒ繝上ャ繧ｷ繝･蛹・""
        salt = bcrypt.gensalt(rounds=12)  # 繧ｳ繧ｹ繝井ｿよ焚繧・2縺ｫ險ｭ螳・
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        """繝代せ繝ｯ繝ｼ繝峨ｒ讀懆ｨｼ"""
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    def check_password_strength(self, password: str) -> Tuple[bool, str]:
        """繝代せ繝ｯ繝ｼ繝牙ｼｷ蠎ｦ繝√ぉ繝・け"""
        if len(password) < 8:
            return False, "繝代せ繝ｯ繝ｼ繝峨・8譁・ｭ嶺ｻ･荳雁ｿ・ｦ√〒縺・

        if not any(c.isupper() for c in password):
            return False, "螟ｧ譁・ｭ励ｒ1譁・ｭ嶺ｻ･荳雁性繧√ｋ蠢・ｦ√′縺ゅｊ縺ｾ縺・

        if not any(c.islower() for c in password):
            return False, "蟆乗枚蟄励ｒ1譁・ｭ嶺ｻ･荳雁性繧√ｋ蠢・ｦ√′縺ゅｊ縺ｾ縺・

        if not any(c.isdigit() for c in password):
            return False, "謨ｰ蟄励ｒ1譁・ｭ嶺ｻ･荳雁性繧√ｋ蠢・ｦ√′縺ゅｊ縺ｾ縺・

        return True, "OK"

    def create_user(self, username: str, email: str, password: str, is_admin: bool = False) -> Optional[int]:
        """繝ｦ繝ｼ繧ｶ繝ｼ菴懈・"""
        # 繝代せ繝ｯ繝ｼ繝牙ｼｷ蠎ｦ繝√ぉ繝・け
        is_strong, message = self.check_password_strength(password)
        if not is_strong:
            raise ValueError(f"繝代せ繝ｯ繝ｼ繝峨′蠑ｱ縺吶℃縺ｾ縺・ {message}")

        password_hash = self.hash_password(password)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """
                    INSERT INTO users (username, email, password_hash, is_admin)
                    VALUES (?, ?, ?, ?)
                """,
                    (username, email, password_hash, is_admin),
                )

                user_id = cursor.lastrowid
                conn.commit()
                return user_id
            except sqlite3.IntegrityError:
                return None

    def get_user(self, username: str) -> Optional[User]:
        """繝ｦ繝ｼ繧ｶ繝ｼ蜿門ｾ・""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()

            if row:
                return User(
                    id=row[0],
                    username=row[1],
                    email=row[2],
                    password_hash=row[3],
                    is_active=bool(row[4]),
                    is_admin=bool(row[5]),
                    created_at=row[8],
                )
            return None

    def is_account_locked(self, username: str) -> bool:
        """繧｢繧ｫ繧ｦ繝ｳ繝医′繝ｭ繝・け縺輔ｌ縺ｦ縺・ｋ縺狗｢ｺ隱・""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT locked_until FROM users
                WHERE username = ? AND locked_until > datetime('now')
            """,
                (username,),
            )

            return cursor.fetchone() is not None

    def record_failed_login(self, username: str):
        """繝ｭ繧ｰ繧､繝ｳ螟ｱ謨励ｒ險倬鹸"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE users
                SET failed_login_attempts = failed_login_attempts + 1
                WHERE username = ?
            """,
                (username,),
            )

            cursor.execute(
                """
                SELECT failed_login_attempts FROM users WHERE username = ?
            """,
                (username,),
            )

            result = cursor.fetchone()
            if result and result[0] >= self.MAX_LOGIN_ATTEMPTS:
                # 繧｢繧ｫ繧ｦ繝ｳ繝医ｒ繝ｭ繝・け
                locked_until = datetime.utcnow() + self.LOCKOUT_DURATION
                cursor.execute(
                    """
                    UPDATE users
                    SET locked_until = ?
                    WHERE username = ?
                """,
                    (locked_until, username),
                )

            conn.commit()

    def reset_failed_login(self, username: str):
        """繝ｭ繧ｰ繧､繝ｳ螟ｱ謨励き繧ｦ繝ｳ繝医ｒ繝ｪ繧ｻ繝・ヨ"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE users
                SET failed_login_attempts = 0, locked_until = NULL
                WHERE username = ?
            """,
                (username,),
            )

            conn.commit()

    def create_token(self, user_id: int, expires_in_days: int = 7) -> str:
        """JWT繝医・繧ｯ繝ｳ菴懈・"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=expires_in_days),
            "iat": datetime.utcnow(),
        }

        token = self._encode_token(payload)

        # 繧ｻ繝・す繝ｧ繝ｳ縺ｫ菫晏ｭ・        expires_at = payload["exp"]
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO sessions (user_id, token, expires_at)
                VALUES (?, ?, ?)
            """,
                (user_id, token, expires_at),
            )

            conn.commit()

        return token

    def verify_token(self, token: str) -> Optional[Dict]:
        """繝医・繧ｯ繝ｳ讀懆ｨｼ"""
        payload = self._decode_token(token)

        if not payload:
            return None

        # 繧ｻ繝・す繝ｧ繝ｳ遒ｺ隱・        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT user_id FROM sessions
                    WHERE token = ? AND expires_at > datetime('now')
                """,
                    (token,),
                )

                result = cursor.fetchone()

                if result:
                    return payload
                return None
        except Exception:
            return None

    def login(self, username: str, password: str) -> Optional[str]:
        """繝ｭ繧ｰ繧､繝ｳ"""
        # 繧｢繧ｫ繧ｦ繝ｳ繝医Ο繝・け繝√ぉ繝・け
        if self.is_account_locked(username):
            raise ValueError("繧｢繧ｫ繧ｦ繝ｳ繝医′繝ｭ繝・け縺輔ｌ縺ｦ縺・∪縺吶・5蛻・ｾ後↓蜀崎ｩｦ陦後＠縺ｦ縺上□縺輔＞縲・)

        user = self.get_user(username)

        if not user or not user.is_active:
            self.record_failed_login(username)
            return None

        if self.verify_password(password, user.password_hash):
            self.reset_failed_login(username)
            return self.create_token(user.id)
        else:
            self.record_failed_login(username)
            return None

    def logout(self, token: str) -> bool:
        """繝ｭ繧ｰ繧｢繧ｦ繝・""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))

            success = cursor.rowcount > 0
            conn.commit()

            return success

    def cleanup_expired_sessions(self):
        """譛滄剞蛻・ｌ繧ｻ繝・す繝ｧ繝ｳ縺ｮ繧ｯ繝ｪ繝ｼ繝ｳ繧｢繝・・"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM sessions WHERE expires_at < datetime('now')
            """
            )

            deleted_count = cursor.rowcount
            conn.commit()

            return deleted_count

    def require_auth(self, token: str) -> Optional[int]:
        """隱崎ｨｼ縺悟ｿ・ｦ・ｼ医ョ繧ｳ繝ｬ繝ｼ繧ｿ逕ｨ・・""
        payload = self.verify_token(token)

        if payload:
            return payload["user_id"]
        return None


if __name__ == "__main__":
    # 繝・せ繝・
    auth = AuthManager("test-secret-key")

    # 繝ｦ繝ｼ繧ｶ繝ｼ菴懈・
    user_id = auth.create_user("testuser", "test@example.com", "TestPassword123")
    print(f"Created user: {user_id}")

    # 繝ｭ繧ｰ繧､繝ｳ
    token = auth.login("testuser", "TestPassword123")
    print(f"Login token: {token}")

    # 繝医・繧ｯ繝ｳ讀懆ｨｼ
    payload = auth.verify_token(token)
    print(f"Token payload: {payload}")

    # 繝ｭ繧ｰ繧｢繧ｦ繝・
    success = auth.logout(token)
    print(f"Logout: {success}")

    # 繧ｻ繝・す繝ｧ繝ｳ繧ｯ繝ｪ繝ｼ繝ｳ繧｢繝・・
    cleaned = auth.cleanup_expired_sessions()
    print(f"Cleaned sessions: {cleaned}")
