# Research: Event Stream Activity Logging

**Date**: 2025-10-04
**Feature**: Event Stream Activity Logging
**Branch**: 010-event-stream-the

## Research Questions & Findings

### 1. JSONL Best Practices for Event Streams

**Decision**: Use atomic write-then-rename pattern with line buffering

**Rationale**:
- JSONL (JSON Lines) ensures each event is a complete, parseable JSON object on a single line
- Atomic writes prevent partial line corruption during crashes
- Line-buffered writes (flush after each event) ensure immediate persistence without excessive syscalls
- Write to temp file, then atomic rename ensures reader never sees partial writes

**Alternatives Considered**:
- **Direct append**: Rejected due to corruption risk on crashes
- **Write-ahead log**: Rejected as over-engineered for this use case
- **Batch buffering**: Rejected due to event loss risk under crashes

**Implementation Approach**:
```python
# Atomic JSONL append pattern
with open(temp_path, 'a') as f:
    f.write(json.dumps(event_dict) + '\n')
    f.flush()  # Force write to disk
os.replace(temp_path, final_path)  # Atomic on POSIX
```

**File Rotation Strategy**:
- Size-based rotation at 500MB (from clarifications)
- Timestamped filenames: `events_YYYY-MM-DD_HH-MM-SS.jsonl`
- Check file size after each write; rotate when threshold exceeded
- New file inherits atomic write pattern

### 2. FastAPI Event Streaming Patterns

**Decision**: Use generator-based streaming with pagination offsets

**Rationale**:
- FastAPI supports async generators for streaming large datasets
- Pagination via limit/offset allows clients to control memory footprint
- Lazy file reading reduces API server memory usage
- OpenAPI schema generation works natively with Pydantic query params

**Alternatives Considered**:
- **Full file load**: Rejected due to memory constraints with 100k+ events
- **Cursor-based pagination**: Rejected as overkill for file-based storage
- **WebSocket streaming**: Rejected as REST is sufficient for historical event queries

**Implementation Approach**:
```python
from fastapi import Query
from typing import List, Optional

@app.get("/simulations/{sim_id}/events")
async def get_events(
    sim_id: str,
    limit: int = Query(1000, le=10000),
    offset: int = Query(0, ge=0),
    event_types: Optional[List[str]] = Query(None)
):
    # Stream events from rotated files with filtering
    events = await event_service.get_filtered_events(sim_id, filter)
    return {"events": events[offset:offset+limit], "total": len(events)}
```

**OpenAPI Schema**:
- Auto-generated from Pydantic models
- Query parameters map to EventFilter fields
- Response schemas defined via Pydantic response models

### 3. Python Async Event Writing

**Decision**: Use asyncio.Queue with background writer task

**Rationale**:
- Non-blocking event emission: main simulation thread never waits on I/O
- Background worker drains queue and writes to JSONL asynchronously
- Bounded queue (size=10000) prevents unbounded memory growth
- Queue full triggers event drop (per clarifications: speed > observability)

**Alternatives Considered**:
- **Synchronous writes**: Rejected due to I/O blocking simulation turns
- **Thread-based writer**: Rejected due to GIL contention and complexity
- **Unbounded queue**: Rejected due to memory exhaustion risk

**Implementation Approach**:
```python
import asyncio
from asyncio import Queue

class EventWriter:
    def __init__(self, max_queue_size: int = 10000):
        self.queue: Queue = Queue(maxsize=max_queue_size)
        self.writer_task: Optional[asyncio.Task] = None

    async def start(self):
        self.writer_task = asyncio.create_task(self._write_loop())

    async def emit(self, event: Event):
        try:
            self.queue.put_nowait(event)  # Non-blocking
        except asyncio.QueueFull:
            logger.warning("Event queue full, dropping event", event_id=event.event_id)

    async def _write_loop(self):
        while True:
            event = await self.queue.get()
            await self._write_event(event)  # Atomic JSONL write
```

**Graceful Shutdown**:
- Flush pending events on shutdown signal
- Wait for queue drain with timeout (10 seconds max)
- Log count of dropped events if timeout exceeded

