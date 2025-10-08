# Quickstart: EventWriter Synchronous Mode

**Feature**: 013-event-writer-fix
**Date**: 2025-10-08
**Validation**: Run this document as a test to verify feature completion

## Purpose

This quickstart validates that the EventWriter synchronous mode implementation works end-to-end. Follow these steps to verify the fix for missing `events.jsonl` files.

## Prerequisites

- Python 3.12 installed
- Project dependencies installed (`uv sync`)
- Working directory: `/home/hendrik/coding/llm_sim/llm_sim`

## Validation Steps

### Step 1: Verify WriteMode Enum Exists

**Test**: Import and inspect WriteMode enum

```bash
uv run python -c "
from llm_sim.infrastructure.events.writer import WriteMode
print('WriteMode.ASYNC:', WriteMode.ASYNC)
print('WriteMode.SYNC:', WriteMode.SYNC)
assert WriteMode.ASYNC == 'async'
assert WriteMode.SYNC == 'sync'
print('✅ WriteMode enum verified')
"
```

**Expected Output**:
```
WriteMode.ASYNC: async
WriteMode.SYNC: sync
✅ WriteMode enum verified
```

**Acceptance Criteria**:
- ✅ WriteMode enum imported successfully
- ✅ ASYNC and SYNC values available
- ✅ Values are strings ("async", "sync")

---

### Step 2: Verify Sync Mode Writes Immediately

**Test**: Create EventWriter in sync mode and verify immediate write

```bash
uv run python -c "
import tempfile
from pathlib import Path
from llm_sim.infrastructure.events.writer import EventWriter, WriteMode
from llm_sim.models.event import Event

# Create temp directory
with tempfile.TemporaryDirectory() as tmpdir:
    output_dir = Path(tmpdir)

    # Initialize writer in SYNC mode
    writer = EventWriter(
        output_dir=output_dir,
        simulation_id='quickstart_test',
        mode=WriteMode.SYNC,
    )

    print(f'Writer mode: {writer.mode}')
    assert writer.mode == WriteMode.SYNC

    # Emit test event
    event = Event(
        event_type='test_event',
        simulation_id='quickstart_test',
        data={'test': 'immediate_write'},
    )
    writer.emit(event)

    # Verify file exists immediately (no need to wait or call stop)
    event_file = output_dir / 'events.jsonl'
    assert event_file.exists(), 'Event file must exist immediately after emit()'

    # Verify content
    content = event_file.read_text()
    assert 'test_event' in content
    assert 'immediate_write' in content

    print('✅ Sync mode writes immediately')
"
```

**Expected Output**:
```
Writer mode: sync
✅ Sync mode writes immediately
```

**Acceptance Criteria**:
- ✅ EventWriter accepts mode=WriteMode.SYNC
- ✅ emit() completes without errors
- ✅ events.jsonl exists immediately after emit()
- ✅ Event content is readable and correct

---

### Step 3: Verify Async Mode Still Works

**Test**: Verify backward compatibility with async mode

```bash
uv run python -c "
import asyncio
import tempfile
from pathlib import Path
from llm_sim.infrastructure.events.writer import EventWriter, WriteMode
from llm_sim.models.event import Event

async def test_async_mode():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Initialize writer in ASYNC mode (default)
        writer = EventWriter(
            output_dir=output_dir,
            simulation_id='async_test',
        )

        print(f'Writer mode: {writer.mode}')
        assert writer.mode == WriteMode.ASYNC

        # Start writer
        await writer.start()

        # Emit event
        event = Event(
            event_type='async_event',
            simulation_id='async_test',
            data={'mode': 'async'},
        )
        writer.emit(event)

        # Stop writer (flushes queue)
        await writer.stop()

        # Verify file exists
        event_file = output_dir / 'events.jsonl'
        assert event_file.exists()

        content = event_file.read_text()
        assert 'async_event' in content

        print('✅ Async mode backward compatibility verified')

asyncio.run(test_async_mode())
"
```

**Expected Output**:
```
Writer mode: async
✅ Async mode backward compatibility verified
```

**Acceptance Criteria**:
- ✅ Default mode is ASYNC
- ✅ Async mode requires start() and stop()
- ✅ Events written after stop() (queue flushed)
- ✅ No breaking changes to async behavior

---

### Step 4: Run Unit Tests

**Test**: Execute all EventWriter tests

```bash
cd /home/hendrik/coding/llm_sim/llm_sim
uv run pytest tests/unit/infrastructure/events/test_event_writer_sync.py -v
```

**Expected Output**:
```
tests/unit/infrastructure/events/test_event_writer_sync.py::test_sync_mode_writes_immediately PASSED
tests/unit/infrastructure/events/test_event_writer_sync.py::test_sync_mode_file_rotation PASSED
tests/unit/infrastructure/events/test_event_writer_sync.py::test_sync_mode_no_async_dependency PASSED
tests/unit/infrastructure/events/test_event_writer_sync.py::test_mode_selection PASSED

====== 4 passed in 0.5s ======
```

**Acceptance Criteria**:
- ✅ All sync mode unit tests pass
- ✅ No test failures or errors
- ✅ Tests complete in < 5 seconds

---

### Step 5: Run Integration Test

**Test**: Full simulation with sync EventWriter

```bash
cd /home/hendrik/coding/llm_sim/llm_sim
uv run pytest tests/integration/test_sync_simulation_events.py -v
```

**Expected Output**:
```
tests/integration/test_sync_simulation_events.py::test_sync_simulation_creates_events PASSED

====== 1 passed in X.Xs ======
```

**Acceptance Criteria**:
- ✅ Integration test passes
- ✅ events.jsonl created in simulation output
- ✅ File contains expected event types

