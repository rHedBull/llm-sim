# Quickstart: Event Stream Activity Logging

**Feature**: Event Stream Activity Logging
**Branch**: 010-event-stream-the
**Date**: 2025-10-04

## Purpose

This quickstart validates the event streaming feature end-to-end by running a minimal simulation, capturing events at different verbosity levels, querying the API, and verifying event integrity.

## Prerequisites

```bash
# Ensure dependencies installed
uv sync

# Confirm Python version
uv run python --version  # Should be 3.12+

# Confirm new dependencies available
uv run python -c "import ulid; import aiofiles; from fastapi import FastAPI"
```

## Test Scenario 1: Basic Event Capture

**Goal**: Verify simulation emits events to JSONL file

**Steps**:

1. Create minimal simulation config (`test_sim.yaml`):
```yaml
simulation:
  name: event-stream-test
  turns: 5
  checkpoint_interval: 999  # Disable checkpoints for clarity

agents:
  - name: agent_alpha
    initial_state:
      wealth: 1000

global_state:
  turn: 0

engine:
  type: simple_economic

validator:
  type: basic
```

2. Run simulation with default (ACTION) verbosity:
```bash
uv run python -m llm_sim.cli run test_sim.yaml --verbosity ACTION
```

3. **Verify**: Events file created
```bash
export SIM_ID=$(ls -t output/ | head -1)
ls -lh output/$SIM_ID/events.jsonl
# Expected: File exists, size >0
```

4. **Verify**: Events are valid JSONL
```bash
uv run python -c "
import json
with open('output/$SIM_ID/events.jsonl') as f:
    for i, line in enumerate(f):
        event = json.loads(line)
        assert 'event_id' in event, f'Line {i} missing event_id'
        assert 'timestamp' in event, f'Line {i} missing timestamp'
        assert 'event_type' in event, f'Line {i} missing event_type'
print(f'✅ All {i+1} events valid')
"
```

5. **Verify**: MILESTONE events present
```bash
uv run python -c "
import json
events = []
with open('output/$SIM_ID/events.jsonl') as f:
    events = [json.loads(line) for line in f]

milestones = [e for e in events if e['event_type'] == 'MILESTONE']
assert len(milestones) >= 10, f'Expected >=10 MILESTONE events (turn_start + turn_end × 5 turns), got {len(milestones)}'
print(f'✅ Found {len(milestones)} MILESTONE events')
"
```

## Test Scenario 2: Verbosity Level Filtering

**Goal**: Verify different verbosity levels capture correct event types

**Steps**:

1. Run simulation with MILESTONE verbosity:
```bash
uv run python -m llm_sim.cli run test_sim.yaml --verbosity MILESTONE --output-dir output/milestone-test
export SIM_MILESTONE=$(ls -t output/milestone-test | head -1)
```

2. Run simulation with DETAIL verbosity:
```bash
uv run python -m llm_sim.cli run test_sim.yaml --verbosity DETAIL --output-dir output/detail-test
export SIM_DETAIL=$(ls -t output/detail-test | head -1)
```

3. **Verify**: MILESTONE run has only MILESTONE events
```bash
uv run python -c "
import json
with open('output/milestone-test/$SIM_MILESTONE/events.jsonl') as f:
    events = [json.loads(line) for line in f]

non_milestone = [e for e in events if e['event_type'] != 'MILESTONE']
assert len(non_milestone) == 0, f'MILESTONE verbosity should only have MILESTONE events, found: {[e[\"event_type\"] for e in non_milestone]}'
print(f'✅ MILESTONE verbosity: {len(events)} MILESTONE events only')
"
```

