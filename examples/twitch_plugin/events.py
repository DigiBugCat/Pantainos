"""
Twitch Plugin Events - Type-safe event models with conditions

This module demonstrates how to create EventModel subclasses with
built-in conditions that work with the Pantainos type system.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import Field

from pantainos import Condition, EventModel


class ChatMessage(EventModel):
    """
    Twitch chat message event with built-in conditions

    Example usage:
        @app.on(ChatMessage, when=ChatMessage.command("hello") & ChatMessage.from_mod())
        async def hello_cmd(event: ChatMessage, twitch: TwitchPlugin):
            await twitch.send(f"Hello {event.user}!")
    """

    event_type: ClassVar[str] = "twitch.chat.message"

    user: str
    message: str
    badges: list[str] = Field(default_factory=list)
    channel: str
    timestamp: datetime = Field(default_factory=datetime.now)
    is_mod: bool = False
    is_subscriber: bool = False

    # Event-specific conditions
    @classmethod
    def command(cls, cmd: str) -> Condition[ChatMessage]:
        """Check if message is a specific command"""

        def check(event: ChatMessage) -> bool:
            return event.message.startswith(f"!{cmd}")

        return cls.condition(check, f"command({cmd})")

    @classmethod
    def from_mod(cls) -> Condition[ChatMessage]:
        """Check if message is from a moderator"""

        def check(event: ChatMessage) -> bool:
            return "moderator" in event.badges or event.is_mod

        return cls.condition(check, "from_mod")

    @classmethod
    def from_subscriber(cls) -> Condition[ChatMessage]:
        """Check if message is from a subscriber"""

        def check(event: ChatMessage) -> bool:
            return "subscriber" in event.badges or event.is_subscriber

        return cls.condition(check, "from_subscriber")

    @classmethod
    def from_user(cls, username: str) -> Condition[ChatMessage]:
        """Check if message is from a specific user"""

        def check(event: ChatMessage) -> bool:
            return event.user.lower() == username.lower()

        return cls.condition(check, f"from_user({username})")

    @classmethod
    def contains_text(cls, text: str) -> Condition[ChatMessage]:
        """Check if message contains specific text (case-insensitive)"""

        def check(event: ChatMessage) -> bool:
            return text.lower() in event.message.lower()

        return cls.condition(check, f"contains_text({text})")

    @classmethod
    def min_length(cls, length: int) -> Condition[ChatMessage]:
        """Check if message is at least a certain length"""

        def check(event: ChatMessage) -> bool:
            return len(event.message) >= length

        return cls.condition(check, f"min_length({length})")

    @property
    def command_name(self) -> str | None:
        """Extract command name if message is a command"""
        if self.message.startswith("!"):
            parts = self.message.split()
            if parts:
                return parts[0][1:]  # Remove the !
        return None

    @property
    def command_args(self) -> list[str]:
        """Extract command arguments if message is a command"""
        if self.message.startswith("!"):
            parts = self.message.split()
            if len(parts) > 1:
                return parts[1:]
        return []


class FollowEvent(EventModel):
    """Twitch follow event"""

    event_type: ClassVar[str] = "twitch.follow"

    user: str
    channel: str
    timestamp: datetime = Field(default_factory=datetime.now)

    @classmethod
    def first_time_follower(cls) -> Condition[FollowEvent]:
        """Check if this is a first-time follow (requires additional tracking)"""

        # This would need to be implemented with database lookup
        def check(_event: FollowEvent) -> bool:
            # Placeholder - would check database for previous follows
            return True

        return cls.condition(check, "first_time_follower")


class RaidEvent(EventModel):
    """Twitch raid event"""

    event_type: ClassVar[str] = "twitch.raid"

    from_channel: str
    to_channel: str
    viewers: int
    timestamp: datetime = Field(default_factory=datetime.now)

    @classmethod
    def min_viewers(cls, count: int) -> Condition[RaidEvent]:
        """Check if raid has minimum viewer count"""

        def check(event: RaidEvent) -> bool:
            return event.viewers >= count

        return cls.condition(check, f"min_viewers({count})")

    @classmethod
    def from_partner(cls) -> Condition[RaidEvent]:
        """Check if raid is from a Twitch partner (requires API lookup)"""

        def check(_event: RaidEvent) -> bool:
            # Placeholder - would check Twitch API for partner status
            return True

        return cls.condition(check, "from_partner")


class SubscriptionEvent(EventModel):
    """Twitch subscription event"""

    event_type: ClassVar[str] = "twitch.subscription"

    user: str
    channel: str
    tier: str  # "1000", "2000", "3000"
    months: int
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)

    @classmethod
    def tier_level(cls, tier: str) -> Condition[SubscriptionEvent]:
        """Check subscription tier"""

        def check(event: SubscriptionEvent) -> bool:
            return event.tier == tier

        return cls.condition(check, f"tier_level({tier})")

    @classmethod
    def min_months(cls, months: int) -> Condition[SubscriptionEvent]:
        """Check minimum months subscribed"""

        def check(event: SubscriptionEvent) -> bool:
            return event.months >= months

        return cls.condition(check, f"min_months({months})")


class DonationEvent(EventModel):
    """Twitch donation/bits event"""

    event_type: ClassVar[str] = "twitch.donation"

    user: str
    amount: float
    currency: str = "USD"
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)

    @classmethod
    def min_amount(cls, amount: float) -> Condition[DonationEvent]:
        """Check minimum donation amount"""

        def check(event: DonationEvent) -> bool:
            return event.amount >= amount

        return cls.condition(check, f"min_amount({amount})")

    @classmethod
    def currency_type(cls, currency: str) -> Condition[DonationEvent]:
        """Check donation currency"""

        def check(event: DonationEvent) -> bool:
            return event.currency.upper() == currency.upper()

        return cls.condition(check, f"currency_type({currency})")
