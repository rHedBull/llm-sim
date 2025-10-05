# Data Model: Event Stream Activity Logging

**Date**: 2025-10-04
**Feature**: Event Stream Activity Logging
**Branch**: 010-event-stream-the

## Entity Relationship Overview

```
SimulationRun (1) ──── (N) Event
     │
     └─ EventStream (collection of events in JSONL files)

Event (base)
  ├─ MilestoneEvent (turn boundaries, phases)
  ├─ DecisionEvent (agent strategic choices)
  ├─ ActionEvent (agent actions)
  ├─ StateEvent (variable transitions)
  ├─ DetailEvent (calculations)
  └─ SystemEvent (LLM calls, errors)

Event ──(caused_by)──> Event (causality graph)
EventFilter ───(filters)───> Event (query criteria)
```

## Core Entities

### 1. Event (Base Model)

**Purpose**: Common schema for all simulation events

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| event_id | str | Yes | ULID identifier | 26-char Base32 |
| timestamp | datetime | Yes | ISO 8601 UTC | Microsecond precision |
| turn_number | int | Yes | Simulation turn | >= 0 |
| event_type | str | Yes | Event category | Enum: MILESTONE\|DECISION\|ACTION\|STATE\|DETAIL\|SYSTEM |
| simulation_id | str | Yes | Run ID | Matches output directory name |
| agent_id | str | No | Agent identifier | Present only for agent events |
| caused_by | List[str] | No | Causality sources | Array of event_ids |
| description | str | No | Human-readable summary | Max 500 chars |
| details | dict | No | Structured payload | JSON-serializable |

**Invariants**:
- `event_id` MUST be globally unique across all simulations
- `timestamp` MUST use UTC timezone
- `event_type` MUST match subclass type
- `agent_id` MUST be absent for SystemEvent, MilestoneEvent
- `caused_by` event_ids MUST reference existing events (eventual consistency)

**JSON Representation**:
```json
{
  "event_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
  "timestamp": "2025-10-04T14:23:45.123456+00:00",
  "turn_number": 42,
  "event_type": "DECISION",
  "simulation_id": "my-sim-20251004-142345-3agents",
  "agent_id": "agent_alice",
  "caused_by": ["01ARZ3NDEKTSV4RRFFQ69G5FAU"],
  "description": "Agent alice changed investment strategy",
  "details": {"decision_type": "strategy_change", "old_value": "conservative", "new_value": "aggressive"}
}
```

### 2. MilestoneEvent (Event)

**Purpose**: Capture turn boundaries and simulation phase transitions

**Additional Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| milestone_type | str | Yes | Milestone category | Enum: turn_start\|turn_end\|phase_transition\|simulation_start\|simulation_end |

**Example**:
```json
{
  "event_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
  "timestamp": "2025-10-04T14:23:45.000000+00:00",
  "turn_number": 1,
  "event_type": "MILESTONE",
  "simulation_id": "my-sim-20251004-142345-3agents",
  "agent_id": null,
  "description": "Turn 1 started",
  "details": {"milestone_type": "turn_start"}
}
```

### 3. DecisionEvent (Event)

**Purpose**: Capture agent strategic decisions and policy changes

**Additional Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| decision_type | str | Yes | Decision category | Free-form string |
| old_value | Any | No | Previous value | JSON-serializable |
| new_value | Any | No | New value | JSON-serializable |

**Example**:
```json
{
  "event_id": "01ARZ3NDEKTSV4RRFFQ69G5FAX",
  "timestamp": "2025-10-04T14:23:46.100000+00:00",
  "turn_number": 1,
  "event_type": "DECISION",
  "simulation_id": "my-sim-20251004-142345-3agents",
  "agent_id": "agent_bob",
  "description": "Bob changed resource allocation",
  "details": {
    "decision_type": "resource_allocation",
    "old_value": {"food": 0.6, "military": 0.4},
    "new_value": {"food": 0.5, "military": 0.5}
  }
}
```

### 4. ActionEvent (Event)