4. **Verify**: DETAIL run has more events than MILESTONE
```bash
uv run python -c "
import json
with open('output/milestone-test/$SIM_MILESTONE/events.jsonl') as f:
    milestone_count = sum(1 for _ in f)
with open('output/detail-test/$SIM_DETAIL/events.jsonl') as f:
    detail_count = sum(1 for _ in f)

assert detail_count > milestone_count, f'DETAIL verbosity ({detail_count}) should capture more events than MILESTONE ({milestone_count})'
print(f'✅ DETAIL verbosity: {detail_count} events (MILESTONE: {milestone_count})')
"
```

## Test Scenario 3: File Rotation

**Goal**: Verify event files rotate at 500MB

**Steps**:

1. Generate large simulation (or mock large event stream):
```bash
# Option A: Long simulation
uv run python -m llm_sim.cli run test_sim.yaml --turns 10000 --verbosity DETAIL

# Option B: Mock rotation test (faster)
uv run python -c "
import json
from pathlib import Path
from datetime import datetime, timezone
from ulid import ULID

output_dir = Path('output/rotation-test')
output_dir.mkdir(exist_ok=True, parents=True)
event_file = output_dir / 'events.jsonl'

# Write events until rotation triggers (500MB)
event_count = 0
file_size = 0
while file_size < 500 * 1024 * 1024:  # 500MB
    event = {
        'event_id': str(ULID()),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'turn_number': event_count // 100,
        'event_type': 'DETAIL',
        'simulation_id': 'rotation-test',
        'description': 'x' * 1000,  # Padding to reach size faster
        'details': {'calculation_type': 'test', 'intermediate_values': {f'key_{i}': i for i in range(50)}}
    }
    line = json.dumps(event) + '\n'
    with open(event_file, 'a') as f:
        f.write(line)
    file_size += len(line.encode())
    event_count += 1
    if event_count % 1000 == 0:
        print(f'Written {event_count} events, size: {file_size / 1024 / 1024:.1f}MB')

print(f'✅ Generated {event_count} events, total size: {file_size / 1024 / 1024:.1f}MB')
"
```

2. **Verify**: Rotated files created
```bash
ls -lh output/rotation-test/events*.jsonl
# Expected: Multiple files (events.jsonl, events_YYYY-MM-DD_HH-MM-SS.jsonl, ...)
```

3. **Verify**: Each rotated file < 500MB
```bash
uv run python -c "
from pathlib import Path
files = sorted(Path('output/rotation-test').glob('events*.jsonl'))
for f in files:
    size_mb = f.stat().st_size / 1024 / 1024
    assert size_mb <= 505, f'{f.name} exceeds 500MB: {size_mb:.1f}MB'  # 5MB tolerance for rotation overhead
    print(f'{f.name}: {size_mb:.1f}MB ✅')
"
```

## Test Scenario 4: API Query & Filtering

**Goal**: Verify API server serves events with filtering

**Steps**:

1. Start API server in background:
```bash
uv run python -m llm_sim.api.server --port 8000 &
API_PID=$!
sleep 2  # Wait for server startup
```

2. **Verify**: Server is running
```bash
curl -s http://localhost:8000/simulations | jq .
# Expected: JSON array of simulations
```

3. **Verify**: Get events for specific simulation
```bash
SIM_ID=$(ls -t output/ | head -1)
curl -s "http://localhost:8000/simulations/$SIM_ID/events?limit=10" | jq '.events | length'
# Expected: 10 (or fewer if <10 events total)
```

4. **Verify**: Filter by event_type
```bash
curl -s "http://localhost:8000/simulations/$SIM_ID/events?event_types=MILESTONE&limit=100" | jq '.events[] | .event_type' | sort | uniq
# Expected: Only "MILESTONE"
```

5. **Verify**: Filter by turn range
```bash
curl -s "http://localhost:8000/simulations/$SIM_ID/events?turn_start=2&turn_end=3&limit=100" | jq '.events[] | .turn_number' | sort | uniq
# Expected: Only 2 and 3
```

