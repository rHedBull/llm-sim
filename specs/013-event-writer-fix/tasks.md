# Tasks: EventWriter Synchronous Mode Implementation

**Feature**: 013-event-writer-fix
**Input**: Design documents from `/home/hendrik/coding/llm_sim/llm_sim/specs/013-event-writer-fix/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
   → Tech stack: Python 3.12, Pydantic 2.x, structlog 24.x
   → Structure: Single project (src/, tests/)
2. Load design documents ✓
   → data-model.md: WriteMode enum, EventWriter modifications
   → contracts/: event_writer_interface.py (20 contract tests)
   → research.md: Sync mode with fsync, TDD approach
3. Generate tasks by category ✓
   → Setup: WriteMode enum, exports
   → Tests: 4 unit tests, 1 integration test (TDD red phase)
   → Core: EventWriter modifications (green phase)
   → Integration: Orchestrator update
   → Polish: Validation, performance tests
4. Apply task rules ✓
   → Tests in parallel [P] (different files)
   → Implementation sequential (same file: writer.py)
5. Number tasks sequentially (T001-T018) ✓
6. TDD enforcement: Tests must fail before implementation ✓
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
Single project structure:
- Source: `src/llm_sim/`
- Tests: `tests/unit/`, `tests/integration/`
- Scenarios: `scenarios/`

---

## Phase A: Setup (Parallel)

- [x] T001 [P] Add WriteMode enum to writer.py
- [x] T002 [P] Export WriteMode from __init__.py

### T001 [P] Add WriteMode enum to writer.py
**File**: `src/llm_sim/infrastructure/events/writer.py`
**Lines**: Insert after imports (after line 16)

Add the WriteMode enum definition:
```python
class WriteMode(str, Enum):
    """Event writer operation modes."""
    ASYNC = "async"
    SYNC = "sync"
```

**Validation**:
- Enum has exactly 2 values: ASYNC and SYNC
- Both values are strings
- Inherits from str and Enum
- Has docstring

**Depends on**: None
**Blocks**: T002, all test tasks

---

### T002 [P] Export WriteMode from __init__.py
**File**: `src/llm_sim/infrastructure/events/__init__.py`

Update exports to include WriteMode:
```python
from llm_sim.infrastructure.events.writer import EventWriter, WriteMode
```

**Validation**:
- WriteMode is importable: `from llm_sim.infrastructure.events import WriteMode`
- No import errors

**Depends on**: T001
**Blocks**: All test tasks

---

## Phase B: Tests First (TDD - Red Phase) ⚠️ MUST COMPLETE BEFORE PHASE D

**CRITICAL**: These tests MUST be written and MUST FAIL before ANY implementation tasks in Phase D.

- [x] T003 [P] Write test_sync_mode_writes_immediately
- [x] T004 [P] Write test_sync_mode_file_rotation
- [x] T005 [P] Write test_sync_mode_no_async_dependency
- [x] T006 [P] Write test_mode_selection
- [x] T007 [P] Write test_sync_simulation_creates_events

### T003 [P] Write test_sync_mode_writes_immediately
**File**: `tests/unit/infrastructure/events/test_event_writer_sync.py` (NEW FILE)

Create new test file with test for immediate sync writes:

```python
"""Unit tests for EventWriter synchronous mode."""

import tempfile
from pathlib import Path

import pytest

from llm_sim.infrastructure.events.writer import EventWriter, WriteMode
from llm_sim.models.event import Event


