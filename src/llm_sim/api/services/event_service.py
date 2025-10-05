"""Event service for discovering and aggregating event files."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from llm_sim.models.event_filter import EventFilter


class EventService:
    """Service for discovering and querying simulation events."""

    def __init__(self, output_root: Path):
        """Initialize event service.

        Args:
            output_root: Root directory containing simulation outputs
        """
        self.output_root = Path(output_root)

    def list_simulations(self) -> List[Dict[str, any]]:
        """List all simulations with event streams.

        Returns:
            List of simulation summaries
        """
        simulations = []

        # Find all simulation directories
        if not self.output_root.exists():
            return simulations

        for sim_dir in self.output_root.iterdir():
            if not sim_dir.is_dir():
                continue

            # Check if events file exists
            event_files = list(sim_dir.glob("events*.jsonl"))
            if not event_files:
                continue

            # Count total events
            event_count = 0
            for event_file in event_files:
                try:
                    with open(event_file) as f:
                        event_count += sum(1 for _ in f)
                except IOError:
                    continue

            # Try to get start time from first event
            start_time = None
            first_file = sorted(event_files)[0]
            try:
                with open(first_file) as f:
                    first_line = f.readline()
                    if first_line:
                        first_event = json.loads(first_line)
                        start_time = first_event.get("timestamp")
            except (IOError, json.JSONDecodeError):
                pass

            simulations.append({
                "id": sim_dir.name,
                "name": sim_dir.name.split("-")[0] if "-" in sim_dir.name else sim_dir.name,
                "start_time": start_time,
                "event_count": event_count,
            })

        return simulations

    def get_filtered_events(
        self, simulation_id: str, event_filter: EventFilter
    ) -> Dict[str, any]:
        """Get filtered events for a simulation.

        Args:
            simulation_id: Simulation identifier
            event_filter: Filter criteria

        Returns:
            Dictionary with events, total count, and has_more flag
        """
        sim_dir = self.output_root / simulation_id
        if not sim_dir.exists():
            return {"events": [], "total": 0, "has_more": False}

        # Discover all event files
        event_files = sorted(sim_dir.glob("events*.jsonl"))
        if not event_files:
            return {"events": [], "total": 0, "has_more": False}

        # Aggregate and filter events
        all_events = []
        for event_file in event_files:
            try:
                with open(event_file) as f:
                    for line in f:
                        try:
                            event = json.loads(line)
                            if event_filter.matches(event):
                                all_events.append(event)
                        except json.JSONDecodeError:
                            continue
            except IOError:
                continue

        # Sort by timestamp (primary) and event_id (secondary)
        all_events.sort(
            key=lambda e: (
                datetime.fromisoformat(e["timestamp"]),
                e["event_id"]
            )
        )

        # Apply pagination
        total = len(all_events)
        start = event_filter.offset
        end = start + event_filter.limit
        paginated_events = all_events[start:end]
        has_more = end < total

        return {
            "events": paginated_events,
            "total": total,
            "has_more": has_more,
        }

    def get_event_by_id(
        self, simulation_id: str, event_id: str
    ) -> Optional[Dict[str, any]]:
        """Get a single event by ID.

        Args:
            simulation_id: Simulation identifier
            event_id: Event identifier

        Returns:
            Event dict or None if not found
        """
        sim_dir = self.output_root / simulation_id
        if not sim_dir.exists():
            return None

        # Search all event files
        event_files = sorted(sim_dir.glob("events*.jsonl"))
        for event_file in event_files:
            try:
                with open(event_file) as f:
                    for line in f:
                        try:
                            event = json.loads(line)
                            if event.get("event_id") == event_id:
                                return event
                        except json.JSONDecodeError:
                            continue
            except IOError:
                continue

        return None

    def get_causality_chain(
        self, simulation_id: str, event_id: str, depth: int = 5
    ) -> Optional[Dict[str, any]]:
        """Get causality chain for an event.

        Args:
            simulation_id: Simulation identifier
            event_id: Event identifier
            depth: Maximum depth to traverse

        Returns:
            Causality chain with upstream and downstream events
        """
        # Get the target event
        event = self.get_event_by_id(simulation_id, event_id)
        if not event:
            return None

        # Build event lookup for efficient causality traversal
        sim_dir = self.output_root / simulation_id
        event_files = sorted(sim_dir.glob("events*.jsonl"))

        event_lookup = {}
        causality_map = {}  # event_id -> list of events that reference it

        for event_file in event_files:
            try:
                with open(event_file) as f:
                    for line in f:
                        try:
                            e = json.loads(line)
                            eid = e.get("event_id")
                            event_lookup[eid] = e

                            # Build reverse causality map
                            caused_by = e.get("caused_by", [])
                            if caused_by:
                                for parent_id in caused_by:
                                    if parent_id not in causality_map:
                                        causality_map[parent_id] = []
                                    causality_map[parent_id].append(e)
                        except json.JSONDecodeError:
                            continue
            except IOError:
                continue

        # Get upstream events (parents)
        upstream = []
        visited = set()

        def get_upstream(eid: str, current_depth: int):
            if current_depth >= depth or eid in visited:
                return
            visited.add(eid)

            e = event_lookup.get(eid)
            if e:
                caused_by = e.get("caused_by") or []
                for parent_id in caused_by:
                    parent = event_lookup.get(parent_id)
                    if parent and parent not in upstream:
                        upstream.append(parent)
                        get_upstream(parent_id, current_depth + 1)

        get_upstream(event_id, 0)

        # Get downstream events (children)
        downstream = causality_map.get(event_id, [])

        return {
            "event_id": event_id,
            "event": event,
            "upstream": upstream,
            "downstream": downstream,
        }