**Purpose**: Capture individual agent actions and transactions

**Additional Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| action_type | str | Yes | Action category | Free-form string |
| action_payload | dict | Yes | Action-specific data | JSON-serializable |

**Example**:
```json
{
  "event_id": "01ARZ3NDEKTSV4RRFFQ69G5FAY",
  "timestamp": "2025-10-04T14:23:47.200000+00:00",
  "turn_number": 1,
  "event_type": "ACTION",
  "simulation_id": "my-sim-20251004-142345-3agents",
  "agent_id": "agent_alice",
  "description": "Alice initiated trade with Bob",
  "details": {
    "action_type": "trade",
    "action_payload": {
      "partner": "agent_bob",
      "offer": {"gold": 100},
      "request": {"food": 50}
    }
  }
}
```

### 5. StateEvent (Event)

**Purpose**: Capture state variable transitions

**Additional Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| variable_name | str | Yes | State variable name | Matches config schema |
| old_value | Any | Yes | Previous value | JSON-serializable |
| new_value | Any | Yes | New value | JSON-serializable |
| scope | str | No | Variable scope | Enum: global\|agent |

**Example**:
```json
{
  "event_id": "01ARZ3NDEKTSV4RRFFQ69G5FAZ",
  "timestamp": "2025-10-04T14:23:48.300000+00:00",
  "turn_number": 1,
  "event_type": "STATE",
  "simulation_id": "my-sim-20251004-142345-3agents",
  "agent_id": "agent_alice",
  "description": "Alice's wealth increased",
  "details": {
    "variable_name": "wealth",
    "old_value": 1000,
    "new_value": 1150,
    "scope": "agent"
  }
}
```

### 6. DetailEvent (Event)

**Purpose**: Capture granular calculations and intermediate values

**Additional Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| calculation_type | str | Yes | Calculation category | Free-form string |
| intermediate_values | dict | Yes | Calculation steps | JSON-serializable |

**Example**:
```json
{
  "event_id": "01ARZ3NDEKTSV4RRFFQ69G5FB0",
  "timestamp": "2025-10-04T14:23:48.350000+00:00",
  "turn_number": 1,
  "event_type": "DETAIL",
  "simulation_id": "my-sim-20251004-142345-3agents",
  "agent_id": null,
  "description": "Interest calculation applied",
  "details": {
    "calculation_type": "interest",
    "intermediate_values": {
      "principal": 1000,
      "rate": 0.05,
      "interest": 50,
      "new_total": 1050
    }
  }
}
```

### 7. SystemEvent (Event)

**Purpose**: Capture system-level events (LLM calls, validation errors, retries)

**Additional Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| error_type | str | No | Error category | Free-form string |
| status | str | Yes | Event status | Enum: success\|failure\|retry\|warning |
| retry_count | int | No | Retry attempt number | >= 0 |

**Example**:
```json
{
  "event_id": "01ARZ3NDEKTSV4RRFFQ69G5FB1",
  "timestamp": "2025-10-04T14:23:49.400000+00:00",
  "turn_number": 1,
  "event_type": "SYSTEM",
  "simulation_id": "my-sim-20251004-142345-3agents",
  "agent_id": null,
  "description": "LLM API call failed, retrying",
  "details": {
    "error_type": "connection_timeout",
    "status": "retry",
    "retry_count": 1,
    "llm_model": "llama3",
    "timeout_ms": 5000
  }
}
```

### 8. EventFilter

**Purpose**: Query criteria for filtering events via API

**Fields**:
| Field | Type | Required | Default | Description | Validation |
|-------|------|----------|---------|-------------|------------|
| start_timestamp | datetime | No | None | Filter start time | ISO 8601 |
| end_timestamp | datetime | No | None | Filter end time | ISO 8601 |
| event_types | List[str] | No | None | Filter by event types | Subset of enum |
| agent_ids | List[str] | No | None | Filter by agents | Agent IDs |
| turn_start | int | No | None | Filter turn range start | >= 0 |
| turn_end | int | No | None | Filter turn range end | >= turn_start |
| limit | int | No | 1000 | Max results | 1-10000 |
| offset | int | No | 0 | Pagination offset | >= 0 |

