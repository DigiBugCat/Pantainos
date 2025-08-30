"""
Lightweight runtime types for Pantainos - no Pydantic overhead
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Event:
    """Simple event dataclass used internally at runtime."""

    type: str
    data: dict[str, Any]
    source: str = "unknown"
    timestamp: float = field(default_factory=lambda: time.time())
