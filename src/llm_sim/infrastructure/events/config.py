"""Event streaming configuration and verbosity levels."""

from enum import Enum
from typing import Set


class VerbosityLevel(str, Enum):
    """Event verbosity levels for filtering event streams.

    Levels are hierarchical - each level includes all events from
    lower levels plus its own event types.
    """

    MILESTONE = "MILESTONE"  # Turn boundaries, phase transitions
    DECISION = "DECISION"    # MILESTONE + agent decisions
    ACTION = "ACTION"        # DECISION + agent actions
    STATE = "STATE"          # ACTION + state variable changes
    DETAIL = "DETAIL"        # STATE + granular calculations, system events


# Verbosity level hierarchy - what event types each level captures
VERBOSITY_EVENT_TYPES: dict[VerbosityLevel, Set[str]] = {
    VerbosityLevel.MILESTONE: {"MILESTONE", "SYSTEM"},  # SYSTEM includes turn/simulation lifecycle events
    VerbosityLevel.DECISION: {"MILESTONE", "SYSTEM", "DECISION"},
    VerbosityLevel.ACTION: {"MILESTONE", "SYSTEM", "DECISION", "ACTION"},
    VerbosityLevel.STATE: {"MILESTONE", "SYSTEM", "DECISION", "ACTION", "ENV"},
    VerbosityLevel.DETAIL: {"MILESTONE", "SYSTEM", "DECISION", "ACTION", "ENV", "DETAIL"},
}


def should_log_event(event_type: str, verbosity: VerbosityLevel) -> bool:
    """Check if an event type should be logged at given verbosity level.

    Args:
        event_type: The event type to check
        verbosity: Current verbosity level

    Returns:
        True if event should be logged at this verbosity level
    """
    allowed_types = VERBOSITY_EVENT_TYPES.get(verbosity, set())
    return event_type in allowed_types
