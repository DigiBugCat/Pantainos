"""
Secure storage repository with encryption for sensitive data like authentication tokens.

Uses cryptography.fernet for symmetric encryption with OS keyring for key management.
"""

import json
import logging
from pathlib import Path
from typing import Any

import aiofiles
from cryptography.fernet import Fernet

from pantainos.db.database import Database

logger = logging.getLogger(__name__)


class SecureStorageRepository:
    """
    Repository for securely storing sensitive data with encryption.

    Provides plugin-scoped storage where each plugin can store secrets
    in its own namespace. Data is encrypted at rest using Fernet encryption.

    Key management hierarchy:
    1. Application config: Use master_key parameter passed to constructor
    2. Development: Use keyring library for OS-level security
    3. Fallback: Generate and store key in local config file (with warnings)
    """

    def __init__(self, database: Database, master_key: str | None = None) -> None:
        """
        Initialize secure storage repository.

        Args:
            database: Database instance for data persistence
            master_key: Optional master key for encryption (overrides environment)
        """
        self.db = database
        self.master_key = master_key
        self._cipher: Fernet | None = None

    async def _get_cipher(self) -> Fernet:
        """
        Get or create the encryption cipher.

        Returns:
            Fernet cipher instance for encryption/decryption
        """
        if self._cipher is not None:
            return self._cipher

        # Try to get master key from various sources
        master_key = None

        # 1. Try provided key (from application config)
        if self.master_key:
            master_key = self.master_key
            logger.debug("Using master key from application configuration")

        # 2. Try OS keyring (development)
        if not master_key:
            try:
                import keyring

                master_key = keyring.get_password("pantainos", "master_key")
                if not master_key:
                    # Generate new key and store in keyring
                    master_key = Fernet.generate_key().decode()
                    keyring.set_password("pantainos", "master_key", master_key)
                    logger.info("Generated new master key and stored in OS keyring")
                else:
                    logger.debug("Using master key from OS keyring")

            except ImportError:
                logger.warning("Keyring library not available, falling back to local storage")
            except Exception as e:
                logger.warning(f"Failed to access OS keyring: {e}, falling back to local storage")

        # 3. Fallback: local config file (not recommended for production)
        if not master_key:
            config_path = Path("~/.pantainos/master_key").expanduser()
            try:
                if config_path.exists():
                    async with aiofiles.open(config_path, encoding="utf-8") as f:
                        master_key = (await f.read()).strip()
                        logger.debug("Using master key from local config file")
                else:
                    # Generate new key and store locally
                    config_path.parent.mkdir(parents=True, exist_ok=True)
                    master_key = Fernet.generate_key().decode()
                    async with aiofiles.open(config_path, "w", encoding="utf-8") as f:
                        await f.write(master_key)
                    # Restrict permissions
                    config_path.chmod(0o600)
                    logger.warning(
                        f"Generated new master key and stored in {config_path}. "
                        "Consider providing master_key in application config or using OS keyring for better security."
                    )
            except Exception as e:
                logger.error(f"Failed to manage local key file: {e}")
                raise RuntimeError("Unable to initialize encryption key") from e

        if not master_key:
            raise RuntimeError("Unable to obtain or generate encryption key")

        try:
            self._cipher = Fernet(master_key.encode() if isinstance(master_key, str) else master_key)
            return self._cipher
        except Exception as e:
            logger.error(f"Failed to initialize cipher: {e}")
            raise RuntimeError("Invalid encryption key") from e

    async def store_secret(
        self,
        namespace: str,
        key: str,
        value: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Store a secret value with encryption.

        Args:
            namespace: Plugin namespace (e.g., "twitch", "discord")
            key: Secret identifier (e.g., "access_token", "api_key")
            value: Secret value to encrypt and store
            metadata: Optional metadata (expiry, scopes, etc.)

        Raises:
            ValueError: If namespace or key is empty
            RuntimeError: If encryption fails
        """
        if not namespace or not key:
            raise ValueError("Namespace and key must be non-empty")

        if not value:
            logger.warning(f"Storing empty value for {namespace}.{key}")

        try:
            cipher = await self._get_cipher()
            encrypted_value = cipher.encrypt(value.encode()).decode()

            metadata_json = json.dumps(metadata or {})

            # Upsert the secret
            await self.db.execute(
                """
                INSERT INTO secure_storage (namespace, key, encrypted_value, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(namespace, key)
                DO UPDATE SET
                    encrypted_value = excluded.encrypted_value,
                    metadata = excluded.metadata,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (namespace, key, encrypted_value, metadata_json),
            )
            await self.db.commit()

            logger.debug(f"Stored secret for {namespace}.{key}")

        except Exception as e:
            logger.error(f"Failed to store secret {namespace}.{key}: {e}")
            raise RuntimeError(f"Failed to store secret: {e}") from e

    async def get_secret(self, namespace: str, key: str) -> str | None:
        """
        Retrieve and decrypt a secret value.

        Args:
            namespace: Plugin namespace
            key: Secret identifier

        Returns:
            Decrypted secret value or None if not found

        Raises:
            ValueError: If namespace or key is empty
            RuntimeError: If decryption fails
        """
        if not namespace or not key:
            raise ValueError("Namespace and key must be non-empty")

        try:
            row = await self.db.fetchone(
                "SELECT encrypted_value FROM secure_storage WHERE namespace = ? AND key = ?",
                (namespace, key),
            )

            if not row:
                return None

            cipher = await self._get_cipher()
            decrypted_value = cipher.decrypt(row[0].encode()).decode()

            logger.debug(f"Retrieved secret for {namespace}.{key}")
            return decrypted_value

        except Exception as e:
            logger.error(f"Failed to retrieve secret {namespace}.{key}: {e}")
            raise RuntimeError(f"Failed to retrieve secret: {e}") from e

    async def delete_secret(self, namespace: str, key: str) -> bool:
        """
        Delete a secret.

        Args:
            namespace: Plugin namespace
            key: Secret identifier

        Returns:
            True if secret was deleted, False if not found

        Raises:
            ValueError: If namespace or key is empty
        """
        if not namespace or not key:
            raise ValueError("Namespace and key must be non-empty")

        cursor = await self.db.execute(
            "DELETE FROM secure_storage WHERE namespace = ? AND key = ?",
            (namespace, key),
        )
        await self.db.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.debug(f"Deleted secret for {namespace}.{key}")
        else:
            logger.debug(f"Secret {namespace}.{key} not found for deletion")

        return deleted

    async def list_keys(self, namespace: str) -> list[str]:
        """
        List all secret keys in a namespace.

        Args:
            namespace: Plugin namespace

        Returns:
            List of secret keys in the namespace

        Raises:
            ValueError: If namespace is empty
        """
        if not namespace:
            raise ValueError("Namespace must be non-empty")

        rows = await self.db.fetchall(
            "SELECT key FROM secure_storage WHERE namespace = ? ORDER BY key",
            (namespace,),
        )

        return [row[0] for row in rows]

    async def get_metadata(self, namespace: str, key: str) -> dict[str, Any] | None:
        """
        Get metadata for a secret without retrieving the secret value.

        Args:
            namespace: Plugin namespace
            key: Secret identifier

        Returns:
            Metadata dictionary or None if secret not found

        Raises:
            ValueError: If namespace or key is empty
        """
        if not namespace or not key:
            raise ValueError("Namespace and key must be non-empty")

        row = await self.db.fetchone(
            "SELECT metadata, created_at, updated_at FROM secure_storage WHERE namespace = ? AND key = ?",
            (namespace, key),
        )

        if not row:
            return None

        try:
            metadata = json.loads(row[0]) if row[0] else {}
            metadata.update(
                {
                    "created_at": row[1],
                    "updated_at": row[2],
                }
            )
            return metadata
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse metadata for {namespace}.{key}: {e}")
            return {"created_at": row[1], "updated_at": row[2]}

    async def list_namespaces(self) -> list[str]:
        """
        List all namespaces that have stored secrets.

        Returns:
            List of namespace strings
        """
        rows = await self.db.fetchall("SELECT DISTINCT namespace FROM secure_storage ORDER BY namespace")
        return [row[0] for row in rows]

    async def clear_namespace(self, namespace: str) -> int:
        """
        Delete all secrets in a namespace.

        Args:
            namespace: Plugin namespace to clear

        Returns:
            Number of secrets deleted

        Raises:
            ValueError: If namespace is empty
        """
        if not namespace:
            raise ValueError("Namespace must be non-empty")

        cursor = await self.db.execute("DELETE FROM secure_storage WHERE namespace = ?", (namespace,))
        await self.db.commit()

        deleted_count = cursor.rowcount
        logger.info(f"Cleared {deleted_count} secrets from namespace '{namespace}'")
        return deleted_count

    async def rotate_encryption_key(self) -> None:
        """
        Rotate the master encryption key by re-encrypting all stored data.

        This is a potentially expensive operation that should be done during maintenance windows.

        Raises:
            RuntimeError: If key rotation fails
        """
        logger.info("Starting encryption key rotation")

        try:
            # Get current cipher
            old_cipher = await self._get_cipher()

            # Generate new key
            new_key = Fernet.generate_key()
            new_cipher = Fernet(new_key)

            # Get all encrypted data
            rows = await self.db.fetchall(
                "SELECT namespace, key, encrypted_value FROM secure_storage ORDER BY namespace, key"
            )

            if not rows:
                logger.info("No secrets to rotate")
                return

            # Re-encrypt all data
            updated_count = 0
            for row in rows:
                namespace, key, encrypted_value = row

                try:
                    # Decrypt with old key
                    decrypted_value = old_cipher.decrypt(encrypted_value.encode()).decode()

                    # Encrypt with new key
                    new_encrypted_value = new_cipher.encrypt(decrypted_value.encode()).decode()

                    # Update database
                    await self.db.execute(
                        """
                        UPDATE secure_storage
                        SET encrypted_value = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE namespace = ? AND key = ?
                        """,
                        (new_encrypted_value, namespace, key),
                    )
                    updated_count += 1

                except Exception as e:
                    logger.error(f"Failed to rotate key for {namespace}.{key}: {e}")
                    raise RuntimeError(f"Key rotation failed at {namespace}.{key}") from e

            await self.db.commit()

            # Update stored master key
            try:
                # Try keyring first
                import keyring

                keyring.set_password("pantainos", "master_key", new_key.decode())
                logger.info("Updated master key in OS keyring")

            except ImportError:
                logger.warning("Keyring not available during rotation")
            except Exception as e:
                logger.warning(f"Failed to update keyring during rotation: {e}")

                # Fallback warning for configuration update
                logger.warning("Please update your application configuration with new key: " + new_key.decode())

            # Update in-memory cipher
            self._cipher = new_cipher

            logger.info(f"Successfully rotated encryption key for {updated_count} secrets")

        except Exception as e:
            logger.error(f"Encryption key rotation failed: {e}")
            raise RuntimeError("Key rotation failed") from e
