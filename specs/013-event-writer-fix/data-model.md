# Data Model: EventWriter Synchronous Mode

**Feature**: 013-event-writer-fix
**Date**: 2025-10-08

## Overview

This feature adds synchronous write mode to EventWriter. The data model changes are minimal - we introduce an enum to represent write modes and preserve all existing Event and EventWriter state structures.

## Entities

### 1. WriteMode (NEW)

**Type**: Enum (str-based)
**Purpose**: Explicitly represent the operational mode of the EventWriter
**Location**: `src/llm_sim/infrastructure/events/writer.py`

**Values**:
```python
class WriteMode(str, Enum):
    """Event writer operation modes."""
    ASYNC = "async"  # Queue-based, background writer task
    SYNC = "sync"    # Immediate, blocking writes with fsync
```

**Validation Rules**:
- Must be one of: "async" or "sync"
- String-based enum for JSON serialization compatibility
- Immutable after EventWriter initialization

**Relationships**:
- Used by EventWriter constructor parameter
- Determines dispatch logic in EventWriter.emit()

**State Transitions**: None (immutable after init)

---

### 2. EventWriter (MODIFIED)

**Type**: Class
**Purpose**: Write events to disk in async or sync mode
**Location**: `src/llm_sim/infrastructure/events/writer.py`

**New Fields**:
```python
mode: WriteMode  # Operational mode (async or sync)
```

**Existing Fields** (unchanged):
```python
output_dir: Path              # Directory for event files
simulation_id: str            # Simulation identifier
verbosity: VerbosityLevel     # Event filtering level
max_queue_size: int           # Queue limit (async mode only)
max_file_size: int            # File rotation threshold
queue: asyncio.Queue[Event]   # Event queue (async mode only)
writer_task: Optional[asyncio.Task]  # Background task (async mode only)
running: bool                 # Writer status (async mode only)
dropped_count: int            # Dropped events count (async mode)
current_file: Path            # Active event file path
current_size: int             # Current file size in bytes
```

**Validation Rules**:
- `mode` must be valid WriteMode enum value
- `output_dir` must be writable directory
- `max_file_size` must be > 0
- `max_queue_size` must be > 0 (ignored in sync mode)

**State Transitions**:
```
# Async mode lifecycle
INIT → start() → RUNNING → stop() → STOPPED

# Sync mode lifecycle
INIT → (ready immediately, no start/stop needed)
```

**Behavioral Changes by Mode**:
| Method | Async Mode | Sync Mode |
|--------|-----------|-----------|
| `__init__()` | Initialize queue, task=None | Initialize queue (unused), task=None |
| `start()` | Create background task | No-op (log skip) |
| `stop()` | Drain queue, cancel task | No-op (log skip) |
| `emit()` | Queue event (non-blocking) | Write immediately (blocking) |
| File writes | Via `_write_event()` (async) | Via `_write_event_sync()` (sync) |
| File rotation | Via `_rotate_file()` (async) | Via `_rotate_file_sync()` (sync) |

---

### 3. Event (UNCHANGED)

**Type**: Pydantic BaseModel
**Purpose**: Represent a simulation event
**Location**: `src/llm_sim/models/event.py`

**Fields** (reference only, no changes):
```python
event_id: str              # Unique event identifier
event_type: str            # Event classification
simulation_id: str         # Associated simulation run
timestamp: datetime        # Event occurrence time
data: dict[str, Any]       # Event-specific payload
```

**Validation Rules** (unchanged):
- `event_id` must be unique
- `event_type` must match VerbosityLevel classification
- `timestamp` must be valid datetime
- `data` must be JSON-serializable

**Serialization**:
- JSONL format: `event.model_dump_json() + "\n"`
- Same serialization for both async and sync modes

---

### 4. VerbosityLevel (UNCHANGED)

**Type**: Enum
**Purpose**: Control event filtering granularity
**Location**: `src/llm_sim/infrastructure/events/config.py`

**Values** (reference only):
```python
class VerbosityLevel(str, Enum):
    MINIMAL = "minimal"  # Critical events only
    ACTION = "action"    # User actions + critical
    FULL = "full"        # All events
```

**Usage**: Same across both async and sync modes

---

## Data Flow

### Sync Mode Event Flow
```
1. Simulation emits event
   ↓
2. EventWriter.emit(event) called
   ↓
3. Check verbosity filter (shared logic)
   ↓
4. if mode == SYNC:
   ↓
5. _write_event_sync(event)
   ↓
6. Check if rotation needed (current_size >= max_file_size)
   ↓
7. If rotation: _rotate_file_sync()
   ↓
8. Open file in append mode
   ↓
9. Write event line
   ↓
10. flush() → fsync()
   ↓
11. Update current_size
   ↓
12. Return to simulation (blocking complete)
```

