"""Event builder helper functions for constructing typed events."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ulid import ULID

from llm_sim.models.event import (
    ActionEvent,
    DecisionEvent,
    DetailEvent,
    MilestoneEvent,
    StateEvent,
    SystemEvent,
)


def create_milestone_event(
    simulation_id: str,
    turn_number: int,
    milestone_type: str,
    description: Optional[str] = None,
    caused_by: Optional[List[str]] = None,
) -> MilestoneEvent:
    """Create a milestone event.

    Args:
        simulation_id: Simulation run identifier
        turn_number: Current turn number
        milestone_type: Type of milestone (turn_start, turn_end, etc.)
        description: Optional human-readable description
        caused_by: Optional list of causal event IDs

    Returns:
        MilestoneEvent instance
    """
    return MilestoneEvent(
        event_id=str(ULID()),
        timestamp=datetime.now(timezone.utc),
        turn_number=turn_number,
        simulation_id=simulation_id,
        description=description,
        caused_by=caused_by,
        details={"milestone_type": milestone_type},
    )


def create_decision_event(
    simulation_id: str,
    turn_number: int,
    agent_id: str,
    decision_type: str,
    old_value: Any = None,
    new_value: Any = None,
    description: Optional[str] = None,
    caused_by: Optional[List[str]] = None,
) -> DecisionEvent:
    """Create a decision event.

    Args:
        simulation_id: Simulation run identifier
        turn_number: Current turn number
        agent_id: Agent making the decision
        decision_type: Type of decision
        old_value: Previous value
        new_value: New value
        description: Optional human-readable description
        caused_by: Optional list of causal event IDs

    Returns:
        DecisionEvent instance
    """
    details: Dict[str, Any] = {"decision_type": decision_type}
    if old_value is not None:
        details["old_value"] = old_value
    if new_value is not None:
        details["new_value"] = new_value

    return DecisionEvent(
        event_id=str(ULID()),
        timestamp=datetime.now(timezone.utc),
        turn_number=turn_number,
        simulation_id=simulation_id,
        agent_id=agent_id,
        description=description,
        caused_by=caused_by,
        details=details,
    )


def create_action_event(
    simulation_id: str,
    turn_number: int,
    agent_id: str,
    action_type: str,
    action_payload: Dict[str, Any],
    description: Optional[str] = None,
    caused_by: Optional[List[str]] = None,
) -> ActionEvent:
    """Create an action event.

    Args:
        simulation_id: Simulation run identifier
        turn_number: Current turn number
        agent_id: Agent performing action
        action_type: Type of action
        action_payload: Action-specific data
        description: Optional human-readable description
        caused_by: Optional list of causal event IDs

    Returns:
        ActionEvent instance
    """
    return ActionEvent(
        event_id=str(ULID()),
        timestamp=datetime.now(timezone.utc),
        turn_number=turn_number,
        simulation_id=simulation_id,
        agent_id=agent_id,
        description=description,
        caused_by=caused_by,
        details={"action_type": action_type, "action_payload": action_payload},
    )


def create_state_event(
    simulation_id: str,
    turn_number: int,
    variable_name: str,
    old_value: Any,
    new_value: Any,
    agent_id: Optional[str] = None,
    scope: str = "global",
    description: Optional[str] = None,
    caused_by: Optional[List[str]] = None,
) -> StateEvent:
    """Create a state change event.

    Args:
        simulation_id: Simulation run identifier
        turn_number: Current turn number
        variable_name: Name of state variable
        old_value: Previous value
        new_value: New value
        agent_id: Optional agent ID for agent-scoped variables
        scope: Variable scope (global or agent)
        description: Optional human-readable description
        caused_by: Optional list of causal event IDs

    Returns:
        StateEvent instance
    """
    return StateEvent(
        event_id=str(ULID()),
        timestamp=datetime.now(timezone.utc),
        turn_number=turn_number,
        simulation_id=simulation_id,
        agent_id=agent_id,
        description=description,
        caused_by=caused_by,
        details={
            "variable_name": variable_name,
            "old_value": old_value,
            "new_value": new_value,
            "scope": scope,
        },
    )


def create_detail_event(
    simulation_id: str,
    turn_number: int,
    calculation_type: str,
    intermediate_values: Dict[str, Any],
    description: Optional[str] = None,
    caused_by: Optional[List[str]] = None,
) -> DetailEvent:
    """Create a detail event for calculations.

    Args:
        simulation_id: Simulation run identifier
        turn_number: Current turn number
        calculation_type: Type of calculation
        intermediate_values: Calculation intermediate values
        description: Optional human-readable description
        caused_by: Optional list of causal event IDs

    Returns:
        DetailEvent instance
    """
    return DetailEvent(
        event_id=str(ULID()),
        timestamp=datetime.now(timezone.utc),
        turn_number=turn_number,
        simulation_id=simulation_id,
        description=description,
        caused_by=caused_by,
        details={
            "calculation_type": calculation_type,
            "intermediate_values": intermediate_values,
        },
    )


def create_system_event(
    simulation_id: str,
    turn_number: int,
    status: str,
    error_type: Optional[str] = None,
    retry_count: Optional[int] = None,
    description: Optional[str] = None,
    caused_by: Optional[List[str]] = None,
    **extra_details: Any,
) -> SystemEvent:
    """Create a system event.

    Args:
        simulation_id: Simulation run identifier
        turn_number: Current turn number
        status: Event status (success, failure, retry, warning)
        error_type: Optional error type
        retry_count: Optional retry attempt count
        description: Optional human-readable description
        caused_by: Optional list of causal event IDs
        **extra_details: Additional details to include

    Returns:
        SystemEvent instance
    """
    details: Dict[str, Any] = {"status": status}
    if error_type:
        details["error_type"] = error_type
    if retry_count is not None:
        details["retry_count"] = retry_count
    details.update(extra_details)

    return SystemEvent(
        event_id=str(ULID()),
        timestamp=datetime.now(timezone.utc),
        turn_number=turn_number,
        simulation_id=simulation_id,
        description=description,
        caused_by=caused_by,
        details=details,
    )
