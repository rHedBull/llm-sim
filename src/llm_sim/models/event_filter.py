"""Event filter model for querying events."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class EventFilter(BaseModel):
    """Criteria for filtering events via API queries."""

    start_timestamp: Optional[datetime] = None
    end_timestamp: Optional[datetime] = None
    event_types: Optional[List[str]] = None
    agent_ids: Optional[List[str]] = None
    turn_start: Optional[int] = Field(None, ge=0)
    turn_end: Optional[int] = Field(None, ge=0)
    limit: int = Field(1000, ge=1, le=10000)
    offset: int = Field(0, ge=0)

    def matches(self, event: dict) -> bool:
        """Check if an event matches this filter.

        Args:
            event: Event dictionary to test

        Returns:
            True if event matches all filter criteria
        """
        # Timestamp range
        if self.start_timestamp:
            event_time = datetime.fromisoformat(event["timestamp"])
            if event_time < self.start_timestamp:
                return False

        if self.end_timestamp:
            event_time = datetime.fromisoformat(event["timestamp"])
            if event_time > self.end_timestamp:
                return False

        # Event types
        if self.event_types:
            if event["event_type"] not in self.event_types:
                return False

        # Agent IDs
        if self.agent_ids:
            if event.get("agent_id") not in self.agent_ids:
                return False

        # Turn range
        if self.turn_start is not None:
            if event["turn_number"] < self.turn_start:
                return False

        if self.turn_end is not None:
            if event["turn_number"] > self.turn_end:
                return False

        return True