### Async Mode Event Flow (UNCHANGED)
```
1. Simulation emits event
   ↓
2. EventWriter.emit(event) called
   ↓
3. Check verbosity filter
   ↓
4. if mode == ASYNC:
   ↓
5. queue.put_nowait(event)
   ↓
6. Return immediately (non-blocking)
   ↓
[Background task _write_loop runs separately]
7. Dequeue event
   ↓
8. _write_event(event) - async
   ↓
9. Check rotation → _rotate_file() if needed - async
   ↓
10. aiofiles write + flush
   ↓
11. Update current_size
```

---

## File System Schema

### Event File Format (UNCHANGED)

**Primary File**: `{output_dir}/events.jsonl`
**Rotated Files**: `{output_dir}/events_{timestamp}.jsonl`

**Format**: JSON Lines (JSONL)
- One JSON object per line
- UTF-8 encoding
- Newline delimited

**Example**:
```jsonl
{"event_id":"evt_001","event_type":"simulation_starting","simulation_id":"sim_123","timestamp":"2025-10-08T10:00:00Z","data":{"config":"spatial_trade_network.yaml"}}
{"event_id":"evt_002","event_type":"turn_started","simulation_id":"sim_123","timestamp":"2025-10-08T10:00:01Z","data":{"turn":1}}
{"event_id":"evt_003","event_type":"agent_action","simulation_id":"sim_123","timestamp":"2025-10-08T10:00:02Z","data":{"agent":"trader_1","action":"buy"}}
```

**Rotation Naming**:
```
events.jsonl                           # Active file (current writes)
events_2025-10-08_10-30-45-123456.jsonl  # Rotated (timestamp with microseconds)
events_2025-10-08_11-15-22-987654.jsonl  # Another rotation
```

**File Size Limit**: 500MB (configurable via `max_file_size`)

---

## Schema Validation

### Type Constraints

```python
# WriteMode
assert mode in ["async", "sync"]

# EventWriter init parameters
assert isinstance(output_dir, Path)
assert isinstance(simulation_id, str)
assert isinstance(verbosity, VerbosityLevel)
assert max_queue_size > 0
assert max_file_size > 0
assert isinstance(mode, WriteMode)

# Event serialization
event_json: str = event.model_dump_json()
assert event_json.endswith('\n') is False  # Newline added separately
assert json.loads(event_json)  # Valid JSON
```

### Invariants

1. **Mode Immutability**: `writer.mode` cannot change after initialization
2. **File Atomicity**: Only one file is "current" at any time (events.jsonl)
3. **Size Tracking**: `current_size` accurately reflects events.jsonl size in bytes
4. **Rotation Uniqueness**: Timestamp includes microseconds to prevent filename collisions
5. **Sync Guarantee** (sync mode): After `emit()` returns, event is on disk (fsynced)
6. **Queue Isolation** (sync mode): Queue exists but is never used

---

## Migration Impact

### Backward Compatibility

✅ **No breaking changes**:
- Default mode is ASYNC (existing behavior preserved)
- Event model unchanged (serialization identical)
- File format unchanged (JSONL)
- Public API unchanged (`emit()`, `start()`, `stop()`)
- Existing async tests pass without modification

### New Code Patterns

```python
# Old pattern (still works)
writer = EventWriter(
    output_dir=Path("output"),
    simulation_id="sim_123",
)

# New pattern (sync mode)
from llm_sim.infrastructure.events.writer import EventWriter, WriteMode

writer = EventWriter(
    output_dir=Path("output"),
    simulation_id="sim_123",
    mode=WriteMode.SYNC,  # Explicit sync mode
)
```

---

## Summary

**New Entities**: 1 (WriteMode enum)
**Modified Entities**: 1 (EventWriter - added mode field + 2 methods)
**Unchanged Entities**: 2 (Event, VerbosityLevel)

**Data Model Complexity**: Minimal
- Single new enum (2 values)
- Single new field on existing class
- No new relationships or dependencies
- No schema version changes needed
- File format remains identical

**Key Design Properties**:
1. Mode is explicit (no auto-detection)
2. Both modes share Event model (no format divergence)
3. Sync mode uses subset of EventWriter state (queue unused)
4. File rotation logic separated by mode (different I/O patterns)
5. Backward compatible (async default)

**Next**: Generate contracts and tests in Phase 1