6. **Verify**: Get single event by ID
```bash
EVENT_ID=$(curl -s "http://localhost:8000/simulations/$SIM_ID/events?limit=1" | jq -r '.events[0].event_id')
curl -s "http://localhost:8000/simulations/$SIM_ID/events/$EVENT_ID" | jq '.event_id'
# Expected: Same EVENT_ID
```

7. **Verify**: Causality chain endpoint
```bash
curl -s "http://localhost:8000/simulations/$SIM_ID/causality/$EVENT_ID" | jq '.upstream | length'
# Expected: >= 0 (number of parent events)
```

8. Cleanup:
```bash
kill $API_PID
```

## Test Scenario 5: Event Integrity & Causality

**Goal**: Verify caused_by references form valid causality graph

**Steps**:

1. Run simulation that generates causality:
```bash
uv run python -m llm_sim.cli run test_sim.yaml --turns 3 --verbosity ACTION
export SIM_ID=$(ls -t output/ | head -1)
```

2. **Verify**: All caused_by event_ids exist
```bash
uv run python -c "
import json
from pathlib import Path

events_file = Path('output/$SIM_ID/events.jsonl')
events = []
with open(events_file) as f:
    events = [json.loads(line) for line in f]

event_ids = {e['event_id'] for e in events}
missing_refs = []

for event in events:
    if 'caused_by' in event and event['caused_by']:
        for parent_id in event['caused_by']:
            if parent_id not in event_ids:
                missing_refs.append((event['event_id'], parent_id))

if missing_refs:
    print(f'❌ Found {len(missing_refs)} missing causality references:')
    for child_id, parent_id in missing_refs[:5]:
        print(f'  Event {child_id} references missing parent {parent_id}')
else:
    print(f'✅ All causality references valid ({len(events)} events checked)')
"
```

3. **Verify**: No cyclic causality (simple check)
```bash
uv run python -c "
import json
from pathlib import Path

events_file = Path('output/$SIM_ID/events.jsonl')
events = []
with open(events_file) as f:
    events = [json.loads(line) for line in f]

# Build causality graph
graph = {e['event_id']: e.get('caused_by', []) for e in events}

# Simple cycle detection: check if any event references itself in caused_by chain
def has_cycle(event_id, visited=None):
    if visited is None:
        visited = set()
    if event_id in visited:
        return True
    visited.add(event_id)
    for parent_id in graph.get(event_id, []):
        if has_cycle(parent_id, visited.copy()):
            return True
    return False

cycles = [eid for eid in graph if has_cycle(eid)]
if cycles:
    print(f'❌ Found {len(cycles)} events with cyclic causality: {cycles[:5]}')
else:
    print(f'✅ No cyclic causality detected ({len(events)} events)')
"
```

## Success Criteria

All test scenarios must pass:

- ✅ **Scenario 1**: Events file created, valid JSONL, MILESTONE events present
- ✅ **Scenario 2**: MILESTONE verbosity excludes other types; DETAIL captures more events
- ✅ **Scenario 3**: File rotation creates multiple files, each < 500MB
- ✅ **Scenario 4**: API returns filtered events, pagination works, causality endpoint responds
- ✅ **Scenario 5**: All caused_by references valid, no cycles

## Troubleshooting

**Issue**: No events.jsonl file created
- Check: Orchestrator initialized EventWriter correctly
- Check: `--verbosity` flag recognized by CLI
- Check: Output directory permissions

**Issue**: API server 404 for /simulations/{sim_id}/events
- Check: Event files exist in output/{sim_id}/
- Check: Simulation ID matches directory name exactly
- Check: API server output directory matches simulation output directory

**Issue**: Large file not rotating
- Check: EventWriter rotation logic triggers at 500MB
- Check: File size calculation includes all rotated files
- Check: Write permissions for creating new timestamped files

**Issue**: caused_by references missing events
- Check: Events written atomically (no partial writes during crash)
- Check: Event emission order (parents before children)
- Check: Causality tracking logic in EventBuilder

---

**Quickstart Status**: ✅ READY (Execute after Phase 4 implementation)
