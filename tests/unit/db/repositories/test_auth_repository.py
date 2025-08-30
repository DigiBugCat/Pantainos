"""
Tests for AuthRepository - OAuth token and API key management
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from pantainos.db.repositories.auth_repository import AuthRepository


@pytest.fixture
def mock_secure_storage():
    """Create mock SecureStorageRepository"""
    return AsyncMock()


@pytest.fixture
def auth_repo(mock_secure_storage):
    """Create AuthRepository with mocked storage"""
    return AuthRepository(mock_secure_storage)


@pytest.mark.asyncio
async def test_store_oauth_token_success(auth_repo, mock_secure_storage):
    """Test storing OAuth token successfully"""
    await auth_repo.store_oauth_token(
        platform="twitch",
        account_type="broadcaster",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        expires_in=3600,
        scopes=["chat:read", "chat:write"],
        user_id="12345",
        username="testuser",
    )

    mock_secure_storage.store_secret.assert_called_once()
    args, kwargs = mock_secure_storage.store_secret.call_args

    assert kwargs["namespace"] == "auth_twitch"
    assert kwargs["key"] == "broadcaster"

    # Check token data structure
    token_data = json.loads(kwargs["value"])
    assert token_data["access_token"] == "test_access_token"
    assert token_data["refresh_token"] == "test_refresh_token"
    assert token_data["scopes"] == ["chat:read", "chat:write"]
    assert token_data["user_id"] == "12345"
    assert token_data["username"] == "testuser"

    # Check metadata
    metadata = kwargs["metadata"]
    assert metadata["platform"] == "twitch"
    assert metadata["account_type"] == "broadcaster"
    assert metadata["token_type"] == "oauth2"
    assert "expires_at" in metadata


@pytest.mark.asyncio
async def test_store_oauth_token_validation_error(auth_repo):
    """Test OAuth token validation errors"""
    with pytest.raises(ValueError, match="required"):
        await auth_repo.store_oauth_token("", "broadcaster", "token")

    with pytest.raises(ValueError, match="required"):
        await auth_repo.store_oauth_token("twitch", "", "token")

    with pytest.raises(ValueError, match="required"):
        await auth_repo.store_oauth_token("twitch", "broadcaster", "")


@pytest.mark.asyncio
async def test_store_oauth_token_storage_error(auth_repo, mock_secure_storage):
    """Test OAuth token storage error handling"""
    mock_secure_storage.store_secret.side_effect = Exception("Storage error")

    with pytest.raises(RuntimeError, match="OAuth token storage failed"):
        await auth_repo.store_oauth_token("twitch", "broadcaster", "token")


@pytest.mark.asyncio
async def test_get_oauth_token_success(auth_repo, mock_secure_storage):
    """Test retrieving OAuth token successfully"""
    token_data = {
        "access_token": "test_token",
        "refresh_token": "test_refresh",
        "scopes": ["read"],
        "user_id": "123",
        "username": "user",
    }
    metadata = {"expires_at": "2024-12-31T23:59:59", "platform": "twitch"}

    mock_secure_storage.get_secret.return_value = json.dumps(token_data)
    mock_secure_storage.get_metadata.return_value = metadata

    result = await auth_repo.get_oauth_token("twitch", "broadcaster")

    assert result["access_token"] == "test_token"
    assert result["expires_at"] == "2024-12-31T23:59:59"
    assert result["platform"] == "twitch"


@pytest.mark.asyncio
async def test_get_oauth_token_not_found(auth_repo, mock_secure_storage):
    """Test getting non-existent OAuth token"""
    mock_secure_storage.get_secret.return_value = None

    result = await auth_repo.get_oauth_token("twitch", "broadcaster")
    assert result is None


@pytest.mark.asyncio
async def test_get_oauth_token_invalid_params(auth_repo):
    """Test getting OAuth token with invalid parameters"""
    result = await auth_repo.get_oauth_token("", "broadcaster")
    assert result is None

    result = await auth_repo.get_oauth_token("twitch", "")
    assert result is None


@pytest.mark.asyncio
async def test_get_oauth_token_json_error(auth_repo, mock_secure_storage):
    """Test OAuth token JSON parsing error"""
    mock_secure_storage.get_secret.return_value = "invalid json"

    result = await auth_repo.get_oauth_token("twitch", "broadcaster")
    assert result is None


@pytest.mark.asyncio
async def test_refresh_oauth_token_success(auth_repo, mock_secure_storage):
    """Test refreshing OAuth token"""
    existing_token = {"access_token": "old_token", "refresh_token": "old_refresh", "scopes": ["read"], "user_id": "123"}

    mock_secure_storage.get_secret.return_value = json.dumps(existing_token)
    mock_secure_storage.get_metadata.return_value = {"expires_at": None}

    await auth_repo.refresh_oauth_token(
        platform="twitch",
        account_type="broadcaster",
        new_access_token="new_token",
        new_refresh_token="new_refresh",
        expires_in=7200,
    )

    # Should call store_secret twice (once in refresh, once from store_oauth_token)
    assert mock_secure_storage.store_secret.call_count >= 1


@pytest.mark.asyncio
async def test_refresh_oauth_token_validation_error(auth_repo):
    """Test refresh token validation errors"""
    with pytest.raises(ValueError, match="required"):
        await auth_repo.refresh_oauth_token("", "broadcaster", "token")


@pytest.mark.asyncio
async def test_refresh_oauth_token_not_found(auth_repo, mock_secure_storage):
    """Test refreshing non-existent OAuth token"""
    mock_secure_storage.get_secret.return_value = None

    with pytest.raises(RuntimeError, match="No existing token found"):
        await auth_repo.refresh_oauth_token("twitch", "broadcaster", "new_token")


@pytest.mark.asyncio
async def test_delete_oauth_token_success(auth_repo, mock_secure_storage):
    """Test deleting OAuth token successfully"""
    mock_secure_storage.delete_secret.return_value = True

    result = await auth_repo.delete_oauth_token("twitch", "broadcaster")

    assert result is True
    mock_secure_storage.delete_secret.assert_called_with("auth_twitch", "broadcaster")


@pytest.mark.asyncio
async def test_delete_oauth_token_invalid_params(auth_repo):
    """Test deleting OAuth token with invalid parameters"""
    result = await auth_repo.delete_oauth_token("", "broadcaster")
    assert result is False

    result = await auth_repo.delete_oauth_token("twitch", "")
    assert result is False


@pytest.mark.asyncio
async def test_is_token_expired_valid_token(auth_repo, mock_secure_storage):
    """Test checking non-expired token"""
    future_time = (datetime.now() + timedelta(hours=1)).isoformat()
    token_data = {"access_token": "token", "expires_at": future_time}

    mock_secure_storage.get_secret.return_value = json.dumps(token_data)
    mock_secure_storage.get_metadata.return_value = {"expires_at": future_time}

    result = await auth_repo.is_token_expired("twitch", "broadcaster")
    assert result is False


@pytest.mark.asyncio
async def test_is_token_expired_expired_token(auth_repo, mock_secure_storage):
    """Test checking expired token"""
    past_time = (datetime.now() - timedelta(hours=1)).isoformat()
    token_data = {"access_token": "token", "expires_at": past_time}

    mock_secure_storage.get_secret.return_value = json.dumps(token_data)
    mock_secure_storage.get_metadata.return_value = {"expires_at": past_time}

    result = await auth_repo.is_token_expired("twitch", "broadcaster")
    assert result is True


@pytest.mark.asyncio
async def test_is_token_expired_no_expiration(auth_repo, mock_secure_storage):
    """Test checking token without expiration info"""
    token_data = {"access_token": "token"}

    mock_secure_storage.get_secret.return_value = json.dumps(token_data)
    mock_secure_storage.get_metadata.return_value = {}

    result = await auth_repo.is_token_expired("twitch", "broadcaster")
    assert result is None


@pytest.mark.asyncio
async def test_is_token_expired_token_not_found(auth_repo, mock_secure_storage):
    """Test checking expiration for non-existent token"""
    mock_secure_storage.get_secret.return_value = None

    result = await auth_repo.is_token_expired("twitch", "broadcaster")
    assert result is None


@pytest.mark.asyncio
async def test_store_api_key_success(auth_repo, mock_secure_storage):
    """Test storing API key successfully"""
    await auth_repo.store_api_key(
        platform="twitch", key_name="webhook_secret", api_key="secret_value", description="Webhook verification secret"
    )

    mock_secure_storage.store_secret.assert_called_once_with(
        namespace="api_twitch",
        key="webhook_secret",
        value="secret_value",
        metadata={
            "platform": "twitch",
            "key_name": "webhook_secret",
            "description": "Webhook verification secret",
            "key_type": "api_key",
        },
    )


@pytest.mark.asyncio
async def test_store_api_key_validation_error(auth_repo):
    """Test API key validation errors"""
    with pytest.raises(ValueError, match="required"):
        await auth_repo.store_api_key("", "key", "value")


@pytest.mark.asyncio
async def test_get_api_key_success(auth_repo, mock_secure_storage):
    """Test retrieving API key"""
    mock_secure_storage.get_secret.return_value = "secret_value"

    result = await auth_repo.get_api_key("twitch", "webhook_secret")

    assert result == "secret_value"
    mock_secure_storage.get_secret.assert_called_with("api_twitch", "webhook_secret")


@pytest.mark.asyncio
async def test_get_api_key_invalid_params(auth_repo):
    """Test getting API key with invalid parameters"""
    result = await auth_repo.get_api_key("", "key")
    assert result is None


@pytest.mark.asyncio
async def test_delete_api_key_success(auth_repo, mock_secure_storage):
    """Test deleting API key"""
    mock_secure_storage.delete_secret.return_value = True

    result = await auth_repo.delete_api_key("twitch", "webhook_secret")

    assert result is True
    mock_secure_storage.delete_secret.assert_called_with("api_twitch", "webhook_secret")


@pytest.mark.asyncio
async def test_list_platform_credentials(auth_repo, mock_secure_storage):
    """Test listing platform credentials"""
    mock_secure_storage.list_keys.side_effect = [
        ["broadcaster", "bot"],  # OAuth keys
        ["webhook_secret", "client_secret"],  # API keys
    ]

    result = await auth_repo.list_platform_credentials("twitch")

    assert result["oauth_tokens"] == ["broadcaster", "bot"]
    assert result["api_keys"] == ["webhook_secret", "client_secret"]


@pytest.mark.asyncio
async def test_clear_platform_credentials(auth_repo, mock_secure_storage):
    """Test clearing platform credentials"""
    mock_secure_storage.clear_namespace.side_effect = [3, 2]  # OAuth, API

    result = await auth_repo.clear_platform_credentials("twitch")

    assert result == 5
    mock_secure_storage.clear_namespace.assert_any_call("auth_twitch")
    mock_secure_storage.clear_namespace.assert_any_call("api_twitch")


@pytest.mark.asyncio
async def test_get_auth_summary(auth_repo, mock_secure_storage):
    """Test getting authentication summary"""
    mock_secure_storage.list_namespaces.return_value = [
        "auth_twitch",
        "auth_discord",
        "api_twitch",
        "api_youtube",
        "other_namespace",
    ]

    mock_secure_storage.list_keys.side_effect = [
        ["broadcaster", "bot"],  # auth_twitch
        ["user"],  # auth_discord
        ["webhook_secret"],  # api_twitch
        ["api_key"],  # api_youtube
    ]

    result = await auth_repo.get_auth_summary()

    assert len(result["oauth_platforms"]) == 2
    assert len(result["api_platforms"]) == 2
    assert result["total_oauth_tokens"] == 3  # 2 + 1
    assert result["total_api_keys"] == 2  # 1 + 1


@pytest.mark.asyncio
async def test_validate_token_format_valid(auth_repo):
    """Test valid token format validation"""
    valid_token = {"access_token": "token", "refresh_token": "refresh", "scopes": ["read"], "user_id": "123"}

    result = await auth_repo.validate_token_format(valid_token)
    assert result is True


@pytest.mark.asyncio
async def test_validate_token_format_invalid_missing_required(auth_repo):
    """Test invalid token format - missing required field"""
    invalid_token = {"refresh_token": "refresh"}

    result = await auth_repo.validate_token_format(invalid_token)
    assert result is False


@pytest.mark.asyncio
async def test_validate_token_format_invalid_extra_field(auth_repo):
    """Test invalid token format - extra field"""
    invalid_token = {"access_token": "token", "unexpected_field": "value"}

    result = await auth_repo.validate_token_format(invalid_token)
    assert result is False


@pytest.mark.asyncio
async def test_validate_token_format_invalid_scopes(auth_repo):
    """Test invalid token format - scopes not list"""
    invalid_token = {"access_token": "token", "scopes": "not_a_list"}

    result = await auth_repo.validate_token_format(invalid_token)
    assert result is False