def test_sync_mode_writes_immediately():
    """Test that sync mode writes events immediately to disk.

    CONTRACT: Sync mode must write and fsync before emit() returns.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = EventWriter(
            output_dir=Path(tmpdir),
            simulation_id="test_sync",
            mode=WriteMode.SYNC,
        )

        # Emit event
        event = Event(
            event_type="test_event",
            simulation_id="test_sync",
            data={"test": "data"},
        )
        writer.emit(event)

        # Check file exists immediately
        event_file = Path(tmpdir) / "events.jsonl"
        assert event_file.exists(), "Event file must exist immediately after emit()"

        # Check content
        content = event_file.read_text()
        assert "test_event" in content
        assert "test_sync" in content
```

**Validation**:
- Test file created in correct location
- Test imports EventWriter and WriteMode
- Test uses WriteMode.SYNC
- Test verifies immediate file existence
- Test FAILS initially (no _write_event_sync implementation yet)

**Depends on**: T001, T002
**Blocks**: T009 (implementation of sync write)

---

### T004 [P] Write test_sync_mode_file_rotation
**File**: `tests/unit/infrastructure/events/test_event_writer_sync.py` (APPEND)

Add test for file rotation in sync mode:

```python
def test_sync_mode_file_rotation():
    """Test that sync mode rotates files at size threshold.

    CONTRACT: Files must rotate when size exceeds max_file_size.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Small file size for testing
        writer = EventWriter(
            output_dir=Path(tmpdir),
            simulation_id="test_rotation",
            mode=WriteMode.SYNC,
            max_file_size=1000,  # 1KB for testing
        )

        # Write events until rotation
        large_data = "x" * 500  # 500 bytes per event
        for i in range(5):  # 2500 bytes total
            event = Event(
                event_type="large_event",
                simulation_id="test_rotation",
                data={"index": i, "payload": large_data},
            )
            writer.emit(event)

        # Check that rotation occurred
        files = list(Path(tmpdir).glob("events*.jsonl"))
        assert len(files) >= 2, "Expected at least 2 files (current + rotated)"

        # Verify current file exists
        assert (Path(tmpdir) / "events.jsonl").exists()

        # Verify rotated file has timestamp
        rotated = [f for f in files if "events_" in f.name and f.name != "events.jsonl"]
        assert len(rotated) > 0, "Expected rotated file with timestamp"
```

**Validation**:
- Test appended to test_event_writer_sync.py
- Test creates small max_file_size
- Test writes enough data to trigger rotation
- Test verifies multiple files exist
- Test FAILS initially (no _rotate_file_sync implementation yet)

**Depends on**: T001, T002
**Blocks**: T010 (implementation of sync rotation)

---

### T005 [P] Write test_sync_mode_no_async_dependency
**File**: `tests/unit/infrastructure/events/test_event_writer_sync.py` (APPEND)

Add test verifying sync mode works without event loop:

```python
def test_sync_mode_no_async_dependency():
    """Test that sync mode works without async event loop.

    CONTRACT: Sync mode must work in pure synchronous contexts.
    """
    # This test runs in pure sync context (no asyncio)
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = EventWriter(
            output_dir=Path(tmpdir),
            simulation_id="test_no_async",
            mode=WriteMode.SYNC,
        )

        # Should work fine without event loop
        for i in range(10):
            event = Event(
                event_type="sync_event",
                simulation_id="test_no_async",
                data={"count": i},
            )
            writer.emit(event)

        # Verify all events written
        content = (Path(tmpdir) / "events.jsonl").read_text()
        assert content.count("sync_event") == 10
