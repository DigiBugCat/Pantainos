"""
User repository for managing platform-agnostic users and their platform identities.

Handles user CRUD operations and multi-platform identity linking.
"""

import logging
from datetime import datetime
from typing import Any

from pantainos.db.database import Database
from pantainos.db.models import User, UserIdentity

logger = logging.getLogger(__name__)


class UserRepository:
    """
    Repository for managing users and their platform identities.

    Provides methods for user management, platform identity linking,
    and cross-platform user lookup and statistics.
    """

    def __init__(self, database: Database) -> None:
        """
        Initialize user repository.

        Args:
            database: Database instance for data persistence
        """
        self.db = database

    async def create_user(
        self,
        username: str,
        display_name: str | None = None,
        points: int = 0,
        watch_time: int = 0,
    ) -> User:
        """
        Create a new platform-agnostic user.

        Args:
            username: Primary username for the user
            display_name: Display name (defaults to username)
            points: Initial points (defaults to 0)
            watch_time: Initial watch time in seconds (defaults to 0)

        Returns:
            Created User instance with assigned ID

        Raises:
            ValueError: If username is empty
            RuntimeError: If user creation fails
        """
        if not username.strip():
            raise ValueError("Username cannot be empty")

        display_name = display_name or username

        try:
            cursor = await self.db.execute(
                """
                INSERT INTO users (username, display_name, points, watch_time, first_seen, last_seen)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (username, display_name, points, watch_time),
            )
            await self.db.commit()

            user_id = cursor.lastrowid
            if not user_id:
                raise RuntimeError("Failed to get user ID after creation")

            user = User(
                id=user_id,
                username=username,
                display_name=display_name,
                points=points,
                watch_time=watch_time,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
            )

            logger.debug(f"Created user {username} with ID {user_id}")
            return user

        except Exception as e:
            logger.error(f"Failed to create user {username}: {e}")
            raise RuntimeError(f"User creation failed: {e}") from e

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Get a user by their ID.

        Args:
            user_id: User ID to look up

        Returns:
            User instance or None if not found
        """
        row = await self.db.fetchone(
            "SELECT id, username, display_name, points, watch_time, first_seen, last_seen FROM users WHERE id = ?",
            (user_id,),
        )

        if not row:
            return None

        return User(
            id=row[0],
            username=row[1],
            display_name=row[2],
            points=row[3],
            watch_time=row[4],
            first_seen=row[5],
            last_seen=row[6],
        )

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Get a user by their username.

        Args:
            username: Username to look up

        Returns:
            User instance or None if not found
        """
        if not username:
            return None

        row = await self.db.fetchone(
            "SELECT id, username, display_name, points, watch_time, first_seen, last_seen FROM users WHERE username = ?",
            (username,),
        )

        if not row:
            return None

        return User(
            id=row[0],
            username=row[1],
            display_name=row[2],
            points=row[3],
            watch_time=row[4],
            first_seen=row[5],
            last_seen=row[6],
        )

    async def get_user_by_platform(self, platform: str, platform_user_id: str) -> User | None:
        """
        Get a user by their platform identity.

        Args:
            platform: Platform name (e.g., "twitch", "discord")
            platform_user_id: Platform-specific user ID

        Returns:
            User instance or None if not found
        """
        if not platform or not platform_user_id:
            return None

        row = await self.db.fetchone(
            """
            SELECT u.id, u.username, u.display_name, u.points, u.watch_time, u.first_seen, u.last_seen
            FROM users u
            JOIN user_identities ui ON u.id = ui.user_id
            WHERE ui.platform = ? AND ui.platform_user_id = ?
            """,
            (platform, platform_user_id),
        )

        if not row:
            return None

        return User(
            id=row[0],
            username=row[1],
            display_name=row[2],
            points=row[3],
            watch_time=row[4],
            first_seen=row[5],
            last_seen=row[6],
        )

    async def update_user(
        self,
        user_id: int,
        username: str | None = None,
        display_name: str | None = None,
        points: int | None = None,
        watch_time: int | None = None,
    ) -> bool:
        """
        Update user information.

        Args:
            user_id: User ID to update
            username: New username (optional)
            display_name: New display name (optional)
            points: New points value (optional)
            watch_time: New watch time (optional)

        Returns:
            True if user was updated, False if not found

        Raises:
            ValueError: If trying to set empty username
            RuntimeError: If update fails
        """
        if username is not None and not username.strip():
            raise ValueError("Username cannot be empty")

        # Use separate update statements to avoid dynamic query construction
        updated_any = False

        if username is not None:
            cursor = await self.db.execute(
                "UPDATE users SET username = ?, last_seen = CURRENT_TIMESTAMP WHERE id = ?", (username, user_id)
            )
            updated_any = updated_any or cursor.rowcount > 0

        if display_name is not None:
            cursor = await self.db.execute(
                "UPDATE users SET display_name = ?, last_seen = CURRENT_TIMESTAMP WHERE id = ?", (display_name, user_id)
            )
            updated_any = updated_any or cursor.rowcount > 0

        if points is not None:
            cursor = await self.db.execute(
                "UPDATE users SET points = ?, last_seen = CURRENT_TIMESTAMP WHERE id = ?", (points, user_id)
            )
            updated_any = updated_any or cursor.rowcount > 0

        if watch_time is not None:
            cursor = await self.db.execute(
                "UPDATE users SET watch_time = ?, last_seen = CURRENT_TIMESTAMP WHERE id = ?", (watch_time, user_id)
            )
            updated_any = updated_any or cursor.rowcount > 0

        if not (username is not None or display_name is not None or points is not None or watch_time is not None):
            return True  # Nothing to update

        try:
            await self.db.commit()
            if updated_any:
                logger.debug(f"Updated user {user_id}")
            return updated_any

        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise RuntimeError(f"User update failed: {e}") from e

    async def delete_user(self, user_id: int) -> bool:
        """
        Delete a user and all their platform identities.

        Args:
            user_id: User ID to delete

        Returns:
            True if user was deleted, False if not found

        Raises:
            RuntimeError: If deletion fails
        """
        try:
            # Delete user (cascade will handle identities)
            cursor = await self.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
            await self.db.commit()

            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted user {user_id}")
            return deleted

        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise RuntimeError(f"User deletion failed: {e}") from e

    async def link_platform_identity(
        self,
        user_id: int,
        platform: str,
        platform_user_id: str,
        platform_username: str,
        is_primary: bool = False,
    ) -> UserIdentity:
        """
        Link a platform identity to a user.

        Args:
            user_id: User ID to link to
            platform: Platform name (e.g., "twitch", "discord")
            platform_user_id: Platform-specific user ID
            platform_username: Platform-specific username
            is_primary: Whether this is the primary identity for the platform

        Returns:
            Created UserIdentity instance

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If linking fails (e.g., identity already exists)
        """
        if not platform or not platform_user_id or not platform_username:
            raise ValueError("Platform, platform_user_id, and platform_username are required")

        try:
            # Check if user exists
            user = await self.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} does not exist")

            # If this is set as primary, unset other primary identities for this user/platform
            if is_primary:
                await self.db.execute(
                    "UPDATE user_identities SET is_primary = 0 WHERE user_id = ? AND platform = ?",
                    (user_id, platform),
                )

            # Insert the new identity
            await self.db.execute(
                """
                INSERT INTO user_identities (user_id, platform, platform_user_id, platform_username, is_primary, linked_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (user_id, platform, platform_user_id, platform_username, is_primary),
            )
            await self.db.commit()

            identity = UserIdentity(
                user_id=user_id,
                platform=platform,
                platform_user_id=platform_user_id,
                platform_username=platform_username,
                is_primary=is_primary,
                linked_at=datetime.now(),
            )

            logger.debug(f"Linked platform identity {platform}:{platform_user_id} to user {user_id}")
            return identity

        except Exception as e:
            logger.error(f"Failed to link platform identity {platform}:{platform_user_id} to user {user_id}: {e}")
            raise RuntimeError(f"Platform identity linking failed: {e}") from e

    async def unlink_platform_identity(self, platform: str, platform_user_id: str) -> bool:
        """
        Unlink a platform identity from its user.

        Args:
            platform: Platform name
            platform_user_id: Platform-specific user ID

        Returns:
            True if identity was unlinked, False if not found

        Raises:
            RuntimeError: If unlinking fails
        """
        if not platform or not platform_user_id:
            return False

        try:
            cursor = await self.db.execute(
                "DELETE FROM user_identities WHERE platform = ? AND platform_user_id = ?",
                (platform, platform_user_id),
            )
            await self.db.commit()

            unlinked = cursor.rowcount > 0
            if unlinked:
                logger.debug(f"Unlinked platform identity {platform}:{platform_user_id}")
            return unlinked

        except Exception as e:
            logger.error(f"Failed to unlink platform identity {platform}:{platform_user_id}: {e}")
            raise RuntimeError(f"Platform identity unlinking failed: {e}") from e

    async def get_user_identities(self, user_id: int) -> list[UserIdentity]:
        """
        Get all platform identities for a user.

        Args:
            user_id: User ID to get identities for

        Returns:
            List of UserIdentity instances
        """
        rows = await self.db.fetchall(
            """
            SELECT user_id, platform, platform_user_id, platform_username, is_primary, linked_at
            FROM user_identities
            WHERE user_id = ?
            ORDER BY platform, is_primary DESC
            """,
            (user_id,),
        )

        return [
            UserIdentity(
                user_id=row[0],
                platform=row[1],
                platform_user_id=row[2],
                platform_username=row[3],
                is_primary=bool(row[4]),
                linked_at=row[5],
            )
            for row in rows
        ]

    async def get_or_create_user_by_platform(
        self,
        platform: str,
        platform_user_id: str,
        platform_username: str,
        display_name: str | None = None,
    ) -> tuple[User, bool]:
        """
        Get existing user by platform identity or create a new one.

        Args:
            platform: Platform name
            platform_user_id: Platform-specific user ID
            platform_username: Platform-specific username
            display_name: Display name for new user (optional)

        Returns:
            Tuple of (User, was_created)

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If operation fails
        """
        if not platform or not platform_user_id or not platform_username:
            raise ValueError("Platform, platform_user_id, and platform_username are required")

        # Try to find existing user
        existing_user = await self.get_user_by_platform(platform, platform_user_id)
        if existing_user:
            return existing_user, False

        # Create new user
        try:
            # Use platform username as base username
            base_username = platform_username
            username = base_username

            # Handle username conflicts by appending platform
            counter = 1
            while await self.get_user_by_username(username):
                username = f"{base_username}_{platform}_{counter}"
                counter += 1

            user = await self.create_user(
                username=username,
                display_name=display_name or platform_username,
                points=0,
                watch_time=0,
            )

            # Link platform identity
            await self.link_platform_identity(
                user_id=user.id,  # type: ignore[arg-type]
                platform=platform,
                platform_user_id=platform_user_id,
                platform_username=platform_username,
                is_primary=True,
            )

            logger.info(f"Created new user {username} for platform {platform}:{platform_user_id}")
            return user, True

        except Exception as e:
            logger.error(f"Failed to get or create user for {platform}:{platform_user_id}: {e}")
            raise RuntimeError(f"Get or create user failed: {e}") from e

    async def update_user_activity(self, user_id: int, points_delta: int = 0, watch_time_delta: int = 0) -> bool:
        """
        Update user activity metrics (points and watch time).

        Args:
            user_id: User ID to update
            points_delta: Points to add (can be negative)
            watch_time_delta: Watch time to add in seconds (can be negative)

        Returns:
            True if user was updated, False if not found

        Raises:
            RuntimeError: If update fails
        """
        if points_delta == 0 and watch_time_delta == 0:
            return True  # Nothing to update

        try:
            cursor = await self.db.execute(
                """
                UPDATE users
                SET points = max(0, points + ?),
                    watch_time = max(0, watch_time + ?),
                    last_seen = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (points_delta, watch_time_delta, user_id),
            )
            await self.db.commit()

            updated = cursor.rowcount > 0
            if updated:
                logger.debug(f"Updated activity for user {user_id}: +{points_delta} points, +{watch_time_delta}s")
            return updated

        except Exception as e:
            logger.error(f"Failed to update activity for user {user_id}: {e}")
            raise RuntimeError(f"Activity update failed: {e}") from e

    async def get_user_stats(self) -> dict[str, Any]:
        """
        Get user statistics.

        Returns:
            Dictionary with user statistics
        """
        total_users = await self.db.fetchval("SELECT COUNT(*) FROM users") or 0

        # Top users by points
        top_points_rows = await self.db.fetchall("SELECT username, points FROM users ORDER BY points DESC LIMIT 10")

        # Top users by watch time
        top_time_rows = await self.db.fetchall(
            "SELECT username, watch_time FROM users ORDER BY watch_time DESC LIMIT 10"
        )

        # Platform breakdown
        platform_rows = await self.db.fetchall(
            "SELECT platform, COUNT(*) FROM user_identities GROUP BY platform ORDER BY COUNT(*) DESC"
        )

        # Recent activity (users seen in last 24 hours)
        recent_users = (
            await self.db.fetchval("SELECT COUNT(*) FROM users WHERE last_seen >= datetime('now', '-1 day')") or 0
        )

        return {
            "total_users": total_users,
            "recent_active_users": recent_users,
            "top_users_by_points": [{"username": row[0], "points": row[1]} for row in top_points_rows],
            "top_users_by_watch_time": [{"username": row[0], "watch_time": row[1]} for row in top_time_rows],
            "platform_breakdown": {row[0]: row[1] for row in platform_rows},
        }

    async def list_users(self, limit: int = 50, offset: int = 0, search: str | None = None) -> list[User]:
        """
        List users with pagination and optional search.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            search: Optional search term for username/display_name

        Returns:
            List of User instances
        """
        if limit <= 0:
            limit = 50
        if offset < 0:
            offset = 0

        query = """
            SELECT id, username, display_name, points, watch_time, first_seen, last_seen
            FROM users
        """
        params: list[Any] = []

        if search:
            query += " WHERE username LIKE ? OR display_name LIKE ?"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        query += " ORDER BY last_seen DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = await self.db.fetchall(query, tuple(params))

        return [
            User(
                id=row[0],
                username=row[1],
                display_name=row[2],
                points=row[3],
                watch_time=row[4],
                first_seen=row[5],
                last_seen=row[6],
            )
            for row in rows
        ]
