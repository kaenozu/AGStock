"""encryption.pyのテスト"""

import os
import tempfile

import pytest

from src.encryption import APIKeyManager, DataEncryption


@pytest.fixture
def encryption_key():
    """暗号化キー"""
    return os.urandom(32)


@pytest.fixture
def encryption(encryption_key):
    """DataEncryptionインスタンス"""
    return DataEncryption(encryption_key)


@pytest.fixture
def api_manager(encryption_key):
    """APIKeyManagerインスタンス"""
    return APIKeyManager(encryption_key)


class TestDataEncryption:
    """DataEncryptionのテスト"""

    def test_init(self, encryption_key):
        """初期化テスト"""
        enc = DataEncryption(encryption_key)
        assert enc.key == encryption_key

    def test_init_invalid_key_length(self):
        """不正なキー長のテスト"""
        with pytest.raises(ValueError):
            DataEncryption(b"short_key")

    def test_encrypt_bytes(self, encryption):
        """バイトデータの暗号化テスト"""
        data = b"test data"
        encrypted = encryption.encrypt(data)

        assert encrypted is not None
        assert encrypted != data
        assert len(encrypted) > len(data)

    def test_decrypt_bytes(self, encryption):
        """バイトデータの復号化テスト"""
        original = b"test data for decryption"
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == original

    def test_encrypt_decrypt_roundtrip(self, encryption):
        """暗号化・復号化ラウンドトリップテスト"""
        original = b"This is a secret message!"
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == original

    def test_encrypt_string(self, encryption):
        """文字列の暗号化テスト"""
        text = "Hello, World!"
        encrypted = encryption.encrypt_string(text)

        assert isinstance(encrypted, str)
        assert encrypted != text

    def test_decrypt_string(self, encryption):
        """文字列の復号化テスト"""
        original = "こんにちは、世界！"
        encrypted = encryption.encrypt_string(original)
        decrypted = encryption.decrypt_string(encrypted)

        assert decrypted == original

    def test_encrypt_string_roundtrip(self, encryption):
        """文字列の暗号化・復号化ラウンドトリップテスト"""
        original = "API Key: sk-12345-abcde"
        encrypted = encryption.encrypt_string(original)
        decrypted = encryption.decrypt_string(encrypted)

        assert decrypted == original

    def test_different_encryptions_different_results(self, encryption):
        """同じデータでも異なる暗号化結果になることを確認"""
        data = b"same data"
        encrypted1 = encryption.encrypt(data)
        encrypted2 = encryption.encrypt(data)

        # IVが異なるため、暗号文も異なる
        assert encrypted1 != encrypted2


class TestAPIKeyManager:
    """APIKeyManagerのテスト"""

    def test_init(self, encryption_key):
        """初期化テスト"""
        manager = APIKeyManager(encryption_key)
        assert manager.encryption is not None

    def test_encrypt_api_key(self, api_manager):
        """APIキー暗号化テスト"""
        api_key = "sk-test-key-12345"
        encrypted = api_manager.encrypt_api_key(api_key)

        assert isinstance(encrypted, str)
        assert encrypted != api_key

    def test_decrypt_api_key(self, api_manager):
        """APIキー復号化テスト"""
        original = "sk-production-key-67890"
        encrypted = api_manager.encrypt_api_key(original)
        decrypted = api_manager.decrypt_api_key(encrypted)

        assert decrypted == original

    def test_store_and_retrieve_api_key(self, api_manager):
        """APIキーの保存と取得テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_api_keys.db")

            api_key = "sk-my-secret-key"
            key_name = "openai"

            api_manager.store_api_key(key_name, api_key, db_path=db_path)
            retrieved = api_manager.retrieve_api_key(key_name, db_path=db_path)

            assert retrieved == api_key

    def test_retrieve_nonexistent_key(self, api_manager):
        """存在しないキーの取得テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_api_keys.db")

            # 最初にテーブルを作成するためにダミーデータを保存
            api_manager.store_api_key("dummy", "dummy-key", db_path=db_path)

            # 存在しないキーを取得
            retrieved = api_manager.retrieve_api_key("nonexistent", db_path=db_path)

            assert retrieved is None

    def test_update_api_key(self, api_manager):
        """APIキーの更新テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_api_keys.db")

            key_name = "anthropic"
            original_key = "original-key"
            updated_key = "updated-key"

            # 最初の保存
            api_manager.store_api_key(key_name, original_key, db_path=db_path)

            # 更新
            api_manager.store_api_key(key_name, updated_key, db_path=db_path)

            # 取得して確認
            retrieved = api_manager.retrieve_api_key(key_name, db_path=db_path)
            assert retrieved == updated_key
