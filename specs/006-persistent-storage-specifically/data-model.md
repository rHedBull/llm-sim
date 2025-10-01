# Data Model: Persistent Simulation State Storage

**Feature**: 006-persistent-storage-specifically
**Date**: 2025-10-01

## Entity Relationship Diagram

```
┌─────────────────┐
│  RunMetadata    │
├─────────────────┤
│ run_id          │◄─────┐
│ simulation_name │      │
│ num_agents      │      │ 1:N
│ start_time      │      │
│ end_time        │      │
│ checkpoint_int  │      │
│ config_snapshot │      │
└─────────────────┘      │
         │               │
         │ 1:1           │
         │               │
         ▼               │
┌─────────────────┐      │
│SimulationResults│      │
├─────────────────┤      │
│ run_metadata    │      │
│ final_state     │      │
│ checkpoints     │      │
│ summary_stats   │      │
└─────────────────┘      │
                         │
┌─────────────────┐      │
│  Checkpoint     │      │
├─────────────────┤      │
│ turn            │◄─────┘
│ checkpoint_type │
│ state           │
│ timestamp       │
└─────────────────┘
         │
         │ contains
         ▼
┌─────────────────┐
│SimulationState  │  (Existing Model)
├─────────────────┤
│ turn            │
│ agents          │
│ global_state    │
└─────────────────┘
```

## Entities

### 1. RunMetadata

**Purpose**: Identifies and tracks a single simulation run execution

**Pydantic Model**:
```python
from datetime import datetime
from pydantic import BaseModel, Field

class RunMetadata(BaseModel):
    """Metadata for a simulation run."""

    run_id: str = Field(
        ...,
        description="Unique identifier: {name}_{N}agents_{YYYYMMDD}_{HHMMSS}_{seq}",
        examples=["EconomicTest_3agents_20251001_143022_01"]
    )

    simulation_name: str = Field(
        ...,
        description="Name from simulation config"
    )

    num_agents: int = Field(
        ...,
        gt=0,
        description="Number of agents in simulation"
    )

    start_time: datetime = Field(
        ...,
        description="Simulation start timestamp (UTC)"
    )

    end_time: datetime | None = Field(
        default=None,
        description="Simulation end timestamp (null if incomplete/crashed)"
    )

    checkpoint_interval: int | None = Field(
        default=None,
        gt=0,
        description="Checkpoint save interval (null = disabled, only last/final saved)"
    )

    config_snapshot: dict = Field(
        ...,
        description="Complete simulation config for validation on resume"
    )
```

**Relationships**:
- Has many `Checkpoint` (0..N)
- Has one `SimulationResults` (0..1, only if completed)

**Lifecycle**:
1. Created at simulation start (before turn 0)
2. `end_time` set when simulation completes/terminates
3. Persisted in memory during run, saved to result.json at end

**Validation Rules**:
- `run_id` must match format regex: `^[a-zA-Z0-9_-]+_\d+agents_\d{8}_\d{6}_\d{2}$`
- `num_agents` must match config agent count
- `checkpoint_interval` must be positive if provided
- `start_time` must be before `end_time` (if end_time set)

---

### 2. Checkpoint

**Purpose**: Represents a saved simulation state at a specific turn

**Pydantic Model**:
```python
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class Checkpoint(BaseModel):
    """A saved simulation state checkpoint."""

    turn: int = Field(
        ...,
        ge=0,
        description="Turn number when checkpoint was saved"
    )

    checkpoint_type: Literal["interval", "last", "final"] = Field(
        ...,
        description="Type of checkpoint: interval (every N), last (most recent), final (simulation end)"
    )

    state: SimulationState = Field(
        ...,
        description="Complete simulation state snapshot at this turn"
    )

    timestamp: datetime = Field(
        ...,
        description="When checkpoint was created (UTC)"
    )
```

**Checkpoint Types**:
- **interval**: Saved at regular intervals (e.g., turn 10, 20, 30 for interval=10)
- **last**: Most recent turn (always saved, overwrites previous "last")
- **final**: Last turn when simulation completes (immutable)

