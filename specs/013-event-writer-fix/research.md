# Research: EventWriter Synchronous Mode Implementation

**Feature**: 013-event-writer-fix
**Date**: 2025-10-08
**Status**: Complete

## Research Overview

This document consolidates research findings for adding synchronous write mode to the EventWriter class.

## 1. Root Cause Analysis

### Problem Context
**Decision**: The async event writer's background task never executes because `_run_turn_sync()` blocks the event loop.

**Rationale**:
- Current EventWriter uses `asyncio.Queue` and background task `_write_loop()`
- The orchestrator runs simulation turns in `_run_turn_sync()` which is a synchronous blocking function
- When the event loop is blocked, `_write_loop()` never gets scheduled
- Events queue up but are never flushed to disk
- Result: Empty events.jsonl files despite events being emitted

**Evidence**:
- Examined `src/llm_sim/infrastructure/events/writer.py:135-152` (_write_loop implementation)
- Analyzed orchestrator execution pattern in `src/llm_sim/orchestrator.py`
- Confirmed `_run_turn_sync()` blocks the event loop during turn processing

**Alternatives Considered**:
1. ❌ **Make orchestrator fully async**: Would require rewriting entire simulation execution model
2. ❌ **Use threading for writer**: Introduces thread safety complexity, violates KISS
3. ✅ **Add sync mode to EventWriter**: Minimal change, preserves async for future use

## 2. Synchronous File I/O Best Practices

### Decision: Use standard library `open()` with explicit `fsync()` for durability

**Rationale**:
- Python's built-in `open()` is sufficient for synchronous file writes
- `f.flush()` ensures Python buffers are written to OS
- `os.fsync(f.fileno())` ensures OS buffers are flushed to disk
- This pattern guarantees durability (events survive crashes)

**Performance Characteristics**:
```python
# Sync write with fsync (guarantees durability)
with open(file, 'a') as f:
    f.write(event_line)
    f.flush()            # Flush Python buffers
    os.fsync(f.fileno()) # Flush OS buffers to disk
# ~1ms per write on SSD, ~10ms on HDD
```

**Alternatives Considered**:
1. **Buffered writes without fsync**: Faster (~0.1ms) but events lost on crash
2. **Memory-mapped files**: Complex, no reliability benefit for JSONL append pattern
3. ✅ **Open + flush + fsync**: Simple, reliable, acceptable performance for scale

**Best Practices Applied**:
- Append mode ('a') for JSONL files
- UTF-8 encoding explicit
- File handles closed immediately (context manager)
- Error handling for IOError

## 3. Dual-Mode Architecture Pattern

### Decision: Single class with mode parameter, branch in `emit()`

**Rationale**:
- Keeps interface unified (`emit()` same for both modes)
- Mode selection explicit at initialization
- Minimal code changes (if/else branch in emit)
- Easy to test both modes in same test suite

**Architecture**:
```
EventWriter
├── __init__(mode: WriteMode)
├── emit(event) → if mode == SYNC: _write_sync() else: queue.put()
├── start() → no-op if SYNC
├── stop() → no-op if SYNC
├── _write_event_sync(event) → NEW
└── _rotate_file_sync() → NEW
```

**Alternatives Considered**:
1. **Separate SyncEventWriter class**: Violates DRY (duplicates verbosity logic, rotation config)
2. **Strategy pattern**: Over-engineered for 2 modes, violates KISS
3. **Abstract base class**: Unnecessary abstraction, violates KISS
4. ✅ **Mode parameter in single class**: Simple, explicit, testable

## 4. Backward Compatibility Strategy

### Decision: Default to async mode, require explicit sync mode opt-in

**Rationale**:
- Preserves existing behavior (no silent changes)
- Orchestrator must explicitly choose sync mode
- Future code can continue using async if event loop is available
- No breaking changes to existing tests or code

**Migration Path**:
```python
# Existing code - unchanged, uses async
writer = EventWriter(output_dir, sim_id)

# New code - explicit sync mode
writer = EventWriter(output_dir, sim_id, mode=WriteMode.SYNC)
```

**Alternatives Considered**:
1. **Auto-detect execution context**: Silent behavior change, violates "No Legacy Support"
2. **Default to sync mode**: Breaking change for any async orchestrator code
3. ✅ **Explicit mode selection, async default**: Zero breaking changes

## 5. File Rotation in Sync Mode

### Decision: Synchronous rotation using `os.rename()` (same as async)

**Rationale**:
- File rotation is already atomic on POSIX (rename syscall)
- `os.rename()` is synchronous and fast (~1ms)
- No need for async file operations in sync mode
- Reuses existing timestamp format and rotation logic

