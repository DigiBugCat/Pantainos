"""
Database models and schema definitions
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class User:
    """Platform-agnostic user data model"""

    id: int | None = None
    username: str = ""
    display_name: str = ""
    points: int = 0
    watch_time: int = 0  # seconds
    first_seen: datetime | None = None
    last_seen: datetime | None = None


@dataclass
class UserIdentity:
    """Platform identity linking model"""

    user_id: int = 0
    platform: str = ""
    platform_user_id: str = ""
    platform_username: str = ""
    is_primary: bool = False
    linked_at: datetime | None = None


@dataclass
class Event:
    """Event data model"""

    id: int | None = None
    type: str = ""
    user_id: int | None = None
    data: dict[str, Any] | None = None
    created_at: datetime | None = None


@dataclass
class Command:
    """Command data model"""

    id: int | None = None
    name: str = ""
    response: str = ""
    enabled: bool = True
    mod_only: bool = False
    usage_count: int = 0
    created_at: datetime | None = None


@dataclass
class ChatMessage:
    """Chat message data model"""

    id: int | None = None
    user_id: int = 0
    message: str = ""
    timestamp: datetime | None = None


@dataclass
class PersistentVariable:
    """Persistent variable data model (survives restarts)"""

    name: str = ""
    value: str = ""
    data_type: str = "string"  # 'string', 'number', 'boolean', 'json'
    description: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def get_typed_value(self) -> Any:
        """Get the value converted to its proper type"""
        if self.data_type == "number":
            try:
                return float(self.value) if "." in self.value else int(self.value)
            except ValueError:
                return 0
        elif self.data_type == "boolean":
            return self.value.lower() in ("true", "1", "yes", "on")
        elif self.data_type == "json":
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return {}
        else:
            return self.value

    @classmethod
    def from_value(cls, name: str, value: Any, description: str = "") -> "PersistentVariable":
        """Create a PersistentVariable from a Python value"""
        if isinstance(value, bool):
            return cls(name=name, value=str(value).lower(), data_type="boolean", description=description)
        if isinstance(value, int | float):
            return cls(name=name, value=str(value), data_type="number", description=description)
        if isinstance(value, dict | list):
            return cls(name=name, value=json.dumps(value), data_type="json", description=description)
        return cls(name=name, value=str(value), data_type="string", description=description)


@dataclass
class SessionVariable:
    """Session variable data model (cleared on restart)"""

    name: str = ""
    value: str = ""
    data_type: str = "string"  # 'string', 'number', 'boolean', 'json'
    created_at: datetime | None = None

    def get_typed_value(self) -> Any:
        """Get the value converted to its proper type"""
        if self.data_type == "number":
            try:
                return float(self.value) if "." in self.value else int(self.value)
            except ValueError:
                return 0
        elif self.data_type == "boolean":
            return self.value.lower() in ("true", "1", "yes", "on")
        elif self.data_type == "json":
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return {}
        else:
            return self.value

    @classmethod
    def from_value(cls, name: str, value: Any) -> "SessionVariable":
        """Create a SessionVariable from a Python value"""
        if isinstance(value, bool):
            return cls(name=name, value=str(value).lower(), data_type="boolean")
        if isinstance(value, int | float):
            return cls(name=name, value=str(value), data_type="number")
        if isinstance(value, dict | list):
            return cls(name=name, value=json.dumps(value), data_type="json")
        return cls(name=name, value=str(value), data_type="string")


@dataclass
class Group:
    """Group data model"""

    name: str = ""
    description: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class GroupMember:
    """Group member data model"""

    group_name: str = ""
    username: str = ""
    added_at: datetime | None = None
    added_by: str = ""


# SQL Schema definitions
SCHEMA_SQL = """
-- Users table (platform-agnostic)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    display_name TEXT,
    points INTEGER DEFAULT 0,
    watch_time INTEGER DEFAULT 0,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User identities table (platform connections)
CREATE TABLE IF NOT EXISTS user_identities (
    user_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    platform_user_id TEXT NOT NULL,
    platform_username TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT 0,
    linked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (platform, platform_user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, platform, platform_user_id)
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    user_id INTEGER,
    data JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Commands table
CREATE TABLE IF NOT EXISTS commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    response TEXT NOT NULL,
    enabled BOOLEAN DEFAULT 1,
    mod_only BOOLEAN DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Persistent variables table (survives restarts)
CREATE TABLE IF NOT EXISTS persistent_variables (
    name TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    data_type TEXT DEFAULT 'string',
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Session variables table (cleared on restart)
CREATE TABLE IF NOT EXISTS session_variables (
    name TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    data_type TEXT DEFAULT 'string',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Groups table (group metadata)
CREATE TABLE IF NOT EXISTS groups (
    name TEXT PRIMARY KEY,
    description TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Group members table (who belongs to which group)
CREATE TABLE IF NOT EXISTS group_members (
    group_name TEXT NOT NULL,
    username TEXT NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    added_by TEXT DEFAULT '',
    PRIMARY KEY (group_name, username),
    FOREIGN KEY (group_name) REFERENCES groups(name) ON DELETE CASCADE
);

-- Modules table (module registration and status)
CREATE TABLE IF NOT EXISTS modules (
    name TEXT PRIMARY KEY,
    enabled BOOLEAN DEFAULT 1,
    settings JSON,
    loaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_identities_platform_lookup ON user_identities(platform, platform_user_id);
CREATE INDEX IF NOT EXISTS idx_identities_user_id ON user_identities(user_id);
CREATE INDEX IF NOT EXISTS idx_identities_primary ON user_identities(user_id, is_primary);
CREATE INDEX IF NOT EXISTS idx_identities_platform_username ON user_identities(platform, platform_username);
CREATE INDEX IF NOT EXISTS idx_group_members_lookup ON group_members(group_name, username);
CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(username);

-- Trigger to update updated_at on persistent_variables
CREATE TRIGGER IF NOT EXISTS update_persistent_variables_updated_at
    AFTER UPDATE ON persistent_variables
BEGIN
    UPDATE persistent_variables SET updated_at = CURRENT_TIMESTAMP WHERE name = NEW.name;
END;

-- Trigger to update updated_at on groups
CREATE TRIGGER IF NOT EXISTS update_groups_updated_at
    AFTER UPDATE ON groups
BEGIN
    UPDATE groups SET updated_at = CURRENT_TIMESTAMP WHERE name = NEW.name;
END;

-- Auth tokens table (OAuth tokens for broadcaster and bot accounts)
CREATE TABLE IF NOT EXISTS auth_tokens (
    account_type TEXT PRIMARY KEY,  -- 'broadcaster' or 'bot'
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at DATETIME,
    scopes TEXT,  -- JSON array of scopes
    user_id TEXT,  -- Twitch user ID
    username TEXT,  -- Twitch username
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Trigger to update updated_at on auth_tokens
CREATE TRIGGER IF NOT EXISTS update_auth_tokens_updated_at
    AFTER UPDATE ON auth_tokens
BEGIN
    UPDATE auth_tokens SET updated_at = CURRENT_TIMESTAMP WHERE account_type = NEW.account_type;
END;
"""