---

### Step 6: Manual Simulation Test

**Test**: Run actual simulation and verify events.jsonl

```bash
cd /home/hendrik/coding/llm_sim/llm_sim

# Run simulation
uv run python -m llm_sim.main scenarios/spatial_trade_network.yaml

# Find the events file
EVENTS_FILE=$(find src/output -name "events.jsonl" -type f | head -1)

echo "Events file: $EVENTS_FILE"

# Verify file exists and has content
if [ -f "$EVENTS_FILE" ]; then
    echo "✅ events.jsonl exists"
    EVENT_COUNT=$(wc -l < "$EVENTS_FILE")
    echo "Event count: $EVENT_COUNT"

    if [ "$EVENT_COUNT" -gt 0 ]; then
        echo "✅ Events written to file"

        # Show first few events
        echo "First 3 events:"
        head -3 "$EVENTS_FILE" | jq -r '.event_type'
    else
        echo "❌ No events in file"
        exit 1
    fi
else
    echo "❌ events.jsonl not found"
    exit 1
fi
```

**Expected Output**:
```
Events file: src/output/run_20251008_103045/sim_xyz/events.jsonl
✅ events.jsonl exists
Event count: 87
✅ Events written to file
First 3 events:
simulation_starting
turn_started
agent_action
```

**Acceptance Criteria**:
- ✅ events.jsonl created in output directory
- ✅ File contains > 0 events
- ✅ Events include simulation_starting, turn_started, etc.

---

### Step 7: Verify File Rotation

**Test**: Force file rotation by writing large events

```bash
uv run python -c "
import tempfile
from pathlib import Path
from llm_sim.infrastructure.events.writer import EventWriter, WriteMode
from llm_sim.models.event import Event

with tempfile.TemporaryDirectory() as tmpdir:
    output_dir = Path(tmpdir)

    # Small rotation threshold for testing
    writer = EventWriter(
        output_dir=output_dir,
        simulation_id='rotation_test',
        mode=WriteMode.SYNC,
        max_file_size=1000,  # 1KB
    )

    # Write events until rotation
    large_payload = 'x' * 400  # 400 bytes per event
    for i in range(5):  # 2000 bytes total
        event = Event(
            event_type='large_event',
            simulation_id='rotation_test',
            data={'index': i, 'payload': large_payload},
        )
        writer.emit(event)

    # Check for rotated files
    files = list(output_dir.glob('events*.jsonl'))
    print(f'Total files: {len(files)}')
    print(f'Files: {[f.name for f in files]}')

    assert len(files) >= 2, 'Expected at least 2 files (current + rotated)'

    # Verify current file exists
    assert (output_dir / 'events.jsonl').exists()

    # Verify rotated file has timestamp
    rotated = [f for f in files if 'events_' in f.name and f.name != 'events.jsonl']
    assert len(rotated) > 0, 'Expected rotated file with timestamp'

    print('✅ File rotation verified')
"
```

**Expected Output**:
```
Total files: 2
Files: ['events.jsonl', 'events_2025-10-08_10-30-45-123456.jsonl']
✅ File rotation verified
```

**Acceptance Criteria**:
- ✅ File rotates when size threshold exceeded
- ✅ Rotated file has timestamped name
- ✅ New events.jsonl created
- ✅ Multiple files present after rotation

---

## Success Criteria

All steps above must pass:

1. ✅ WriteMode enum available and correct
2. ✅ Sync mode writes immediately
3. ✅ Async mode backward compatibility preserved
4. ✅ Unit tests pass (4/4)
5. ✅ Integration test passes (1/1)
6. ✅ Manual simulation creates events.jsonl
7. ✅ File rotation works correctly

## Troubleshooting

### Issue: "ImportError: cannot import name 'WriteMode'"

**Solution**: Verify WriteMode is exported in `__init__.py`:
```bash
grep -r "WriteMode" src/llm_sim/infrastructure/events/__init__.py
```

Should see:
```python
from llm_sim.infrastructure.events.writer import WriteMode
```

---

### Issue: "events.jsonl not created"

**Solution**: Check orchestrator uses sync mode:
```bash
grep -A 5 "EventWriter" src/llm_sim/orchestrator.py
```

Should see:
```python
self.event_writer = EventWriter(
    output_dir=self.output_dir,
    simulation_id=self.run_id,
    mode=WriteMode.SYNC,  # Must be SYNC
)
```

---

### Issue: "Permission denied" when writing events

**Solution**: Check output directory permissions:
```bash
ls -la output/
chmod 755 output/
```

---

### Issue: Tests fail with "no running event loop"

**Solution**: Verify sync mode tests don't use async/await:
```bash
grep -n "async def" tests/unit/infrastructure/events/test_event_writer_sync.py
```

Sync mode tests should be synchronous functions, not async.

---

## Performance Validation

Optional: Measure sync mode performance

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

**Expected**: < 5ms average latency on modern SSD

---

## Rollback Procedure

If feature needs to be rolled back:

1. **Revert orchestrator change**:
   ```bash
   # Remove mode=WriteMode.SYNC from orchestrator
   git checkout src/llm_sim/orchestrator.py
   ```

2. **Keep async default**:
   - Async mode is default, so no changes needed
   - Existing code continues to work

3. **Remove tests** (optional):
   ```bash
   rm tests/unit/infrastructure/events/test_event_writer_sync.py
   rm tests/integration/test_sync_simulation_events.py
   ```

Feature can be disabled without removing code by switching orchestrator back to async mode.

---

**Quickstart Complete**: If all steps pass, the EventWriter synchronous mode feature is working correctly.
