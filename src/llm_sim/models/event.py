"""Event models for simulation event streaming."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from ulid import ULID


class Event(BaseModel):
    """Base model for all simulation events.

    All events share common metadata fields. Subclasses add
    type-specific fields in the details dictionary.
    """

    event_id: str = Field(default_factory=lambda: str(ULID()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    turn_number: int = Field(ge=0)
    event_type: Literal["MILESTONE", "DECISION", "ACTION", "ENV", "DETAIL", "SYSTEM"]
    simulation_id: str
    agent_id: Optional[str] = None
    caused_by: Optional[List[str]] = None
    description: Optional[str] = Field(None, max_length=500)
    details: Optional[Dict[str, Any]] = None

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MilestoneEvent(Event):
    """Event for turn boundaries and simulation phase transitions."""

    event_type: Literal["MILESTONE"] = "MILESTONE"

    def __init__(self, **data: Any) -> None:
        """Initialize milestone event with proper details structure."""
        super().__init__(**data)
        if self.details is None:
            self.details = {}

    @property
    def milestone_type(self) -> Optional[str]:
        """Get milestone type from details."""
        return self.details.get("milestone_type") if self.details else None


class DecisionEvent(Event):
    """Event for agent strategic decisions and policy changes."""

    event_type: Literal["DECISION"] = "DECISION"

    def __init__(self, **data: Any) -> None:
        """Initialize decision event, requiring agent_id."""
        if "agent_id" not in data or data["agent_id"] is None:
            raise ValueError("DecisionEvent requires agent_id")
        super().__init__(**data)
        if self.details is None:
            self.details = {}

    @property
    def decision_type(self) -> Optional[str]:
        """Get decision type from details."""
        return self.details.get("decision_type") if self.details else None

    @property
    def old_value(self) -> Any:
        """Get old value from details."""
        return self.details.get("old_value") if self.details else None

    @property
    def new_value(self) -> Any:
        """Get new value from details."""
        return self.details.get("new_value") if self.details else None


class ActionEvent(Event):
    """Event for individual agent actions and transactions."""

    event_type: Literal["ACTION"] = "ACTION"

    def __init__(self, **data: Any) -> None:
        """Initialize action event, requiring agent_id."""
        if "agent_id" not in data or data["agent_id"] is None:
            raise ValueError("ActionEvent requires agent_id")
        super().__init__(**data)
        if self.details is None:
            self.details = {}

    @property
    def action_type(self) -> Optional[str]:
        """Get action type from details."""
        return self.details.get("action_type") if self.details else None

    @property
    def action_payload(self) -> Optional[Dict[str, Any]]:
        """Get action payload from details."""
        return self.details.get("action_payload") if self.details else None


class EnvEvent(Event):
    """Event for environment/state variable transitions."""

    event_type: Literal["ENV"] = "ENV"

    def __init__(self, **data: Any) -> None:
        """Initialize state event."""
        super().__init__(**data)
        if self.details is None:
            self.details = {}

    @property
    def variable_name(self) -> Optional[str]:
        """Get variable name from details."""
        return self.details.get("variable_name") if self.details else None

    @property
    def old_value(self) -> Any:
        """Get old value from details."""
        return self.details.get("old_value") if self.details else None

    @property
    def new_value(self) -> Any:
        """Get new value from details."""
        return self.details.get("new_value") if self.details else None

    @property
    def scope(self) -> Optional[str]:
        """Get scope from details."""
        return self.details.get("scope") if self.details else None


class DetailEvent(Event):
    """Event for granular calculations and intermediate values."""

    event_type: Literal["DETAIL"] = "DETAIL"

    def __init__(self, **data: Any) -> None:
        """Initialize detail event."""
        super().__init__(**data)
        if self.details is None:
            self.details = {}

    @property
    def calculation_type(self) -> Optional[str]:
        """Get calculation type from details."""
        return self.details.get("calculation_type") if self.details else None

    @property
    def intermediate_values(self) -> Optional[Dict[str, Any]]:
        """Get intermediate values from details."""
        return self.details.get("intermediate_values") if self.details else None


class SystemEvent(Event):
    """Event for simulation system lifecycle events (simulation/turn start/end)."""

    event_type: Literal["SYSTEM"] = "SYSTEM"

    def __init__(self, **data: Any) -> None:
        """Initialize system event."""
        super().__init__(**data)
        if self.details is None:
            self.details = {}

    @property
    def system_event_type(self) -> Optional[str]:
        """Get system event type from details."""
        return self.details.get("system_event_type") if self.details else None

    @property
    def status(self) -> Optional[str]:
        """Get status from details."""
        return self.details.get("status") if self.details else None


# Backward compatibility alias
StateEvent = EnvEvent
