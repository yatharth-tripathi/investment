"""Time utilities for market simulation."""

from datetime import datetime, timezone

def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc) #UTC Universal Time Coordinated