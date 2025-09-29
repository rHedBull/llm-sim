"""Action models for the simulation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel


class ActionType(str, Enum):
    """Types of actions agents can take."""

    GROW = "grow"
    MAINTAIN = "maintain"
    DECLINE = "decline"


class Action(BaseModel):
    """Action taken by an agent."""

    agent_name: str
    action_type: ActionType
    parameters: Dict[str, Any]
    validated: bool = False
    validation_timestamp: Optional[datetime] = None

    def mark_validated(self) -> "Action":
        """Mark this action as validated.

        Returns:
            New Action instance marked as validated
        """
        return self.model_copy(update={"validated": True, "validation_timestamp": datetime.now()})