```

**Validation**:
- Test appended to test_event_writer_sync.py
- Test is synchronous (no async/await)
- Test writes multiple events
- Test verifies all events written
- Test FAILS initially (no sync mode implementation)

**Depends on**: T001, T002
**Blocks**: T008-T013 (all sync mode implementation)

---

### T006 [P] Write test_mode_selection
**File**: `tests/unit/infrastructure/events/test_event_writer_sync.py` (APPEND)

Add test verifying mode parameter is respected:

```python
def test_mode_selection():
    """Test that writer respects mode parameter.

    CONTRACT: Mode must be settable and respected at initialization.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        sync_writer = EventWriter(
            output_dir=Path(tmpdir),
            simulation_id="test",
            mode=WriteMode.SYNC,
        )
        assert sync_writer.mode == WriteMode.SYNC

        async_writer = EventWriter(
            output_dir=Path(tmpdir),
            simulation_id="test2",
            mode=WriteMode.ASYNC,
        )
        assert async_writer.mode == WriteMode.ASYNC

        # Test default is ASYNC (backward compatibility)
        default_writer = EventWriter(
            output_dir=Path(tmpdir),
            simulation_id="test3",
        )
        assert default_writer.mode == WriteMode.ASYNC
```

**Validation**:
- Test appended to test_event_writer_sync.py
- Test creates writers in both modes
- Test verifies mode attribute
- Test verifies async is default
- Test FAILS initially (no mode parameter yet)

**Depends on**: T001, T002
**Blocks**: T008 (add mode parameter)

---

### T007 [P] Write test_sync_simulation_creates_events (integration)
**File**: `tests/integration/test_sync_simulation_events.py` (NEW FILE)

Create integration test for full simulation:

```python
"""Integration test for sync EventWriter with simulation."""

import pytest
from pathlib import Path

from llm_sim.orchestrator import Orchestrator
from llm_sim.models.config import SimulationConfig


@pytest.mark.asyncio
async def test_sync_simulation_creates_events():
    """Test that sync simulation mode creates events.jsonl.

    This is the end-to-end test validating the fix for missing events.jsonl files.
    """
    # Load test scenario
    config = SimulationConfig.from_file("scenarios/spatial_trade_network.yaml")

    # Run simulation
    orchestrator = Orchestrator(config)
    await orchestrator.run()

    # Check events file exists
    event_files = list(orchestrator.output_dir.glob("*/events.jsonl"))
    assert len(event_files) > 0, "No events.jsonl created - bug not fixed!"

    # Check events were written
    event_content = event_files[0].read_text()
    event_lines = event_content.strip().split("\n")
    assert len(event_lines) > 0, "events.jsonl is empty"

    # Check for expected event types
    assert "simulation_starting" in event_content
    assert "turn_completed" in event_content
```

**Validation**:
- Test file created in tests/integration/
- Test runs full simulation
- Test verifies events.jsonl exists
- Test checks expected event types
- Test FAILS initially (orchestrator still uses async mode)

**Depends on**: T001, T002
**Blocks**: T014 (orchestrator integration)

---

## Phase C: Verify Red Phase

- [x] T008 Run tests and verify they fail

### T008 Run tests and verify they fail
**Command**: `uv run pytest tests/unit/infrastructure/events/test_event_writer_sync.py tests/integration/test_sync_simulation_events.py -v`

Expected output:
```
tests/unit/infrastructure/events/test_event_writer_sync.py::test_sync_mode_writes_immediately FAILED
tests/unit/infrastructure/events/test_event_writer_sync.py::test_sync_mode_file_rotation FAILED
tests/unit/infrastructure/events/test_event_writer_sync.py::test_sync_mode_no_async_dependency FAILED
tests/unit/infrastructure/events/test_event_writer_sync.py::test_mode_selection FAILED
tests/integration/test_sync_simulation_events.py::test_sync_simulation_creates_events FAILED

====== 5 failed in X.Xs ======
```

**Validation**:
- All 5 tests MUST fail
- Failures due to missing implementation (not import errors)
- If tests pass or have import errors, fix tests before proceeding

**Depends on**: T003-T007
**Blocks**: T009 (cannot implement until tests fail)

---

## Phase D: Implementation (Green Phase)

**CRITICAL**: Only proceed after verifying tests fail in T008.

- [x] T009 Add mode parameter to EventWriter.__init__
- [x] T010 Implement _write_event_sync method
- [x] T011 Implement _rotate_file_sync method
- [x] T012 Update emit() to dispatch by mode
- [x] T013 Update start() for sync mode no-op
- [x] T014 Update stop() for sync mode no-op

### T009 Add mode parameter to EventWriter.__init__
**File**: `src/llm_sim/infrastructure/events/writer.py`
**Lines**: Modify __init__ method (around line 30-46)

Update the constructor signature and initialization:

```python
def __init__(
    self,
    output_dir: Path,
    simulation_id: str,
    verbosity: VerbosityLevel = VerbosityLevel.ACTION,
    max_queue_size: int = 10000,
    max_file_size: int = ROTATION_SIZE_BYTES,
    mode: WriteMode = WriteMode.ASYNC,  # NEW PARAMETER
) -> None:
    """Initialize event writer.

    Args:
        output_dir: Directory for event files
        simulation_id: Simulation run identifier
        verbosity: Event verbosity level
        max_queue_size: Maximum events to queue before dropping (async mode only)
        max_file_size: Maximum file size before rotation (default 500MB)
        mode: Write mode (async or sync)
    """
    self.output_dir = Path(output_dir)
    self.simulation_id = simulation_id
    self.verbosity = verbosity
    self.max_queue_size = max_queue_size
    self.max_file_size = max_file_size
    self.mode = mode  # NEW

    # Async mode state
    self.queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=max_queue_size)
    self.writer_task: Optional[asyncio.Task] = None
    self.running = False
    self.dropped_count = 0

    # Current event file
    self.current_file = self.output_dir / "events.jsonl"
    self.current_size = 0

    # Ensure output directory exists
    self.output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "event_writer_initialized",
        mode=self.mode.value,
        output_dir=str(self.output_dir),
        verbosity=self.verbosity.value,
    )
```

**Validation**:
- Mode parameter added with default WriteMode.ASYNC
- self.mode assigned
- Logger includes mode in output
- test_mode_selection should now pass

**Depends on**: T008
**Blocks**: T010-T013

---

### T010 Implement _write_event_sync method
**File**: `src/llm_sim/infrastructure/events/writer.py`
**Lines**: Add new method after _rotate_file (after line 207)

Add synchronous event write method:

```python
def _write_event_sync(self, event: Event) -> None:
    """Synchronously write event to file with rotation check.

    This method is blocking and should only be called in sync mode.
    File writes are flushed immediately to ensure persistence.

    Args:
        event: Event to write
    """
    # Check if rotation needed
    if self.current_size >= self.max_file_size:
        self._rotate_file_sync()

    # Serialize event
    event_json = event.model_dump_json()
    event_line = event_json + "\n"
    event_bytes = event_line.encode("utf-8")

    # Synchronous atomic write with immediate flush
    try:
        with open(self.current_file, mode="a", encoding="utf-8") as f:
            f.write(event_line)
            f.flush()  # Force write to disk
            os.fsync(f.fileno())  # Ensure OS buffers are flushed

        # Update size
        self.current_size += len(event_bytes)

    except IOError as e:
        logger.error(
            "event_file_write_failed",
            file=str(self.current_file),
            event_id=event.event_id,
            error=str(e),
            mode="sync",
        )
```

**Validation**:
- Method added to EventWriter class
- Uses standard open() (not aiofiles)
- Calls flush() and fsync()
- Updates current_size
- Logs errors with mode="sync"
- test_sync_mode_writes_immediately should now pass

**Depends on**: T009
**Blocks**: T011

---

### T011 Implement _rotate_file_sync method
**File**: `src/llm_sim/infrastructure/events/writer.py`
**Lines**: Add new method after _write_event_sync

Add synchronous file rotation method:

```python
def _rotate_file_sync(self) -> None:
    """Synchronously rotate the current event file when size threshold exceeded.

    This is a blocking operation that renames the current file and resets
    the size counter. Safe to call from sync contexts.
    """
    # Generate timestamped filename with microseconds to avoid collisions
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    rotated_file = self.output_dir / f"events_{timestamp}.jsonl"

    # Rename current file
    if self.current_file.exists():
        try:
            os.rename(self.current_file, rotated_file)
            size_mb = self.current_size / (1024 * 1024)
            logger.info(
                "event_file_rotated",
                old_file=str(self.current_file),
                new_file=str(rotated_file),
                size_mb=round(size_mb, 2),
                mode="sync",
            )
        except OSError as e:
            logger.error(
                "event_file_rotation_failed",
                error=str(e),
                mode="sync",
            )

    # Reset size counter
    self.current_size = 0
```

**Validation**:
- Method added to EventWriter class
- Uses os.rename() (not async)
- Logs rotation with mode="sync"
- Resets current_size
- test_sync_mode_file_rotation should now pass

**Depends on**: T010
**Blocks**: T012

---

### T012 Update emit() to dispatch by mode
**File**: `src/llm_sim/infrastructure/events/writer.py`
**Lines**: Modify emit method (around line 113-133)

Update emit() to branch based on mode:

```python
def emit(self, event: Event) -> None:
    """Emit an event (mode-aware, non-blocking in async mode).

    Args:
        event: Event to emit
    """
    # Check verbosity filter (shared by both modes)
    if not should_log_event(event.event_type, self.verbosity):
        return

    if self.mode == WriteMode.SYNC:
        # Synchronous write - immediate, blocking
        self._write_event_sync(event)
    else:
        # Async write - queue and return immediately
        try:
            self.queue.put_nowait(event)
        except asyncio.QueueFull:
            self.dropped_count += 1
            if self.dropped_count % 100 == 0:  # Log every 100 drops
                logger.warning(
                    "event_queue_full_dropping",
                    event_id=event.event_id,
                    total_dropped=self.dropped_count,
                )
```

**Validation**:
- emit() checks self.mode
- Calls _write_event_sync() in sync mode
- Preserves async queue logic in async mode
- test_sync_mode_no_async_dependency should now pass

**Depends on**: T011
**Blocks**: T013

---

### T013 Update start() for sync mode no-op
**File**: `src/llm_sim/infrastructure/events/writer.py`
**Lines**: Modify start method (around line 65-76)

Update start() to skip in sync mode:

```python
async def start(self) -> None:
    """Start the background writer task (async mode only).

    In sync mode, this is a no-op since writes happen immediately.
    """
    if self.mode == WriteMode.SYNC:
        logger.info(
            "event_writer_start_skipped",
            reason="sync mode writes immediately",
        )
        return

    if self.running:
        return

    self.running = True
    self.writer_task = asyncio.create_task(self._write_loop())
    logger.info(
        "event_writer_started",
        output_dir=str(self.output_dir),
        verbosity=self.verbosity.value,
    )
```

**Validation**:
- Checks mode at beginning
- Returns early if sync mode
- Logs skip reason
- Preserves async task creation

**Depends on**: T012
**Blocks**: T014

---

### T014 Update stop() for sync mode no-op
**File**: `src/llm_sim/infrastructure/events/writer.py`
**Lines**: Modify stop method (around line 78-111)

Update stop() to skip in sync mode:

```python
async def stop(self, timeout: float = 10.0) -> None:
    """Stop the writer and flush pending events.

    In sync mode, this is a no-op since all writes are already flushed.

    Args:
        timeout: Maximum seconds to wait for queue drain (async mode only)
    """
    if self.mode == WriteMode.SYNC:
        logger.info(
            "event_writer_stopped",
            mode="sync",
            note="all events written synchronously",
        )
        return

    if not self.running:
        return

    self.running = False

    # Wait for queue to drain with timeout
    try:
        await asyncio.wait_for(self.queue.join(), timeout=timeout)
    except asyncio.TimeoutError:
        remaining = self.queue.qsize()
        logger.warning(
            "event_writer_timeout",
            remaining_events=remaining,
            timeout_seconds=timeout,
        )

    # Cancel writer task
    if self.writer_task:
        self.writer_task.cancel()
        try:
            await self.writer_task
        except asyncio.CancelledError:
            pass

    logger.info(
        "event_writer_stopped",
        total_dropped=self.dropped_count,
    )
```

**Validation**:
- Checks mode at beginning
- Returns early if sync mode
- Logs completion with mode context
- Preserves async queue drain logic

**Depends on**: T013
**Blocks**: T015

---

## Phase E: Integration

- [x] T015 Update orchestrator to use WriteMode.SYNC
- [x] T016 Run all tests - expect PASS (green phase)

### T015 Update orchestrator to use WriteMode.SYNC
**File**: `src/llm_sim/orchestrator.py`
**Lines**: Modify EventWriter initialization (search for "EventWriter(")

Import WriteMode and use sync mode:

1. Add import at top of file:
```python
from llm_sim.infrastructure.events.writer import EventWriter, WriteMode
```

2. Update EventWriter initialization (around line 100):
```python
self.event_writer = EventWriter(
    output_dir=self.output_dir,
    simulation_id=self.run_id,
    verbosity=verbosity,
    mode=WriteMode.SYNC,  # Use sync mode for sync execution
)
```

**Validation**:
- WriteMode imported
- mode=WriteMode.SYNC added to EventWriter call
- test_sync_simulation_creates_events should now pass

**Depends on**: T014
**Blocks**: T016

---

### T016 Run all tests - expect PASS (green phase)
**Command**: `uv run pytest tests/unit/infrastructure/events/test_event_writer_sync.py tests/integration/test_sync_simulation_events.py -v`

Expected output:
```
tests/unit/infrastructure/events/test_event_writer_sync.py::test_sync_mode_writes_immediately PASSED
tests/unit/infrastructure/events/test_event_writer_sync.py::test_sync_mode_file_rotation PASSED
tests/unit/infrastructure/events/test_event_writer_sync.py::test_sync_mode_no_async_dependency PASSED
tests/unit/infrastructure/events/test_event_writer_sync.py::test_mode_selection PASSED
tests/integration/test_sync_simulation_events.py::test_sync_simulation_creates_events PASSED

====== 5 passed in X.Xs ======
```

**Validation**:
- All 5 tests MUST pass
- No test failures
- Green phase complete (TDD cycle: Red → Green)

**Action if failures**:
- Debug failing tests
- Fix implementation bugs
- Re-run until all pass
- Do NOT proceed to Phase F until all tests pass

**Depends on**: T015
**Blocks**: T017

---

## Phase F: Validation & Polish

- [x] T017 Execute quickstart validation (steps 1-7)
- [x] T018 Run performance benchmarks

### T017 Execute quickstart validation (steps 1-7)
**File**: Follow steps in `specs/013-event-writer-fix/quickstart.md`

Execute all 7 quickstart validation steps:

1. **Step 1**: Verify WriteMode enum exists
   ```bash
   uv run python -c "from llm_sim.infrastructure.events.writer import WriteMode; print('✅ WriteMode enum verified')"
   ```

2. **Step 2**: Verify sync mode writes immediately
   ```bash
   uv run python -c "
   import tempfile
   from pathlib import Path
   from llm_sim.infrastructure.events.writer import EventWriter, WriteMode
   from llm_sim.models.event import Event

   with tempfile.TemporaryDirectory() as tmpdir:
       writer = EventWriter(output_dir=Path(tmpdir), simulation_id='test', mode=WriteMode.SYNC)
       event = Event(event_type='test', simulation_id='test', data={})
       writer.emit(event)
       assert (Path(tmpdir) / 'events.jsonl').exists()
       print('✅ Sync mode writes immediately')
   "
   ```

3. **Step 3**: Verify async mode still works
   ```bash
   # Run async mode test from quickstart.md
   ```

4. **Step 4**: Run unit tests
   ```bash
   uv run pytest tests/unit/infrastructure/events/test_event_writer_sync.py -v
   ```

5. **Step 5**: Run integration test
   ```bash
   uv run pytest tests/integration/test_sync_simulation_events.py -v
   ```

6. **Step 6**: Manual simulation test
   ```bash
   uv run python -m llm_sim.main scenarios/spatial_trade_network.yaml
   # Verify events.jsonl exists and has content
   ```

7. **Step 7**: Verify file rotation
   ```bash
   # Run rotation test from quickstart.md
   ```

**Validation**:
- All 7 steps complete successfully
- Each step shows ✅ indicator
- Manual simulation creates events.jsonl
- File rotation works correctly

**Depends on**: T016
**Blocks**: T018

---

### T018 Run performance benchmarks
**Command**: Execute performance validation from quickstart.md

```bash
uv run python -c "
import time
import tempfile
from pathlib import Path
from llm_sim.infrastructure.events.writer import EventWriter, WriteMode
from llm_sim.models.event import Event

with tempfile.TemporaryDirectory() as tmpdir:
    writer = EventWriter(
        output_dir=Path(tmpdir),
        simulation_id='perf_test',
        mode=WriteMode.SYNC,
    )

    # Time 100 event writes
    start = time.perf_counter()
    for i in range(100):
        event = Event(
            event_type='perf_event',
            simulation_id='perf_test',
            data={'index': i},
        )
        writer.emit(event)
    elapsed = time.perf_counter() - start

    avg_latency_ms = (elapsed / 100) * 1000
    print(f'Average write latency: {avg_latency_ms:.2f}ms')
    print(f'Throughput: {100/elapsed:.0f} events/sec')

    # Should be < 10ms per event on SSD
    assert avg_latency_ms < 10, 'Write latency too high'
    print('✅ Performance acceptable')
"
```

**Validation**:
- Average latency < 10ms per event
- Throughput > 100 events/sec
- Test completes without assertion errors
- Performance meets requirements from research.md

**Depends on**: T017
**Blocks**: None (final task)

---

## Task Dependencies

```
Setup Phase (Parallel):
  T001 [P] ─────┐
  T002 [P] ─────┤
                ├──→ Test Phase

Test Phase (Parallel - Red):
  T003 [P] ─────┐
  T004 [P] ─────┤
  T005 [P] ─────┤
  T006 [P] ─────┤
  T007 [P] ─────┤
                ├──→ T008 (verify red)

Verify Red:
  T008 ──────────→ Implementation Phase

Implementation Phase (Sequential - Green):
  T009 → T010 → T011 → T012 → T013 → T014

Integration Phase:
  T015 → T016 (verify green)

Validation Phase:
  T017 → T018
```

## Parallel Execution Examples

### Phase A: Setup (2 tasks in parallel)
```bash
# Terminal 1:
# Task T001: Add WriteMode enum

# Terminal 2:
# Task T002: Export WriteMode from __init__.py
```

### Phase B: Tests (5 tasks in parallel)
```bash
# Terminal 1:
# Task T003: Write test_sync_mode_writes_immediately

# Terminal 2:
# Task T004: Write test_sync_mode_file_rotation

# Terminal 3:
# Task T005: Write test_sync_mode_no_async_dependency

# Terminal 4:
# Task T006: Write test_mode_selection

# Terminal 5:
# Task T007: Write test_sync_simulation_creates_events
```

## Critical Path

The longest sequential path (critical path):
```
T001 → T002 → T003 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018
(14 sequential tasks)
```

Estimated time:
- Setup: 10 minutes (T001-T002)
- Tests: 30 minutes (T003-T007 in parallel)
- Verify red: 2 minutes (T008)
- Implementation: 60 minutes (T009-T014)
- Integration: 10 minutes (T015-T016)
- Validation: 20 minutes (T017-T018)
- **Total**: ~2.5 hours

With parallelization:
- Phase A: 5 minutes (parallel)
- Phase B: 15 minutes (parallel test writing)
- Phases C-F: 2 hours (sequential)
- **Total**: ~2.2 hours

## Validation Checklist

Pre-execution validation:
- [x] All contracts have corresponding tests (event_writer_interface.py → T003-T006)
- [x] All entities have model tasks (WriteMode enum → T001)
- [x] All tests come before implementation (T003-T007 before T009-T014)
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task

Post-execution validation:
- [ ] All 18 tasks completed
- [ ] All 5 tests pass (4 unit, 1 integration)
- [ ] events.jsonl created in simulations
- [ ] Performance benchmarks met
- [ ] Quickstart validation complete
- [ ] No regressions in existing async mode

## Notes

- **TDD Enforcement**: Tasks T003-T007 MUST fail before starting T009
- **Same File Constraint**: T009-T014 modify writer.py sequentially (no parallel)
- **Backward Compatibility**: Default mode is ASYNC (preserves existing behavior)
- **Performance**: Sync mode ~1ms/event is acceptable for 200 events/simulation
- **File Rotation**: Rotation at 500MB threshold (unlikely with current scale)
- **Error Handling**: Log errors, don't crash simulation
- **Commit Strategy**: Commit after each phase completion

## Commit Messages

Suggested commit messages after each phase:

- After T002: `feat: Add WriteMode enum for EventWriter`
- After T007: `test: Add sync mode tests (TDD red phase)`
- After T008: `test: Verify all sync mode tests fail`
- After T014: `feat: Implement EventWriter synchronous mode`
- After T015: `feat: Integrate sync mode with Orchestrator`
- After T016: `test: Verify all sync mode tests pass (TDD green phase)`
- After T018: `chore: Validate sync mode performance and quickstart`

## Success Criteria

Feature is complete when:
1. ✅ All 18 tasks completed
2. ✅ All tests pass (5/5)
3. ✅ Manual simulation creates events.jsonl
4. ✅ Performance benchmarks met (<10ms/event)
5. ✅ Quickstart validation passes (7/7 steps)
6. ✅ Zero breaking changes to async mode
7. ✅ Constitution compliance maintained (all 7 principles)

---

**Ready for execution**: Tasks can be executed in order T001 → T018
