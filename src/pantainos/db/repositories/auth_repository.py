"""
Authentication repository for managing OAuth tokens and authentication credentials.

Uses SecureStorageRepository for encrypted storage of sensitive authentication data.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from pantainos.db.repositories.secure_storage_repository import SecureStorageRepository

logger = logging.getLogger(__name__)


class AuthRepository:
    """
    Repository for managing authentication tokens and credentials.

    Provides high-level authentication operations built on top of
    SecureStorageRepository for encrypted token storage.
    """

    def __init__(self, secure_storage: SecureStorageRepository) -> None:
        """
        Initialize authentication repository.

        Args:
            secure_storage: SecureStorageRepository instance for encrypted storage
        """
        self.storage = secure_storage

    async def store_oauth_token(
        self,
        platform: str,
        account_type: str,
        access_token: str,
        refresh_token: str | None = None,
        expires_in: int | None = None,
        scopes: list[str] | None = None,
        user_id: str | None = None,
        username: str | None = None,
    ) -> None:
        """
        Store OAuth token credentials for a platform and account type.

        Args:
            platform: Platform name (e.g., "twitch", "discord", "youtube")
            account_type: Account type (e.g., "broadcaster", "bot", "moderator")
            access_token: OAuth access token
            refresh_token: OAuth refresh token (optional)
            expires_in: Token expiration time in seconds (optional)
            scopes: List of granted scopes (optional)
            user_id: Platform user ID (optional)
            username: Platform username (optional)

        Raises:
            ValueError: If required parameters are missing
            RuntimeError: If storage operation fails
        """
        if not platform or not account_type or not access_token:
            raise ValueError("Platform, account_type, and access_token are required")

        namespace = f"auth_{platform}"
        key = account_type

        # Calculate expiration datetime if expires_in is provided
        expires_at = None
        if expires_in is not None:
            expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()

        # Prepare token data
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "scopes": scopes or [],
            "user_id": user_id,
            "username": username,
        }

        # Prepare metadata
        metadata = {
            "platform": platform,
            "account_type": account_type,
            "expires_at": expires_at,
            "token_type": "oauth2",
        }

        try:
            await self.storage.store_secret(
                namespace=namespace,
                key=key,
                value=json.dumps(token_data),
                metadata=metadata,
            )

            logger.info(f"Stored OAuth token for {platform}:{account_type}")

        except Exception as e:
            logger.error(f"Failed to store OAuth token for {platform}:{account_type}: {e}")
            raise RuntimeError(f"OAuth token storage failed: {e}") from e

    async def get_oauth_token(self, platform: str, account_type: str) -> dict[str, Any] | None:
        """
        Retrieve OAuth token credentials.

        Args:
            platform: Platform name
            account_type: Account type

        Returns:
            Dictionary with token data or None if not found

        Raises:
            RuntimeError: If retrieval fails
        """
        if not platform or not account_type:
            return None

        namespace = f"auth_{platform}"
        key = account_type

        try:
            token_json = await self.storage.get_secret(namespace, key)
            if not token_json:
                return None

            token_data: dict[str, Any] = json.loads(token_json)

            # Get metadata for expiration info
            metadata = await self.storage.get_metadata(namespace, key)
            if metadata:
                token_data["expires_at"] = metadata.get("expires_at")
                token_data["platform"] = metadata.get("platform")
                token_data["account_type"] = metadata.get("account_type")

            return token_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OAuth token for {platform}:{account_type}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve OAuth token for {platform}:{account_type}: {e}")
            raise RuntimeError(f"OAuth token retrieval failed: {e}") from e

    async def refresh_oauth_token(
        self,
        platform: str,
        account_type: str,
        new_access_token: str,
        new_refresh_token: str | None = None,
        expires_in: int | None = None,
    ) -> None:
        """
        Update OAuth token with refreshed credentials.

        Args:
            platform: Platform name
            account_type: Account type
            new_access_token: New access token
            new_refresh_token: New refresh token (optional)
            expires_in: Token expiration time in seconds (optional)

        Raises:
            ValueError: If required parameters are missing
            RuntimeError: If token doesn't exist or update fails
        """
        if not platform or not account_type or not new_access_token:
            raise ValueError("Platform, account_type, and new_access_token are required")

        # Get existing token data
        existing_token = await self.get_oauth_token(platform, account_type)
        if not existing_token:
            raise RuntimeError(f"No existing token found for {platform}:{account_type}")

        # Update token data
        existing_token["access_token"] = new_access_token
        if new_refresh_token is not None:
            existing_token["refresh_token"] = new_refresh_token

        # Calculate new expiration time if provided
        new_expires_in = expires_in

        # Store updated token
        await self.store_oauth_token(
            platform=platform,
            account_type=account_type,
            access_token=new_access_token,
            refresh_token=existing_token.get("refresh_token"),
            expires_in=new_expires_in,
            scopes=existing_token.get("scopes"),
            user_id=existing_token.get("user_id"),
            username=existing_token.get("username"),
        )

        logger.info(f"Refreshed OAuth token for {platform}:{account_type}")

    async def delete_oauth_token(self, platform: str, account_type: str) -> bool:
        """
        Delete OAuth token credentials.

        Args:
            platform: Platform name
            account_type: Account type

        Returns:
            True if token was deleted, False if not found
        """
        if not platform or not account_type:
            return False

        namespace = f"auth_{platform}"
        key = account_type

        deleted = await self.storage.delete_secret(namespace, key)
        if deleted:
            logger.info(f"Deleted OAuth token for {platform}:{account_type}")

        return deleted

    async def is_token_expired(self, platform: str, account_type: str) -> bool | None:
        """
        Check if an OAuth token is expired.

        Args:
            platform: Platform name
            account_type: Account type

        Returns:
            True if expired, False if valid, None if token not found or no expiration info
        """
        token = await self.get_oauth_token(platform, account_type)
        if not token:
            return None

        expires_at_str = token.get("expires_at")
        if not expires_at_str:
            return None  # No expiration info available

        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            return datetime.now() >= expires_at
        except (ValueError, TypeError):
            logger.warning(f"Invalid expiration format for {platform}:{account_type}")
            return None

    async def store_api_key(
        self,
        platform: str,
        key_name: str,
        api_key: str,
        description: str | None = None,
    ) -> None:
        """
        Store an API key for a platform.

        Args:
            platform: Platform name
            key_name: Key identifier (e.g., "webhook_secret", "client_secret")
            api_key: API key value
            description: Optional description

        Raises:
            ValueError: If required parameters are missing
            RuntimeError: If storage operation fails
        """
        if not platform or not key_name or not api_key:
            raise ValueError("Platform, key_name, and api_key are required")

        namespace = f"api_{platform}"
        metadata = {
            "platform": platform,
            "key_name": key_name,
            "description": description,
            "key_type": "api_key",
        }

        try:
            await self.storage.store_secret(
                namespace=namespace,
                key=key_name,
                value=api_key,
                metadata=metadata,
            )

            logger.info(f"Stored API key {key_name} for {platform}")

        except Exception as e:
            logger.error(f"Failed to store API key {key_name} for {platform}: {e}")
            raise RuntimeError(f"API key storage failed: {e}") from e

    async def get_api_key(self, platform: str, key_name: str) -> str | None:
        """
        Retrieve an API key.

        Args:
            platform: Platform name
            key_name: Key identifier

        Returns:
            API key value or None if not found
        """
        if not platform or not key_name:
            return None

        namespace = f"api_{platform}"
        return await self.storage.get_secret(namespace, key_name)

    async def delete_api_key(self, platform: str, key_name: str) -> bool:
        """
        Delete an API key.

        Args:
            platform: Platform name
            key_name: Key identifier

        Returns:
            True if key was deleted, False if not found
        """
        if not platform or not key_name:
            return False

        namespace = f"api_{platform}"
        deleted = await self.storage.delete_secret(namespace, key_name)
        if deleted:
            logger.info(f"Deleted API key {key_name} for {platform}")

        return deleted

    async def list_platform_credentials(self, platform: str) -> dict[str, list[str]]:
        """
        List all credential types for a platform.

        Args:
            platform: Platform name

        Returns:
            Dictionary with credential types and their keys
        """
        if not platform:
            return {}

        auth_namespace = f"auth_{platform}"
        api_namespace = f"api_{platform}"

        oauth_keys = await self.storage.list_keys(auth_namespace)
        api_keys = await self.storage.list_keys(api_namespace)

        return {
            "oauth_tokens": oauth_keys,
            "api_keys": api_keys,
        }

    async def clear_platform_credentials(self, platform: str) -> int:
        """
        Clear all credentials for a platform.

        Args:
            platform: Platform name

        Returns:
            Total number of credentials deleted
        """
        if not platform:
            return 0

        auth_namespace = f"auth_{platform}"
        api_namespace = f"api_{platform}"

        deleted_count = 0
        deleted_count += await self.storage.clear_namespace(auth_namespace)
        deleted_count += await self.storage.clear_namespace(api_namespace)

        logger.info(f"Cleared {deleted_count} credentials for platform {platform}")
        return deleted_count

    async def get_auth_summary(self) -> dict[str, Any]:
        """
        Get a summary of all stored authentication credentials.

        Returns:
            Dictionary with authentication summary information
        """
        all_namespaces = await self.storage.list_namespaces()

        auth_platforms = []
        api_platforms = []

        for namespace in all_namespaces:
            if namespace.startswith("auth_"):
                platform = namespace[5:]  # Remove "auth_" prefix
                keys = await self.storage.list_keys(namespace)
                auth_platforms.append({"platform": platform, "account_types": keys})

            elif namespace.startswith("api_"):
                platform = namespace[4:]  # Remove "api_" prefix
                keys = await self.storage.list_keys(namespace)
                api_platforms.append({"platform": platform, "api_keys": keys})

        return {
            "oauth_platforms": auth_platforms,
            "api_platforms": api_platforms,
            "total_oauth_tokens": sum(len(p["account_types"]) for p in auth_platforms),
            "total_api_keys": sum(len(p["api_keys"]) for p in api_platforms),
        }

    async def validate_token_format(self, token_data: dict[str, Any]) -> bool:
        """
        Validate OAuth token data format.

        Args:
            token_data: Token data dictionary

        Returns:
            True if format is valid, False otherwise
        """
        required_fields = ["access_token"]
        optional_fields = ["refresh_token", "scopes", "user_id", "username", "expires_at"]

        # Check required fields
        for field in required_fields:
            if field not in token_data or not token_data[field]:
                return False

        # Check that all fields are expected
        for field in token_data:
            if field not in required_fields + optional_fields:
                return False

        # Validate scopes format - return False if scopes exists, is not None, and is not a list
        return not (
            "scopes" in token_data and token_data["scopes"] is not None and not isinstance(token_data["scopes"], list)
        )