### 4. Event ID Generation

**Decision**: Use ULID (Universally Unique Lexicographically Sortable Identifier)

**Rationale**:
- Sortable by timestamp (128-bit: 48-bit timestamp + 80-bit random)
- Collision-resistant (80 bits of randomness)
- URL-safe Base32 encoding (26 characters)
- Monotonic within same millisecond (important for causality tracking)
- Python library available: `python-ulid`

**Alternatives Considered**:
- **UUID v4**: Rejected due to lack of sortability
- **UUID v7**: Considered but ULID has better adoption and libraries
- **Incremental IDs**: Rejected due to coordination overhead across rotated files

**Implementation**:
```python
from ulid import ULID

event_id = str(ULID())  # Example: 01ARZ3NDEKTSV4RRFFQ69G5FAV
```

**Causality Tracking**:
- Each event stores `caused_by: List[str]` with parent event ULIDs
- Allows multi-parent causality (e.g., decision caused by multiple state changes)
- API `/causality/{event_id}` endpoint traverses graph recursively

### 5. Timestamp Precision

**Decision**: ISO 8601 with microsecond precision using datetime.isoformat()

**Rationale**:
- Python `datetime` supports microsecond precision natively
- ISO 8601 format universally parseable and sortable as strings
- Wall clock (not monotonic) chosen for human-readable timestamps
- Acceptable sub-millisecond precision for event ordering

**Alternatives Considered**:
- **Nanosecond precision**: Rejected as overkill and not supported by JSON
- **Unix timestamps**: Rejected due to poor human readability
- **Monotonic clock**: Rejected as wall clock time more useful for debugging

**Implementation**:
```python
from datetime import datetime, timezone

timestamp = datetime.now(timezone.utc).isoformat()  # 2025-10-04T14:23:45.123456+00:00
```

**Event Ordering**:
- Primary sort: timestamp (microsecond precision)
- Secondary sort: ULID (for same-microsecond events)
- Monotonic guarantee within single simulation process

## Technology Stack Summary

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Event ID | ULID (python-ulid) | Sortable, collision-resistant, URL-safe |
| Timestamp | ISO 8601 (datetime) | Universal format, microsecond precision |
| Storage | JSONL files | Simple, human-readable, no DB overhead |
| File I/O | asyncio + aiofiles | Non-blocking writes, graceful degradation |
| Queue | asyncio.Queue | Bounded, async-native, drop-on-full |
| API Server | FastAPI + uvicorn | Async, OpenAPI, Pydantic integration |
| Rotation | Size-based (500MB) | Prevents unbounded file growth |

## Dependencies to Add

Via `uv add`:
```bash
uv add python-ulid      # Event ID generation
uv add aiofiles         # Async file I/O
uv add fastapi          # API server
uv add uvicorn[standard]  # ASGI server for FastAPI
```

## Open Questions Resolved

All clarifications from spec.md resolved:
- ✅ Default verbosity: ACTION level
- ✅ File rotation: 500MB with timestamps
- ✅ Retention policy: Delete with simulation output directory
- ✅ Backlog handling: Drop events, log warning
- ✅ Causality representation: Array of source event_ids on each event
- ✅ Required metadata: event_id, timestamp, turn_number, event_type, simulation_id, agent_id (optional), caused_by (optional)
- ✅ Payload schema: Hybrid (common fields + type-specific fields)

## Performance Considerations

**Expected Overhead**:
- Event construction: ~100 microseconds (Pydantic model instantiation)
- Queue enqueue: ~1 microsecond (non-blocking)
- Async write: ~500 microseconds per event (amortized, background thread)
- **Total simulation overhead**: <1ms per event (meets performance goal)

**Scalability**:
- 1000 events/sec sustained throughput (meets goal)
- 100k events per simulation run (manageable with 500MB rotation)
- API pagination handles millions of events across rotated files

**Memory Footprint**:
- Queue: ~10MB (10k events × ~1KB each)
- API server: <50MB for event aggregation across 10 files

---

**Phase 0 Status**: ✅ COMPLETE (All unknowns resolved, no NEEDS CLARIFICATION)
