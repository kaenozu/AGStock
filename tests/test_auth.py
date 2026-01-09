"""
Test Suite for Authentication System
"""

import os
import tempfile

import pytest

from src.auth import AuthManager

# Test constants (not actual secrets)
TEST_PASSWORD = os.getenv('TEST_PASSWORD', 'TestPassword123')  # For testing only
TEST_SECRET_KEY = os.getenv('TEST_SECRET_KEY', 'test-secret-key')  # For testing only


class TestAuthManager:
    """認証マネージャーのテスト"""

    @pytest.fixture
    def auth_manager(self):
        """テスト用の認証マネージャー"""
        # 一時ファイルを使用
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        auth = AuthManager(TEST_SECRET_KEY, db_path)
        yield auth

        # クリーンアップ
        del auth
        import gc

        gc.collect()

        try:
            os.unlink(db_path)
        except PermissionError:
            pass  # Windowsでのファイルロック問題を回避

    def test_password_hashing(self, auth_manager):
        """パスワードハッシュ化のテスト"""
        password = TEST_PASSWORD
        hashed = auth_manager.hash_password(password)

        assert hashed != password
        assert auth_manager.verify_password(password, hashed)
        assert not auth_manager.verify_password("WrongPassword", hashed)

    def test_password_strength_check(self, auth_manager):
        """パスワード強度チェックのテスト"""
        # 弱いパスワード
        is_strong, msg = auth_manager.check_password_strength("weak")
        assert not is_strong

        # 強いパスワード
        is_strong, msg = auth_manager.check_password_strength(TEST_PASSWORD)
        assert is_strong
        assert msg == "OK"

    def test_create_user(self, auth_manager):
        """ユーザー作成のテスト"""
        user_id = auth_manager.create_user("testuser", "test@example.com", TEST_PASSWORD)

        assert user_id is not None
        assert user_id > 0

        # 重複ユーザー
        duplicate_id = auth_manager.create_user("testuser", "test2@example.com", TEST_PASSWORD)
        assert duplicate_id is None

    def test_weak_password_rejection(self, auth_manager):
        """弱いパスワードの拒否テスト"""
        with pytest.raises(ValueError):
            auth_manager.create_user("testuser", "test@example.com", "weak")

    def test_login_success(self, auth_manager):
        """ログイン成功のテスト"""
        auth_manager.create_user("testuser", "test@example.com", TEST_PASSWORD)

        token = auth_manager.login("testuser", TEST_PASSWORD)
        assert token is not None

        # トークン検証
        payload = auth_manager.verify_token(token)
        assert payload is not None
        assert "user_id" in payload

    def test_login_failure(self, auth_manager):
        """ログイン失敗のテスト"""
        auth_manager.create_user("testuser", "test@example.com", "TestPassword123")

        token = auth_manager.login("testuser", "WrongPassword")
        assert token is None

    def test_account_lockout(self, auth_manager):
        """アカウントロックアウトのテスト"""
        auth_manager.create_user("testuser", "test@example.com", "TestPassword123")

        # 5回失敗
        for _ in range(5):
            auth_manager.login("testuser", "WrongPassword")

        # アカウントがロックされる
        assert auth_manager.is_account_locked("testuser")

        # ロック中はログインできない
        with pytest.raises(ValueError):
            auth_manager.login("testuser", TEST_PASSWORD)

    def test_logout(self, auth_manager):
        """ログアウトのテスト"""
        auth_manager.create_user("testuser", "test@example.com", TEST_PASSWORD)
        token = auth_manager.login("testuser", TEST_PASSWORD)

        # ログアウト
        success = auth_manager.logout(token)
        assert success

        # トークンが無効になる
        payload = auth_manager.verify_token(token)
        assert payload is None

    def test_session_cleanup(self, auth_manager):
        """セッションクリーンアップのテスト"""
        auth_manager.create_user("testuser", "test@example.com", TEST_PASSWORD)
        token = auth_manager.login("testuser", TEST_PASSWORD)

        # 期限切れセッションを削除
        deleted = auth_manager.cleanup_expired_sessions()
        assert deleted >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
