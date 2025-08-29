"""
Lightweight runtime types for Pantainos - no Pydantic overhead
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Event:
    """Simple event dataclass used internally at runtime."""

    type: str
    data: dict[str, Any]
    source: str = "unknown"
    timestamp: float = field(default_factory=lambda: time.time())

    # Back-compat helpers (minimal)
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    # Pydantic-like compat to reduce breakage during migration
    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
