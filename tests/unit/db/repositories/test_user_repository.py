"""
Tests for UserRepository - User management and platform identity linking
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pantainos.db.repositories.user_repository import UserRepository


@pytest.fixture
def mock_database():
    """Create mock Database instance"""
    db = AsyncMock()
    db.fetchone.return_value = None
    db.fetchall.return_value = []
    db.fetchval.return_value = 0
    cursor = MagicMock()
    cursor.rowcount = 1
    cursor.lastrowid = 123
    db.execute.return_value = cursor
    return db


@pytest.fixture
def user_repo(mock_database):
    """Create UserRepository with mocked database"""
    return UserRepository(mock_database)


@pytest.mark.asyncio
async def test_create_user_success(user_repo, mock_database):
    """Test creating user successfully"""
    mock_database.execute.return_value.lastrowid = 123

    user = await user_repo.create_user("testuser", "Test User", 100, 3600)

    assert user.id == 123
    assert user.username == "testuser"
    assert user.display_name == "Test User"
    assert user.points == 100
    assert user.watch_time == 3600

    mock_database.execute.assert_called_once()
    mock_database.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_defaults(user_repo, mock_database):
    """Test creating user with default values"""
    mock_database.execute.return_value.lastrowid = 124

    user = await user_repo.create_user("testuser")

    assert user.display_name == "testuser"  # defaults to username
    assert user.points == 0
    assert user.watch_time == 0


@pytest.mark.asyncio
async def test_create_user_validation_error(user_repo):
    """Test create user validation errors"""
    with pytest.raises(ValueError, match="cannot be empty"):
        await user_repo.create_user("")

    with pytest.raises(ValueError, match="cannot be empty"):
        await user_repo.create_user("   ")


@pytest.mark.asyncio
async def test_create_user_no_lastrowid(user_repo, mock_database):
    """Test create user when lastrowid is None"""
    mock_database.execute.return_value.lastrowid = None

    with pytest.raises(RuntimeError, match="Failed to get user ID"):
        await user_repo.create_user("testuser")


@pytest.mark.asyncio
async def test_create_user_database_error(user_repo, mock_database):
    """Test create user database error handling"""
    mock_database.execute.side_effect = Exception("Database error")

    with pytest.raises(RuntimeError, match="User creation failed"):
        await user_repo.create_user("testuser")


@pytest.mark.asyncio
async def test_get_user_by_id_success(user_repo, mock_database):
    """Test getting user by ID successfully"""
    mock_database.fetchone.return_value = (
        123,
        "testuser",
        "Test User",
        100,
        3600,
        "2024-01-01 00:00:00",
        "2024-01-02 12:00:00",
    )

    user = await user_repo.get_user_by_id(123)

    assert user is not None
    assert user.id == 123
    assert user.username == "testuser"
    assert user.display_name == "Test User"
    assert user.points == 100
    assert user.watch_time == 3600


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(user_repo, mock_database):
    """Test getting non-existent user by ID"""
    mock_database.fetchone.return_value = None

    user = await user_repo.get_user_by_id(999)

    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_username_success(user_repo, mock_database):
    """Test getting user by username successfully"""
    mock_database.fetchone.return_value = (
        123,
        "testuser",
        "Test User",
        100,
        3600,
        "2024-01-01 00:00:00",
        "2024-01-02 12:00:00",
    )

    user = await user_repo.get_user_by_username("testuser")

    assert user is not None
    assert user.username == "testuser"


@pytest.mark.asyncio
async def test_get_user_by_username_not_found(user_repo, mock_database):
    """Test getting non-existent user by username"""
    mock_database.fetchone.return_value = None

    user = await user_repo.get_user_by_username("nonexistent")

    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_username_empty(user_repo):
    """Test getting user by empty username"""
    user = await user_repo.get_user_by_username("")

    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_platform_success(user_repo, mock_database):
    """Test getting user by platform identity"""
    mock_database.fetchone.return_value = (
        123,
        "testuser",
        "Test User",
        100,
        3600,
        "2024-01-01 00:00:00",
        "2024-01-02 12:00:00",
    )

    user = await user_repo.get_user_by_platform("twitch", "12345")

    assert user is not None
    assert user.id == 123


@pytest.mark.asyncio
async def test_get_user_by_platform_not_found(user_repo, mock_database):
    """Test getting user by non-existent platform identity"""
    mock_database.fetchone.return_value = None

    user = await user_repo.get_user_by_platform("twitch", "99999")

    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_platform_invalid_params(user_repo):
    """Test getting user by platform with invalid parameters"""
    user = await user_repo.get_user_by_platform("", "12345")
    assert user is None

    user = await user_repo.get_user_by_platform("twitch", "")
    assert user is None


@pytest.mark.asyncio
async def test_update_user_success(user_repo, mock_database):
    """Test updating user successfully"""
    mock_database.execute.return_value.rowcount = 1

    result = await user_repo.update_user(123, username="newname", points=200)

    assert result is True
    # Should call execute for each field being updated
    assert mock_database.execute.call_count == 2
    mock_database.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_not_found(user_repo, mock_database):
    """Test updating non-existent user"""
    mock_database.execute.return_value.rowcount = 0

    result = await user_repo.update_user(999, username="newname")

    assert result is False


@pytest.mark.asyncio
async def test_update_user_no_changes(user_repo):
    """Test updating user with no changes"""
    result = await user_repo.update_user(123)

    assert result is True  # Nothing to update


@pytest.mark.asyncio
async def test_update_user_validation_error(user_repo):
    """Test update user validation errors"""
    with pytest.raises(ValueError, match="cannot be empty"):
        await user_repo.update_user(123, username="")


@pytest.mark.asyncio
async def test_update_user_database_error(user_repo, mock_database):
    """Test update user database error handling"""
    mock_database.commit.side_effect = Exception("Database error")

    with pytest.raises(RuntimeError, match="User update failed"):
        await user_repo.update_user(123, username="newname")


@pytest.mark.asyncio
async def test_delete_user_success(user_repo, mock_database):
    """Test deleting user successfully"""
    mock_database.execute.return_value.rowcount = 1

    result = await user_repo.delete_user(123)

    assert result is True
    mock_database.execute.assert_called_with("DELETE FROM users WHERE id = ?", (123,))
    mock_database.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_user_not_found(user_repo, mock_database):
    """Test deleting non-existent user"""
    mock_database.execute.return_value.rowcount = 0

    result = await user_repo.delete_user(999)

    assert result is False


@pytest.mark.asyncio
async def test_delete_user_database_error(user_repo, mock_database):
    """Test delete user database error handling"""
    mock_database.execute.side_effect = Exception("Database error")

    with pytest.raises(RuntimeError, match="User deletion failed"):
        await user_repo.delete_user(123)


@pytest.mark.asyncio
async def test_link_platform_identity_success(user_repo, mock_database):
    """Test linking platform identity successfully"""
    # Mock user exists
    mock_database.fetchone.return_value = (
        123,
        "testuser",
        "Test User",
        100,
        3600,
        "2024-01-01 00:00:00",
        "2024-01-02 12:00:00",
    )

    identity = await user_repo.link_platform_identity(123, "twitch", "12345", "twitchuser", is_primary=True)

    assert identity.user_id == 123
    assert identity.platform == "twitch"
    assert identity.platform_user_id == "12345"
    assert identity.platform_username == "twitchuser"
    assert identity.is_primary is True

    # Should call execute twice (unset primary, insert new)
    assert mock_database.execute.call_count == 2
    mock_database.commit.assert_called_once()


@pytest.mark.asyncio
async def test_link_platform_identity_not_primary(user_repo, mock_database):
    """Test linking non-primary platform identity"""
    # Mock user exists
    mock_database.fetchone.return_value = (
        123,
        "testuser",
        "Test User",
        100,
        3600,
        "2024-01-01 00:00:00",
        "2024-01-02 12:00:00",
    )

    identity = await user_repo.link_platform_identity(123, "twitch", "12345", "twitchuser", is_primary=False)

    assert identity.is_primary is False

    # Should call execute once (just insert, no primary unset)
    assert mock_database.execute.call_count == 1


@pytest.mark.asyncio
async def test_link_platform_identity_user_not_exists(user_repo, mock_database):
    """Test linking platform identity for non-existent user"""
    mock_database.fetchone.return_value = None

    with pytest.raises(RuntimeError, match="Platform identity linking failed"):
        await user_repo.link_platform_identity(999, "twitch", "12345", "twitchuser")


@pytest.mark.asyncio
async def test_link_platform_identity_validation_error(user_repo):
    """Test link platform identity validation errors"""
    with pytest.raises(ValueError, match="required"):
        await user_repo.link_platform_identity(123, "", "12345", "twitchuser")

    with pytest.raises(ValueError, match="required"):
        await user_repo.link_platform_identity(123, "twitch", "", "twitchuser")

    with pytest.raises(ValueError, match="required"):
        await user_repo.link_platform_identity(123, "twitch", "12345", "")


@pytest.mark.asyncio
async def test_link_platform_identity_database_error(user_repo, mock_database):
    """Test link platform identity database error handling"""
    # Mock user exists
    mock_database.fetchone.return_value = (123, "testuser", "Test User", 100, 3600, "2024-01-01", "2024-01-02")
    mock_database.execute.side_effect = Exception("Database error")

    with pytest.raises(RuntimeError, match="Platform identity linking failed"):
        await user_repo.link_platform_identity(123, "twitch", "12345", "twitchuser")


@pytest.mark.asyncio
async def test_unlink_platform_identity_success(user_repo, mock_database):
    """Test unlinking platform identity successfully"""
    mock_database.execute.return_value.rowcount = 1

    result = await user_repo.unlink_platform_identity("twitch", "12345")

    assert result is True
    mock_database.execute.assert_called_with(
        "DELETE FROM user_identities WHERE platform = ? AND platform_user_id = ?", ("twitch", "12345")
    )
    mock_database.commit.assert_called_once()


@pytest.mark.asyncio
async def test_unlink_platform_identity_not_found(user_repo, mock_database):
    """Test unlinking non-existent platform identity"""
    mock_database.execute.return_value.rowcount = 0

    result = await user_repo.unlink_platform_identity("twitch", "99999")

    assert result is False


@pytest.mark.asyncio
async def test_unlink_platform_identity_invalid_params(user_repo):
    """Test unlinking platform identity with invalid parameters"""
    result = await user_repo.unlink_platform_identity("", "12345")
    assert result is False

    result = await user_repo.unlink_platform_identity("twitch", "")
    assert result is False


@pytest.mark.asyncio
async def test_unlink_platform_identity_database_error(user_repo, mock_database):
    """Test unlink platform identity database error handling"""
    mock_database.execute.side_effect = Exception("Database error")

    with pytest.raises(RuntimeError, match="Platform identity unlinking failed"):
        await user_repo.unlink_platform_identity("twitch", "12345")


@pytest.mark.asyncio
async def test_get_user_identities_success(user_repo, mock_database):
    """Test getting user identities successfully"""
    mock_database.fetchall.return_value = [
        (123, "twitch", "12345", "twitchuser", True, "2024-01-01 00:00:00"),
        (123, "discord", "67890", "discorduser", False, "2024-01-02 00:00:00"),
    ]

    identities = await user_repo.get_user_identities(123)

    assert len(identities) == 2
    assert identities[0].platform == "twitch"
    assert identities[0].is_primary is True
    assert identities[1].platform == "discord"
    assert identities[1].is_primary is False


@pytest.mark.asyncio
async def test_get_user_identities_empty(user_repo, mock_database):
    """Test getting user identities when none exist"""
    mock_database.fetchall.return_value = []

    identities = await user_repo.get_user_identities(123)

    assert len(identities) == 0


@pytest.mark.asyncio
async def test_get_or_create_user_by_platform_existing(user_repo, mock_database):
    """Test get or create user when user already exists"""
    # Mock existing user found
    mock_database.fetchone.return_value = (
        123,
        "testuser",
        "Test User",
        100,
        3600,
        "2024-01-01 00:00:00",
        "2024-01-02 12:00:00",
    )

    user, was_created = await user_repo.get_or_create_user_by_platform("twitch", "12345", "twitchuser")

    assert user.id == 123
    assert was_created is False


@pytest.mark.asyncio
async def test_get_or_create_user_by_platform_create_new(user_repo, mock_database):
    """Test get or create user when creating new user"""
    # Mock sequence: get_user_by_platform (None), get_user_by_username (None), get_user_by_id (user data)
    user_data = (124, "twitchuser", "Display Name", 0, 0, "2024-01-01 00:00:00", "2024-01-02 12:00:00")
    mock_database.fetchone.side_effect = [None, None, user_data]
    mock_database.execute.return_value.lastrowid = 124

    user, was_created = await user_repo.get_or_create_user_by_platform("twitch", "12345", "twitchuser", "Display Name")

    assert user.id == 124
    assert user.username == "twitchuser"
    assert user.display_name == "Display Name"
    assert was_created is True


@pytest.mark.asyncio
async def test_get_or_create_user_by_platform_username_conflict(user_repo, mock_database):
    """Test get or create user with username conflict resolution"""
    user_data = (124, "twitchuser_twitch_1", "twitchuser", 0, 0, "2024-01-01 00:00:00", "2024-01-02 12:00:00")
    existing_user_data = (999, "twitchuser", "Existing User", 100, 1000, "2024-01-01 00:00:00", "2024-01-02 12:00:00")

    # Mock sequence: get_user_by_platform (None), get_user_by_username conflicts (existing user) then success (None), get_user_by_id (user_data)
    mock_database.fetchone.side_effect = [
        None,  # get_user_by_platform - no existing user
        existing_user_data,  # get_user_by_username("twitchuser") - username conflict (existing user)
        None,  # get_user_by_username("twitchuser_twitch_1") - available
        user_data,  # get_user_by_id(124) in link_platform_identity - user exists
    ]
    mock_database.execute.return_value.lastrowid = 124

    user, was_created = await user_repo.get_or_create_user_by_platform("twitch", "12345", "twitchuser")

    assert user.username == "twitchuser_twitch_1"
    assert was_created is True


@pytest.mark.asyncio
async def test_get_or_create_user_by_platform_validation_error(user_repo):
    """Test get or create user validation errors"""
    with pytest.raises(ValueError, match="required"):
        await user_repo.get_or_create_user_by_platform("", "12345", "twitchuser")


@pytest.mark.asyncio
async def test_get_or_create_user_by_platform_database_error(user_repo, mock_database):
    """Test get or create user database error handling"""
    # Let initial checks succeed, then fail on user creation
    mock_database.fetchone.side_effect = [None, None]  # No existing user by platform, username available
    mock_database.execute.side_effect = Exception("Database error")  # Fail on user creation

    with pytest.raises(RuntimeError, match="Get or create user failed"):
        await user_repo.get_or_create_user_by_platform("twitch", "12345", "twitchuser")


@pytest.mark.asyncio
async def test_update_user_activity_success(user_repo, mock_database):
    """Test updating user activity successfully"""
    mock_database.execute.return_value.rowcount = 1

    result = await user_repo.update_user_activity(123, points_delta=50, watch_time_delta=1800)

    assert result is True
    mock_database.execute.assert_called_with(
        "\n                UPDATE users\n                SET points = max(0, points + ?),\n                    watch_time = max(0, watch_time + ?),\n                    last_seen = CURRENT_TIMESTAMP\n                WHERE id = ?\n                ",
        (50, 1800, 123),
    )
    mock_database.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_activity_not_found(user_repo, mock_database):
    """Test updating activity for non-existent user"""
    mock_database.execute.return_value.rowcount = 0

    result = await user_repo.update_user_activity(999, points_delta=50)

    assert result is False


@pytest.mark.asyncio
async def test_update_user_activity_no_changes(user_repo):
    """Test updating user activity with no changes"""
    result = await user_repo.update_user_activity(123, points_delta=0, watch_time_delta=0)

    assert result is True  # Nothing to update


@pytest.mark.asyncio
async def test_update_user_activity_database_error(user_repo, mock_database):
    """Test update user activity database error handling"""
    mock_database.execute.side_effect = Exception("Database error")

    with pytest.raises(RuntimeError, match="Activity update failed"):
        await user_repo.update_user_activity(123, points_delta=50)


@pytest.mark.asyncio
async def test_get_user_stats_success(user_repo, mock_database):
    """Test getting user statistics successfully"""
    mock_database.fetchval.side_effect = [100, 25]  # total_users, recent_users
    mock_database.fetchall.side_effect = [
        [("user1", 1000), ("user2", 800)],  # top points
        [("user3", 36000), ("user4", 18000)],  # top watch time
        [("twitch", 50), ("discord", 30)],  # platform breakdown
    ]

    stats = await user_repo.get_user_stats()

    assert stats["total_users"] == 100
    assert stats["recent_active_users"] == 25
    assert len(stats["top_users_by_points"]) == 2
    assert stats["top_users_by_points"][0]["username"] == "user1"
    assert stats["top_users_by_points"][0]["points"] == 1000
    assert len(stats["top_users_by_watch_time"]) == 2
    assert stats["platform_breakdown"]["twitch"] == 50
    assert stats["platform_breakdown"]["discord"] == 30


@pytest.mark.asyncio
async def test_get_user_stats_empty_database(user_repo, mock_database):
    """Test getting user statistics from empty database"""
    mock_database.fetchval.return_value = None
    mock_database.fetchall.return_value = []

    stats = await user_repo.get_user_stats()

    assert stats["total_users"] == 0
    assert stats["recent_active_users"] == 0
    assert len(stats["top_users_by_points"]) == 0
    assert len(stats["top_users_by_watch_time"]) == 0
    assert len(stats["platform_breakdown"]) == 0


@pytest.mark.asyncio
async def test_list_users_success(user_repo, mock_database):
    """Test listing users successfully"""
    mock_database.fetchall.return_value = [
        (123, "user1", "User One", 100, 3600, "2024-01-01", "2024-01-02"),
        (124, "user2", "User Two", 200, 7200, "2024-01-01", "2024-01-02"),
    ]

    users = await user_repo.list_users(limit=10, offset=0)

    assert len(users) == 2
    assert users[0].username == "user1"
    assert users[1].username == "user2"


@pytest.mark.asyncio
async def test_list_users_with_search(user_repo, mock_database):
    """Test listing users with search term"""
    mock_database.fetchall.return_value = [
        (123, "testuser", "Test User", 100, 3600, "2024-01-01", "2024-01-02"),
    ]

    users = await user_repo.list_users(search="test")

    # Verify search query was constructed properly
    call_args = mock_database.fetchall.call_args
    query = call_args[0][0]
    assert "WHERE username LIKE ? OR display_name LIKE ?" in query

    params = call_args[0][1]
    assert "%test%" in params


@pytest.mark.asyncio
async def test_list_users_pagination(user_repo, mock_database):
    """Test listing users with pagination"""
    mock_database.fetchall.return_value = []

    await user_repo.list_users(limit=25, offset=50)

    call_args = mock_database.fetchall.call_args
    params = call_args[0][1]
    # Last two params should be limit and offset
    assert params[-2:] == (25, 50)


@pytest.mark.asyncio
async def test_list_users_invalid_params(user_repo, mock_database):
    """Test listing users with invalid parameters"""
    mock_database.fetchall.return_value = []

    await user_repo.list_users(limit=-5, offset=-10)

    call_args = mock_database.fetchall.call_args
    params = call_args[0][1]
    # Should be corrected to valid values
    assert params[-2:] == (50, 0)  # limit defaults to 50, offset corrected to 0


@pytest.mark.asyncio
async def test_list_users_empty_result(user_repo, mock_database):
    """Test listing users when no results found"""
    mock_database.fetchall.return_value = []

    users = await user_repo.list_users()

    assert len(users) == 0
