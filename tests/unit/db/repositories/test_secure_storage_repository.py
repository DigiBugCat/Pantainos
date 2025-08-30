"""
Tests for SecureStorageRepository - Encrypted storage for sensitive data
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet

from pantainos.db.repositories.secure_storage_repository import SecureStorageRepository


@pytest.fixture
def mock_database():
    """Create mock Database instance"""
    db = AsyncMock()
    db.fetchone.return_value = None
    db.fetchall.return_value = []
    db.execute.return_value = MagicMock(rowcount=1)
    return db


@pytest.fixture
def test_key():
    """Generate a test encryption key"""
    return Fernet.generate_key().decode()


@pytest.fixture
def secure_storage_with_key(mock_database, test_key):
    """Create SecureStorageRepository with a test key"""
    return SecureStorageRepository(mock_database, master_key=test_key)


@pytest.fixture
def secure_storage_no_key(mock_database):
    """Create SecureStorageRepository without a key"""
    return SecureStorageRepository(mock_database)


@pytest.mark.asyncio
async def test_get_cipher_with_provided_key(secure_storage_with_key):
    """Test cipher initialization with provided master key"""
    cipher = await secure_storage_with_key._get_cipher()

    assert cipher is not None
    assert isinstance(cipher, Fernet)

    # Should cache the cipher
    cipher2 = await secure_storage_with_key._get_cipher()
    assert cipher is cipher2


@pytest.mark.asyncio
async def test_get_cipher_with_keyring(secure_storage_no_key):
    """Test cipher initialization with keyring fallback"""
    mock_keyring = MagicMock()
    mock_keyring.get_password.return_value = Fernet.generate_key().decode()

    with patch.dict("sys.modules", {"keyring": mock_keyring}):
        cipher = await secure_storage_no_key._get_cipher()
        assert cipher is not None
        mock_keyring.get_password.assert_called_with("pantainos", "master_key")


@pytest.mark.asyncio
async def test_get_cipher_keyring_generate_new(secure_storage_no_key):
    """Test generating new key when keyring has no stored key"""
    mock_keyring = MagicMock()
    mock_keyring.get_password.return_value = None

    with patch.dict("sys.modules", {"keyring": mock_keyring}):
        cipher = await secure_storage_no_key._get_cipher()
        assert cipher is not None
        mock_keyring.set_password.assert_called_once()


@pytest.mark.asyncio
async def test_get_cipher_keyring_unavailable(secure_storage_no_key):
    """Test fallback when keyring is not available"""
    with patch.dict("sys.modules", {"keyring": None}):
        with patch("pantainos.db.repositories.secure_storage_repository.aiofiles") as mock_aiofiles:
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "master_key"

                # Mock file operations
                mock_file = AsyncMock()
                mock_file.read.return_value = Fernet.generate_key().decode()
                mock_aiofiles.open.return_value.__aenter__.return_value = mock_file

                with patch.object(Path, "exists", return_value=True):
                    with patch.object(Path, "expanduser", return_value=config_path):
                        cipher = await secure_storage_no_key._get_cipher()
                        assert cipher is not None


@pytest.mark.asyncio
async def test_get_cipher_generate_local_key(secure_storage_no_key):
    """Test generating new local key file"""
    with patch.dict("sys.modules", {"keyring": None}):
        with patch("pantainos.db.repositories.secure_storage_repository.aiofiles") as mock_aiofiles:
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "master_key"

                # Mock file operations for creation
                mock_file = AsyncMock()
                mock_aiofiles.open.return_value.__aenter__.return_value = mock_file

                with patch.object(Path, "exists", return_value=False):
                    with patch.object(Path, "expanduser", return_value=config_path):
                        with patch.object(Path, "mkdir"):
                            with patch.object(Path, "chmod"):
                                cipher = await secure_storage_no_key._get_cipher()
                                assert cipher is not None
                                mock_file.write.assert_called_once()


@pytest.mark.asyncio
async def test_get_cipher_no_key_available(secure_storage_no_key):
    """Test error when no key is available"""
    with patch.dict("sys.modules", {"keyring": None}):
        with patch("pantainos.db.repositories.secure_storage_repository.aiofiles") as mock_aiofiles:
            mock_aiofiles.open.side_effect = Exception("File error")

            with patch.object(Path, "exists", return_value=False):
                with pytest.raises(RuntimeError, match="Unable to initialize encryption key"):
                    await secure_storage_no_key._get_cipher()


@pytest.mark.asyncio
async def test_get_cipher_invalid_key():
    """Test error with invalid encryption key"""
    invalid_storage = SecureStorageRepository(AsyncMock(), master_key="invalid_key")

    with pytest.raises(RuntimeError, match="Invalid encryption key"):
        await invalid_storage._get_cipher()


@pytest.mark.asyncio
async def test_store_secret_success(secure_storage_with_key, mock_database):
    """Test storing secret successfully"""
    await secure_storage_with_key.store_secret(
        namespace="test_plugin", key="api_key", value="secret_value", metadata={"description": "Test API key"}
    )

    mock_database.execute.assert_called_once()
    mock_database.commit.assert_called_once()

    # Verify SQL parameters
    args = mock_database.execute.call_args[0]
    assert "INSERT INTO secure_storage" in args[0]
    sql_params = args[1]
    assert sql_params[0] == "test_plugin"  # namespace
    assert sql_params[1] == "api_key"  # key
    assert sql_params[2] != "secret_value"  # encrypted_value (should be encrypted)
    assert json.loads(sql_params[3])["description"] == "Test API key"  # metadata


@pytest.mark.asyncio
async def test_store_secret_validation_error(secure_storage_with_key):
    """Test store secret validation errors"""
    with pytest.raises(ValueError, match="non-empty"):
        await secure_storage_with_key.store_secret("", "key", "value")

    with pytest.raises(ValueError, match="non-empty"):
        await secure_storage_with_key.store_secret("namespace", "", "value")


@pytest.mark.asyncio
async def test_store_secret_empty_value(secure_storage_with_key, mock_database):
    """Test storing empty secret value"""
    await secure_storage_with_key.store_secret("namespace", "key", "")

    mock_database.execute.assert_called_once()


@pytest.mark.asyncio
async def test_store_secret_database_error(secure_storage_with_key, mock_database):
    """Test store secret database error handling"""
    mock_database.execute.side_effect = Exception("Database error")

    with pytest.raises(RuntimeError, match="Failed to store secret"):
        await secure_storage_with_key.store_secret("namespace", "key", "value")


@pytest.mark.asyncio
async def test_get_secret_success(secure_storage_with_key, mock_database, test_key):
    """Test retrieving secret successfully"""
    # Encrypt test data
    cipher = Fernet(test_key.encode())
    encrypted_value = cipher.encrypt(b"secret_value").decode()

    mock_database.fetchone.return_value = (encrypted_value,)

    result = await secure_storage_with_key.get_secret("test_plugin", "api_key")

    assert result == "secret_value"
    mock_database.fetchone.assert_called_with(
        "SELECT encrypted_value FROM secure_storage WHERE namespace = ? AND key = ?", ("test_plugin", "api_key")
    )


@pytest.mark.asyncio
async def test_get_secret_not_found(secure_storage_with_key, mock_database):
    """Test retrieving non-existent secret"""
    mock_database.fetchone.return_value = None

    result = await secure_storage_with_key.get_secret("test_plugin", "api_key")

    assert result is None


@pytest.mark.asyncio
async def test_get_secret_validation_error(secure_storage_with_key):
    """Test get secret validation errors"""
    with pytest.raises(ValueError, match="non-empty"):
        await secure_storage_with_key.get_secret("", "key")

    with pytest.raises(ValueError, match="non-empty"):
        await secure_storage_with_key.get_secret("namespace", "")


@pytest.mark.asyncio
async def test_get_secret_decryption_error(secure_storage_with_key, mock_database):
    """Test get secret decryption error handling"""
    mock_database.fetchone.return_value = ("invalid_encrypted_data",)

    with pytest.raises(RuntimeError, match="Failed to retrieve secret"):
        await secure_storage_with_key.get_secret("namespace", "key")


@pytest.mark.asyncio
async def test_delete_secret_success(secure_storage_with_key, mock_database):
    """Test deleting secret successfully"""
    mock_database.execute.return_value.rowcount = 1

    result = await secure_storage_with_key.delete_secret("test_plugin", "api_key")

    assert result is True
    mock_database.execute.assert_called_with(
        "DELETE FROM secure_storage WHERE namespace = ? AND key = ?", ("test_plugin", "api_key")
    )
    mock_database.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_secret_not_found(secure_storage_with_key, mock_database):
    """Test deleting non-existent secret"""
    mock_database.execute.return_value.rowcount = 0

    result = await secure_storage_with_key.delete_secret("test_plugin", "api_key")

    assert result is False


@pytest.mark.asyncio
async def test_delete_secret_validation_error(secure_storage_with_key):
    """Test delete secret validation errors"""
    with pytest.raises(ValueError, match="non-empty"):
        await secure_storage_with_key.delete_secret("", "key")

    with pytest.raises(ValueError, match="non-empty"):
        await secure_storage_with_key.delete_secret("namespace", "")


@pytest.mark.asyncio
async def test_list_keys_success(secure_storage_with_key, mock_database):
    """Test listing keys in namespace"""
    mock_database.fetchall.return_value = [("api_key",), ("webhook_secret",)]

    result = await secure_storage_with_key.list_keys("test_plugin")

    assert result == ["api_key", "webhook_secret"]
    mock_database.fetchall.assert_called_with(
        "SELECT key FROM secure_storage WHERE namespace = ? ORDER BY key", ("test_plugin",)
    )


@pytest.mark.asyncio
async def test_list_keys_empty_namespace(secure_storage_with_key, mock_database):
    """Test listing keys in empty namespace"""
    mock_database.fetchall.return_value = []

    result = await secure_storage_with_key.list_keys("empty_plugin")

    assert result == []


@pytest.mark.asyncio
async def test_list_keys_validation_error(secure_storage_with_key):
    """Test list keys validation error"""
    with pytest.raises(ValueError, match="non-empty"):
        await secure_storage_with_key.list_keys("")


@pytest.mark.asyncio
async def test_get_metadata_success(secure_storage_with_key, mock_database):
    """Test getting metadata successfully"""
    metadata_json = json.dumps({"description": "Test key", "expires": "2024-12-31"})
    mock_database.fetchone.return_value = (metadata_json, "2024-01-01 00:00:00", "2024-01-02 12:00:00")

    result = await secure_storage_with_key.get_metadata("test_plugin", "api_key")

    assert result["description"] == "Test key"
    assert result["expires"] == "2024-12-31"
    assert result["created_at"] == "2024-01-01 00:00:00"
    assert result["updated_at"] == "2024-01-02 12:00:00"


@pytest.mark.asyncio
async def test_get_metadata_not_found(secure_storage_with_key, mock_database):
    """Test getting metadata for non-existent secret"""
    mock_database.fetchone.return_value = None

    result = await secure_storage_with_key.get_metadata("test_plugin", "api_key")

    assert result is None


@pytest.mark.asyncio
async def test_get_metadata_invalid_json(secure_storage_with_key, mock_database):
    """Test getting metadata with invalid JSON"""
    mock_database.fetchone.return_value = ("invalid json", "2024-01-01", "2024-01-02")

    result = await secure_storage_with_key.get_metadata("test_plugin", "api_key")

    # Should return timestamps even with invalid JSON metadata
    assert result["created_at"] == "2024-01-01"
    assert result["updated_at"] == "2024-01-02"


@pytest.mark.asyncio
async def test_get_metadata_validation_error(secure_storage_with_key):
    """Test get metadata validation errors"""
    with pytest.raises(ValueError, match="non-empty"):
        await secure_storage_with_key.get_metadata("", "key")


@pytest.mark.asyncio
async def test_list_namespaces_success(secure_storage_with_key, mock_database):
    """Test listing all namespaces"""
    mock_database.fetchall.return_value = [("plugin1",), ("plugin2",), ("auth_twitch",)]

    result = await secure_storage_with_key.list_namespaces()

    assert result == ["plugin1", "plugin2", "auth_twitch"]
    mock_database.fetchall.assert_called_with("SELECT DISTINCT namespace FROM secure_storage ORDER BY namespace")


@pytest.mark.asyncio
async def test_list_namespaces_empty(secure_storage_with_key, mock_database):
    """Test listing namespaces when none exist"""
    mock_database.fetchall.return_value = []

    result = await secure_storage_with_key.list_namespaces()

    assert result == []


@pytest.mark.asyncio
async def test_clear_namespace_success(secure_storage_with_key, mock_database):
    """Test clearing namespace successfully"""
    mock_database.execute.return_value.rowcount = 3

    result = await secure_storage_with_key.clear_namespace("test_plugin")

    assert result == 3
    mock_database.execute.assert_called_with("DELETE FROM secure_storage WHERE namespace = ?", ("test_plugin",))
    mock_database.commit.assert_called_once()


@pytest.mark.asyncio
async def test_clear_namespace_validation_error(secure_storage_with_key):
    """Test clear namespace validation error"""
    with pytest.raises(ValueError, match="non-empty"):
        await secure_storage_with_key.clear_namespace("")


@pytest.mark.asyncio
async def test_rotate_encryption_key_success(secure_storage_with_key, mock_database, test_key):
    """Test encryption key rotation successfully"""
    # Mock existing encrypted data
    cipher = Fernet(test_key.encode())
    encrypted_data = [
        ("plugin1", "key1", cipher.encrypt(b"secret1").decode()),
        ("plugin1", "key2", cipher.encrypt(b"secret2").decode()),
    ]
    mock_database.fetchall.return_value = encrypted_data

    with patch.dict("sys.modules", {"keyring": MagicMock()}):
        await secure_storage_with_key.rotate_encryption_key()

    # Should call execute for each secret update
    assert mock_database.execute.call_count == 2
    mock_database.commit.assert_called_once()


@pytest.mark.asyncio
async def test_rotate_encryption_key_no_secrets(secure_storage_with_key, mock_database):
    """Test key rotation with no existing secrets"""
    mock_database.fetchall.return_value = []

    await secure_storage_with_key.rotate_encryption_key()

    # Should not attempt any updates
    assert mock_database.execute.call_count == 0


@pytest.mark.asyncio
async def test_rotate_encryption_key_decryption_error(secure_storage_with_key, mock_database):
    """Test key rotation with decryption error"""
    # Mock invalid encrypted data
    mock_database.fetchall.return_value = [("plugin1", "key1", "invalid_encrypted_data")]

    with pytest.raises(RuntimeError, match="Key rotation failed"):
        await secure_storage_with_key.rotate_encryption_key()


@pytest.mark.asyncio
async def test_rotate_encryption_key_keyring_fallback(secure_storage_with_key, mock_database, test_key):
    """Test key rotation keyring fallback"""
    cipher = Fernet(test_key.encode())
    mock_database.fetchall.return_value = [("plugin1", "key1", cipher.encrypt(b"secret1").decode())]

    # Mock keyring unavailable
    with patch.dict("sys.modules", {"keyring": None}):
        await secure_storage_with_key.rotate_encryption_key()

    mock_database.execute.assert_called_once()


@pytest.mark.asyncio
async def test_encryption_roundtrip(secure_storage_with_key, mock_database, test_key):
    """Test that encryption and decryption work correctly together"""
    # Store a secret
    await secure_storage_with_key.store_secret("test", "key", "original_value")

    # Get the encrypted value from the database call
    store_args = mock_database.execute.call_args[0][1]
    encrypted_value = store_args[2]

    # Mock the database to return the encrypted value
    mock_database.fetchone.return_value = (encrypted_value,)

    # Retrieve and verify the secret
    result = await secure_storage_with_key.get_secret("test", "key")
    assert result == "original_value"


@pytest.mark.asyncio
async def test_different_keys_produce_different_encryption():
    """Test that different master keys produce different encrypted results"""
    mock_db1 = AsyncMock()
    mock_db2 = AsyncMock()

    key1 = Fernet.generate_key().decode()
    key2 = Fernet.generate_key().decode()

    storage1 = SecureStorageRepository(mock_db1, master_key=key1)
    storage2 = SecureStorageRepository(mock_db2, master_key=key2)

    await storage1.store_secret("test", "key", "same_value")
    await storage2.store_secret("test", "key", "same_value")

    encrypted1 = mock_db1.execute.call_args[0][1][2]
    encrypted2 = mock_db2.execute.call_args[0][1][2]

    # Different keys should produce different encrypted values
    assert encrypted1 != encrypted2
