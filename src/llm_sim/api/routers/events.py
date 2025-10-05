"""Event API endpoints."""

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Request

from llm_sim.api.services.event_service import EventService
from llm_sim.models.event_filter import EventFilter

router = APIRouter()


def get_event_service(request: Request) -> EventService:
    """Get EventService from app state.

    Args:
        request: FastAPI request

    Returns:
        EventService instance
    """
    output_root = getattr(request.app.state, "output_root", Path("output"))
    return EventService(output_root)


@router.get("/simulations")
async def list_simulations(request: Request):
    """List all simulations with event streams.

    Returns:
        List of simulation summaries
    """
    service = get_event_service(request)
    simulations = service.list_simulations()
    return {"simulations": simulations}


@router.get("/simulations/{simulation_id}/events")
async def get_events(
    request: Request,
    simulation_id: str,
    start_timestamp: Optional[str] = Query(None),
    end_timestamp: Optional[str] = Query(None),
    event_types: Optional[List[str]] = Query(None),
    agent_ids: Optional[List[str]] = Query(None),
    turn_start: Optional[int] = Query(None, ge=0),
    turn_end: Optional[int] = Query(None, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    """Get filtered events for a simulation.

    Args:
        simulation_id: Simulation identifier
        start_timestamp: Filter events after this timestamp (ISO 8601)
        end_timestamp: Filter events before this timestamp (ISO 8601)
        event_types: Filter by event types
        agent_ids: Filter by agent identifiers
        turn_start: Filter events from this turn onwards
        turn_end: Filter events up to this turn
        limit: Maximum number of events to return
        offset: Number of events to skip (pagination)

    Returns:
        Filtered events with pagination info
    """
    from datetime import datetime

    # Build filter
    event_filter = EventFilter(
        start_timestamp=datetime.fromisoformat(start_timestamp) if start_timestamp else None,
        end_timestamp=datetime.fromisoformat(end_timestamp) if end_timestamp else None,
        event_types=event_types,
        agent_ids=agent_ids,
        turn_start=turn_start,
        turn_end=turn_end,
        limit=limit,
        offset=offset,
    )

    service = get_event_service(request)
    result = service.get_filtered_events(simulation_id, event_filter)

    return result


@router.get("/simulations/{simulation_id}/events/{event_id}")
async def get_event_by_id(
    request: Request,
    simulation_id: str,
    event_id: str,
):
    """Get a single event by ID.

    Args:
        simulation_id: Simulation identifier
        event_id: Event identifier

    Returns:
        Event details

    Raises:
        HTTPException: If event not found
    """
    service = get_event_service(request)
    event = service.get_event_by_id(simulation_id, event_id)

    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"Event {event_id} not found in simulation {simulation_id}",
        )

    return event


@router.get("/simulations/{simulation_id}/causality/{event_id}")
async def get_causality_chain(
    request: Request,
    simulation_id: str,
    event_id: str,
    depth: int = Query(5, ge=1, le=20),
):
    """Get causality chain for an event.

    Args:
        simulation_id: Simulation identifier
        event_id: Event identifier
        depth: Maximum depth to traverse (default 5, max 20)

    Returns:
        Causality chain with upstream and downstream events

    Raises:
        HTTPException: If event not found
    """
    service = get_event_service(request)
    result = service.get_causality_chain(simulation_id, event_id, depth)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Event {event_id} not found in simulation {simulation_id}",
        )

    return result