**Implementation**:
```python
def _rotate_file_sync(self) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    rotated_file = self.output_dir / f"events_{timestamp}.jsonl"
    os.rename(self.current_file, rotated_file)
    self.current_size = 0
```

**Alternatives Considered**:
1. **Copy + delete**: Slower, not atomic
2. **Disable rotation in sync mode**: Limits durability for long runs
3. ✅ **Synchronous rename**: Simple, atomic, fast

## 6. Error Handling Strategy

### Decision: Log errors and continue (same as async mode)

**Rationale**:
- Event writing should not crash simulation
- Errors are rare (disk full, permissions)
- Logging provides observability
- Simulation can continue with degraded observability

**Error Scenarios**:
```python
# Write error
try:
    with open(file, 'a') as f:
        f.write(event_line)
        f.flush()
        os.fsync(f.fileno())
except IOError as e:
    logger.error("event_file_write_failed",
                 file=str(file),
                 event_id=event.event_id,
                 error=str(e),
                 mode="sync")
    # Continue - don't crash simulation
```

**Alternatives Considered**:
1. **Raise exception**: Would crash simulation on disk full
2. **Retry logic**: Adds complexity, unlikely to help (disk full is persistent)
3. ✅ **Log and continue**: Graceful degradation, matches async behavior

## 7. Performance Validation

### Expected Performance (Sync Mode)

**Write Latency**:
- Single event write with fsync: ~1ms (SSD), ~10ms (HDD)
- Current simulation scale: 200 events per run
- Total overhead: ~200ms per simulation run (negligible)

**Throughput**:
- Sync mode: ~1,000 events/sec
- Current event rate: ~10 events/turn × 20 turns / 60 seconds = ~3 events/sec
- Headroom: 300x over current needs

**File Rotation Overhead**:
- Rotation trigger: 500MB file size
- Average event size: ~500 bytes
- Events before rotation: ~1M events
- Current simulations: ~200 events (0.02% of threshold)
- Rotation probability per run: ~0%

**Conclusion**: Sync mode performance is more than adequate for current scale. fsync overhead is negligible compared to LLM inference time (~1-5 seconds per turn).

## 8. Testing Strategy

### Decision: TDD approach with separate test file for sync mode

**Test Structure**:
```
tests/unit/infrastructure/events/
├── test_event_writer_async.py  # Existing async tests (unchanged)
└── test_event_writer_sync.py   # New sync mode tests

tests/integration/
└── test_sync_simulation_events.py  # End-to-end test
```

**Test Coverage**:
1. **Unit - Sync mode writes immediately** (test_sync_mode_writes_immediately)
2. **Unit - File rotation at threshold** (test_sync_mode_file_rotation)
3. **Unit - No async dependency** (test_sync_mode_no_async_dependency)
4. **Unit - Mode selection respected** (test_mode_selection)
5. **Integration - Full simulation creates events.jsonl** (test_sync_simulation_creates_events)

**Rationale**:
- Separate files keep async tests unchanged (backward compatibility)
- Each test focused on one behavior
- Integration test validates end-to-end fix
- All tests must fail before implementation (red phase)

## 9. Migration Path to Microservices (Future)

### Decision: Keep same interface for future remote event service

**Future-Proofing**:
```python
# Phase 1 (Current): Local sync mode
writer = EventWriter(output_dir, sim_id, mode=WriteMode.SYNC)

# Phase 2 (Future): Remote event service
writer = RemoteEventWriter(service_url, sim_id)

# Same interface
writer.emit(event)  # Works for both
```

**Rationale**:
- `emit(event)` interface is service-agnostic
- Mode parameter becomes service URL parameter
- Sync guarantees translate to synchronous HTTP POST
- No changes needed to simulation code

**Migration Steps** (documented, not implemented):
1. Deploy remote event service
2. Create RemoteEventWriter adapter class
3. Update orchestrator configuration (URL instead of directory)
4. Keep local fallback for development

## Research Summary

All research complete. No NEEDS CLARIFICATION markers remain. Key decisions:

1. ✅ **Root Cause**: Async writer blocked by synchronous execution
2. ✅ **Solution**: Add sync mode with explicit fsync for durability
3. ✅ **Architecture**: Single class with mode parameter (KISS)
4. ✅ **Backward Compatibility**: Async default, explicit sync opt-in
5. ✅ **Performance**: Adequate for current scale (200 events/run)
6. ✅ **Testing**: TDD with 5 tests (4 unit, 1 integration)
7. ✅ **Future**: Interface ready for remote event service migration

**Next Phase**: Design (data model, contracts, quickstart)
