# Event Streaming Feature

The event streaming feature provides fine-grained observability into simulation execution by capturing every significant action, decision, state change, and system event.

## Overview

**Purpose**: Capture simulation activity at configurable verbosity levels between checkpoint snapshots.

**Key Capabilities**:
- ✅ Non-blocking async event capture
- ✅ Automatic file rotation at 500MB
- ✅ 5 hierarchical verbosity levels
- ✅ REST API for querying events
- ✅ Causality chain analysis
- ✅ Multi-file aggregation

## Quick Start

### 1. Run Simulation with Event Streaming

```python
from pathlib import Path
from llm_sim.orchestrator import SimulationOrchestrator
from llm_sim.models.config import SimulationConfig
from llm_sim.infrastructure.events import VerbosityLevel

# Load your configuration
config = SimulationConfig.from_yaml("simulation.yaml")

# Create orchestrator with event streaming
orchestrator = SimulationOrchestrator(
    config=config,
    output_root=Path("output"),
    event_verbosity=VerbosityLevel.ACTION  # Default: ACTION
)

# Run simulation - events are automatically captured
results = orchestrator.run()

# Events written to: output/{run_id}/events.jsonl
```

### 2. Query Events Programmatically

```python
from pathlib import Path
from llm_sim.api.services.event_service import EventService
from llm_sim.models.event_filter import EventFilter

# Initialize service
service = EventService(Path("output"))

# List all simulations
simulations = service.list_simulations()

# Get filtered events
filter = EventFilter(
    event_types=["DECISION", "ACTION"],
    agent_ids=["agent_alice"],
    turn_start=5,
    turn_end=10,
    limit=100
)
result = service.get_filtered_events("simulation-id", filter)

# Analyze causality
chain = service.get_causality_chain("simulation-id", "event-id")
```

### 3. Use the REST API

Start the API server:

```bash
python -m llm_sim.api.server
# Server starts at http://localhost:8000
# OpenAPI docs at http://localhost:8000/docs
```

Query events:

```bash
# List simulations
curl http://localhost:8000/simulations

# Get all events
curl "http://localhost:8000/simulations/{sim_id}/events?limit=100"

# Filter by event type
curl "http://localhost:8000/simulations/{sim_id}/events?event_types=MILESTONE&event_types=DECISION"

# Filter by agent
curl "http://localhost:8000/simulations/{sim_id}/events?agent_ids=agent_alice"

# Filter by turn range
curl "http://localhost:8000/simulations/{sim_id}/events?turn_start=5&turn_end=10"

# Get causality chain
curl "http://localhost:8000/simulations/{sim_id}/causality/{event_id}?depth=5"
```

## Verbosity Levels

Events are captured based on the configured verbosity level. Each level includes all events from lower levels:

| Level | Events Captured | Use Case |
|-------|----------------|----------|
| **MILESTONE** | Turn boundaries, simulation start/end | Minimal logging |
| **DECISION** | MILESTONE + agent decisions, policy changes | Strategic overview |
| **ACTION** ⭐ | DECISION + agent actions, transactions | **Default - balanced** |
| **STATE** | ACTION + state variable changes | Detailed state tracking |
| **DETAIL** | STATE + calculations, system events | Full observability |

**Default**: `ACTION` level provides balanced observability without excessive detail.

### Event Type Hierarchy

```
MILESTONE  ─┐
            ├─ DECISION  ─┐
                          ├─ ACTION  ─┐
                                      ├─ STATE  ─┐
                                                  ├─ DETAIL
                                                  └─ SYSTEM
```

## Event Types

### MILESTONE Events
**Captures**: Turn boundaries, simulation phases
**Fields**: `milestone_type` (turn_start, turn_end, simulation_start, simulation_end, phase_transition)

Example:
```json
{
  "event_id": "01K6RFJ1A2B3C4D5E6F7G8H9J0",
  "timestamp": "2025-10-04T20:00:00+00:00",
  "turn_number": 1,
  "event_type": "MILESTONE",
  "simulation_id": "sim-001",
  "description": "Turn 1 started",
  "details": {"milestone_type": "turn_start"}
}
```

### DECISION Events
**Captures**: Agent strategic decisions, policy changes
**Fields**: `decision_type`, `old_value`, `new_value`
**Requires**: `agent_id`

### ACTION Events
**Captures**: Agent actions, transactions
**Fields**: `action_type`, `action_payload`
**Requires**: `agent_id`

### STATE Events
**Captures**: State variable transitions
**Fields**: `variable_name`, `old_value`, `new_value`, `scope` (global/agent)

### DETAIL Events
**Captures**: Calculations, intermediate values
**Fields**: `calculation_type`, `intermediate_values`

### SYSTEM Events
**Captures**: LLM calls, errors, retries
**Fields**: `error_type`, `status`, `retry_count`

## Event Schema

All events share common metadata:

```python
{
  "event_id": str,        # ULID (sortable, unique)
  "timestamp": str,       # ISO 8601 with microseconds
  "turn_number": int,     # Simulation turn
  "event_type": str,      # MILESTONE|DECISION|ACTION|STATE|DETAIL|SYSTEM
  "simulation_id": str,   # Simulation run ID
  "agent_id": str?,       # Optional: present for agent events
  "caused_by": [str]?,    # Optional: causal event IDs
  "description": str?,    # Optional: human-readable summary
  "details": dict?        # Optional: type-specific data
}
```

## File Storage

### File Organization