**Relationships**:
- Belongs to one `RunMetadata` (via filesystem structure)
- Contains one `SimulationState`

**Lifecycle**:
1. Created when `should_save_checkpoint()` returns True
2. Serialized to `output/{run_id}/checkpoints/turn_{N}.json`
3. Immutable once saved (no updates)
4. "last" checkpoint overwrites previous on each turn

**Validation Rules**:
- `turn` must match `state.turn`
- `checkpoint_type` determines file naming: `turn_{turn}.json` or `last.json`
- `timestamp` must be >= simulation start_time

**File Mapping**:
- `interval`: `checkpoints/turn_{turn}.json`
- `last`: `checkpoints/last.json` (overwrites each turn)
- `final`: `checkpoints/turn_{turn}.json` (same as interval, immutable)

---

### 3. SimulationResults

**Purpose**: Summary output and final results for a completed run

**Pydantic Model**:
```python
from pydantic import BaseModel, Field

class SimulationResults(BaseModel):
    """Final results and metadata for a completed simulation run."""

    run_metadata: RunMetadata = Field(
        ...,
        description="Run identification and configuration"
    )

    final_state: SimulationState = Field(
        ...,
        description="Simulation state at the last turn"
    )

    checkpoints: list[int] = Field(
        ...,
        description="List of turn numbers where checkpoints were saved"
    )

    summary_stats: dict = Field(
        default_factory=dict,
        description="Summary statistics (implementation-defined, e.g., agent outcomes, termination reason)"
    )
```

**Relationships**:
- Belongs to one `RunMetadata`
- Contains one `SimulationState` (final)
- References many `Checkpoint` (by turn number)

**Lifecycle**:
1. Created when simulation completes (max turns or termination)
2. Serialized once to `output/{run_id}/result.json`
3. Immutable after creation

**Validation Rules**:
- `final_state.turn` must match last executed turn
- `checkpoints` list must be sorted ascending
- `run_metadata.end_time` must be set
- All `checkpoints` turns must exist as files

**Summary Stats** (deferred clarification - initial proposal):
```python
summary_stats = {
    "total_turns": 100,
    "termination_reason": "max_turns",  # or "termination_condition"
    "agent_final_states": {
        "Agent_A": {"economic_strength": 1500},
        "Agent_B": {"economic_strength": 1200}
    },
    "elapsed_time_seconds": 45.3
}
```

---

### 4. SimulationState (Existing)

**Purpose**: Complete snapshot of simulation at a single turn

**Existing Model** (no changes needed):
```python
from pydantic import BaseModel

class SimulationState(BaseModel):
    """Current simulation state."""

    turn: int
    agents: dict[str, AgentState]  # agent_name -> AgentState
    global_state: GlobalState
```

**Verification Needed**:
- ✅ All fields JSON-serializable via Pydantic
- ✅ `AgentState` and `GlobalState` are Pydantic models
- ✅ No circular references
- ✅ Handles nested structures (agents dict)

**Relationships**:
- Contained in `Checkpoint`
- Contained in `SimulationResults` (as final_state)

**Lifecycle**: Created each turn by engine, passed to orchestrator

---

## State Transitions

### RunMetadata State Machine
```
[NEW] → [RUNNING] → [COMPLETED]
                  → [INTERRUPTED] (end_time = null)
```

### Checkpoint Types Over Time
```
Turn 0: (start)
Turn 1: last.json
Turn 5: turn_5.json (interval), last.json
Turn 10: turn_10.json (interval), last.json
Turn 15: turn_15.json (final), last.json
(end)
```

---

## Filesystem Schema

### Directory Structure
```
output/
└── EconomicTest_3agents_20251001_143022_01/
    ├── checkpoints/
    │   ├── last.json           # Most recent (overwritten each turn)
    │   ├── turn_5.json         # Interval checkpoint
    │   ├── turn_10.json        # Interval checkpoint
    │   └── turn_15.json        # Final checkpoint
    └── result.json             # SimulationResults
```