**Example Query**:
```json
{
  "event_types": ["DECISION", "ACTION"],
  "agent_ids": ["agent_alice"],
  "turn_start": 5,
  "turn_end": 10,
  "limit": 100,
  "offset": 0
}
```

## Relationships

### Event Causality Graph

**Relationship**: Event ──(caused_by)──> Event (many-to-many)

**Semantics**:
- Each event MAY reference 0-N parent events via `caused_by` array
- Causality is directional: child event references parent event_ids
- Graph MAY be cyclic (rare but possible in complex feedback loops)
- Missing parent event_ids are tolerated (eventual consistency)

**Traversal**:
```
Given event E:
- Upstream causality: Events referenced by E.caused_by (recursively)
- Downstream causality: Events that reference E.event_id in their caused_by array
```

### Simulation-Event Relationship

**Relationship**: SimulationRun ──(has)──> EventStream (one-to-many files)

**File Organization**:
```
output/
└── {simulation_id}/
    ├── events.jsonl                           # Primary event file
    ├── events_2025-10-04_14-25-00.jsonl      # Rotated file 1
    ├── events_2025-10-04_14-30-00.jsonl      # Rotated file 2
    └── checkpoints/                           # Existing checkpoint files
```

**Aggregation Logic**:
- Events MUST be aggregated across all `events*.jsonl` files in simulation directory
- Sort order: timestamp (primary), event_id (secondary)
- API server MUST discover all matching files via glob pattern

## Validation Rules

### Schema Validation

1. **Required Fields**: All base Event fields marked "Required: Yes" MUST be present
2. **Type Safety**: Field types MUST match Pydantic schema
3. **Enum Validation**: Enum fields MUST use only allowed values
4. **Causality Integrity**: `caused_by` event_ids SHOULD exist (soft requirement, not enforced)

### Business Logic Validation

1. **Agent ID Consistency**:
   - SystemEvent MUST NOT have agent_id
   - MilestoneEvent (global milestones) MUST NOT have agent_id
   - DecisionEvent, ActionEvent MUST have agent_id
   - StateEvent SHOULD have agent_id for agent-scoped variables

2. **Timestamp Ordering**:
   - Events within same turn SHOULD have increasing timestamps
   - Events across turns MUST have non-decreasing turn_numbers

3. **Verbosity Level Filtering**:
   - MILESTONE: Only MilestoneEvent
   - DECISION: MilestoneEvent + DecisionEvent
   - ACTION: DECISION events + ActionEvent
   - STATE: ACTION events + StateEvent
   - DETAIL: STATE events + DetailEvent + SystemEvent

## State Transitions

**Event Lifecycle**:
```
Created (in-memory Event object)
    ↓
Queued (EventWriter async queue)
    ↓
Written (JSONL file append)
    ↓
Discoverable (API server finds event)
    ↓
Deleted (simulation output directory removed)
```

**File Rotation Lifecycle**:
```
events.jsonl (active file, size < 500MB)
    ↓ [size >= 500MB]
Rotate: Rename to events_{timestamp}.jsonl
    ↓
Create new events.jsonl (continue writing)
```

## Performance Characteristics

**Event Size**:
- Minimal event (MILESTONE): ~200 bytes
- Average event (ACTION): ~500 bytes
- Large event (DETAIL with calculations): ~2KB
- **Estimate**: ~500 bytes average per event

**Storage Scaling**:
- 10k events: ~5MB (single file)
- 100k events: ~50MB (requires 0 rotations)
- 1M events: ~500MB (requires 1-2 rotations)

**Query Performance** (API):
- Single file scan: 10k events/sec (SSD)
- Multi-file aggregation: 5k events/sec across 10 files
- Filter application: 50% overhead (regex + timestamp parsing)
- **Expected API latency**: <100ms for 1000-event response

---

**Phase 1 Data Model Status**: ✅ COMPLETE