```
output/
└── {simulation_id}/
    ├── events.jsonl                        # Primary event file
    ├── events_2025-10-04_14-25-00.jsonl   # Rotated file 1
    ├── events_2025-10-04_14-30-00.jsonl   # Rotated file 2
    └── checkpoints/                        # Checkpoint files
```

### File Rotation

- **Trigger**: Automatic rotation when file reaches 500MB
- **Naming**: `events_YYYY-MM-DD_HH-MM-SS.jsonl`
- **Format**: JSONL (one event per line, valid JSON)
- **API Handling**: Automatically aggregates events across all rotated files

## API Endpoints

### GET /simulations
List all simulations with event streams.

**Response**:
```json
{
  "simulations": [
    {
      "id": "sim-001",
      "name": "economic-model",
      "start_time": "2025-10-04T20:00:00+00:00",
      "event_count": 1523
    }
  ]
}
```

### GET /simulations/{sim_id}/events
Get filtered events with pagination.

**Query Parameters**:
- `start_timestamp`: ISO 8601 timestamp
- `end_timestamp`: ISO 8601 timestamp
- `event_types`: Array of event types
- `agent_ids`: Array of agent IDs
- `turn_start`: Minimum turn number
- `turn_end`: Maximum turn number
- `limit`: Max results (default 1000, max 10000)
- `offset`: Pagination offset (default 0)

**Response**:
```json
{
  "events": [...],
  "total": 1523,
  "has_more": true
}
```

### GET /simulations/{sim_id}/events/{event_id}
Get a single event by ID.

**Response**: Single event object

### GET /simulations/{sim_id}/causality/{event_id}
Get causality chain for an event.

**Query Parameters**:
- `depth`: Max traversal depth (default 5, max 20)

**Response**:
```json
{
  "event_id": "...",
  "event": {...},
  "upstream": [...],   # Parent events (causes)
  "downstream": [...]  # Child events (effects)
}
```

## Performance Characteristics

### Event Writer

- **Throughput**: 1000+ events/sec sustained
- **Latency**: <1ms overhead per event (non-blocking)
- **Queue Size**: 10,000 events (bounded)
- **Backlog Strategy**: Drop events with warning (simulation speed > observability)

### API Server

- **Single File Scan**: 10,000 events/sec (SSD)
- **Multi-File Aggregation**: 5,000 events/sec across 10 files
- **Filter Overhead**: ~50% (timestamp parsing + regex)
- **Typical Latency**: <100ms for 1000-event response

### Storage Scaling

| Events | Size | Files | Notes |
|--------|------|-------|-------|
| 10k | ~5MB | 1 | Single file |
| 100k | ~50MB | 1 | Single file |
| 1M | ~500MB | 2-3 | Rotation triggered |
| 10M | ~5GB | 10-20 | Multi-file aggregation |

## Causality Tracking

Events can reference parent events via the `caused_by` array:

```python
# Decision caused by turn start
create_decision_event(
    ...
    caused_by=["turn_start_event_id"]
)

# Action caused by multiple decisions
create_action_event(
    ...
    caused_by=["decision_1_id", "decision_2_id"]
)
```

### Causality Graph

```
turn_start (MILESTONE)
    ↓
decision_1 (DECISION)  ──┐
                         ├─→ action_1 (ACTION)
decision_2 (DECISION)  ──┘      ↓
                            state_change (STATE)
```

The API's `/causality` endpoint traverses this graph to show:
- **Upstream**: All events that caused this event (recursive)
- **Downstream**: All events caused by this event

## Integration Examples

### Custom Event Emission

```python
from llm_sim.infrastructure.events import create_system_event

# Emit custom system event
event = create_system_event(
    simulation_id=sim_id,
    turn_number=current_turn,
    status="warning",
    error_type="timeout",
    retry_count=2,
    description="LLM API timed out, retrying",
    llm_model="llama3",
    timeout_ms=5000
)
orchestrator.event_writer.emit(event)
```

### Event-Driven Analysis

```python
# Analyze agent behavior patterns
filter = EventFilter(
    event_types=["DECISION"],
    agent_ids=["agent_alice"]
)
decisions = service.get_filtered_events(sim_id, filter)

# Extract decision patterns
patterns = {}
for event in decisions['events']:
    decision_type = event['details']['decision_type']
    patterns[decision_type] = patterns.get(decision_type, 0) + 1

print(f"Agent alice decision patterns: {patterns}")
```

## Troubleshooting

### No events.jsonl file created
- Check: EventWriter was started (`await writer.start()`)
- Check: EventWriter was stopped with flush (`await writer.stop()`)
- Check: Output directory permissions

### Events missing from API
- Check: Event files exist in `output/{sim_id}/`
- Check: Simulation ID matches directory name exactly
- Check: API server `output_root` matches simulation output directory

### File not rotating at 500MB
- Check: EventWriter rotation logic executes after each write
- Check: File size calculation includes all rotated files
- Check: Write permissions for creating timestamped files

## Next Steps

- **UI Integration**: Use API to build timeline visualizations
- **Real-time Monitoring**: WebSocket streaming for live event updates
- **Event Replay**: Reconstruct simulation state from event stream
- **Analytics**: Aggregate events for behavior pattern analysis
- **Export**: Convert JSONL to other formats (CSV, Parquet, etc.)

## Demo

Run the comprehensive demo:

```bash
python examples/event_stream_demo.py
```

This demonstrates:
1. Event writer with async I/O
2. Event service with filtering
3. Causality chain analysis
4. Verbosity level behavior