### File Formats

**Checkpoint File** (`turn_N.json` or `last.json`):
```json
{
  "turn": 5,
  "checkpoint_type": "interval",
  "state": {
    "turn": 5,
    "agents": {
      "Agent_A": {"name": "Agent_A", "economic_strength": 1050.0},
      "Agent_B": {"name": "Agent_B", "economic_strength": 980.0}
    },
    "global_state": {
      "interest_rate": 0.05,
      "total_economic_value": 2030.0
    }
  },
  "timestamp": "2025-10-01T14:30:22.123456Z"
}
```

**Result File** (`result.json`):
```json
{
  "run_metadata": {
    "run_id": "EconomicTest_3agents_20251001_143022_01",
    "simulation_name": "EconomicTest",
    "num_agents": 2,
    "start_time": "2025-10-01T14:30:15.000000Z",
    "end_time": "2025-10-01T14:30:35.000000Z",
    "checkpoint_interval": 5,
    "config_snapshot": { /* full config */ }
  },
  "final_state": { /* SimulationState at turn 15 */ },
  "checkpoints": [5, 10, 15],
  "summary_stats": {
    "total_turns": 15,
    "termination_reason": "max_turns",
    "elapsed_time_seconds": 20.0
  }
}
```

---

## Data Integrity Rules

### Save Operations
1. **Atomicity**: All file writes use temp + rename pattern
2. **Validation**: Pydantic validates all data before serialization
3. **Fail-fast**: Any save error halts simulation immediately
4. **Immutability**: Checkpoint files never modified after creation (except `last.json` overwrite)

### Load Operations
1. **Validation**: Pydantic validates JSON schema on load
2. **Config match**: Loaded state's config_snapshot compared to current config
3. **Turn verification**: Loaded turn number matches requested turn
4. **Error handling**: Missing/corrupted files raise CheckpointLoadError

### Consistency Guarantees
- All checkpoints for a run use same `run_id`
- `result.json` `checkpoints` list matches actual checkpoint files
- `final_state.turn` matches last checkpoint turn
- No gaps in interval checkpoints (except where simulation crashed)

---

## Migration Strategy

**Phase 1** (this implementation):
- No version field in schema
- Incompatible changes break old checkpoints (documented)

**Future** (deferred clarification):
- Add `schema_version` field to all models
- Implement migration functions for version N → N+1
- Support loading previous version with automatic migration

---

## Performance Considerations

### Serialization
- **Pydantic v2**: Fast C-based serialization (~10x faster than v1)
- **Expected**: <100ms for 100-agent state at 1000 turns
- **Bottleneck**: File I/O, not serialization

### Storage
- **Typical checkpoint**: 10-100 KB (100 agents)
- **100 turns with interval=10**: ~1 MB total
- **Compression**: Not implemented (future enhancement if needed)

### Load Performance
- **Expected**: <50ms to load and validate checkpoint
- **Bottleneck**: JSON parsing, file read

---

## Testing Requirements

From this data model, contract tests must verify:

1. **RunMetadata**:
   - Serialization round-trip (save/load preserves data)
   - Validation (positive num_agents, valid run_id format)
   - start_time < end_time enforcement

2. **Checkpoint**:
   - turn matches state.turn
   - checkpoint_type enum validation
   - Serialization with nested SimulationState

3. **SimulationResults**:
   - checkpoints list sorted
   - References valid checkpoint files
   - summary_stats schema (flexible dict)

4. **SimulationState**:
   - Already tested (existing model)
   - Verify JSON compatibility with all field types

---

## Dependencies

**Data Model → Code**:
- `src/llm_sim/models/checkpoint.py`: NEW file with RunMetadata, Checkpoint, SimulationResults
- `src/llm_sim/models/state.py`: EXISTING, verify JSON serialization
- `src/llm_sim/models/config.py`: EXTEND with checkpoint_interval field

**No database** - purely file-based storage
**No caching** - read from disk on demand
**No indexing** - filesystem directory listing sufficient
