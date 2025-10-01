# Research: Persistent Simulation State Storage

**Feature**: 006-persistent-storage-specifically
**Date**: 2025-10-01

## Research Questions

### 1. JSON Serialization Strategy for SimulationState

**Question**: How should we serialize Pydantic models to JSON for checkpoint files?

**Decision**: Use Pydantic's built-in `.model_dump_json()` and `.model_validate_json()` methods

**Rationale**:
- SimulationState is already a Pydantic v2 model
- Pydantic provides automatic JSON serialization with type validation
- Handles nested models (AgentState, GlobalState) automatically
- Built-in datetime serialization (ISO 8601 format)
- Validation on deserialization ensures data integrity

**Alternatives Considered**:
- **Custom JSON encoder**: Rejected - adds unnecessary complexity, duplicates Pydantic functionality
- **Pickle format**: Rejected - not human-readable, version fragile, security risks
- **MessagePack**: Rejected - binary format not required, loses human readability advantage

**Implementation Pattern**:
```python
# Save
json_str = state.model_dump_json(indent=2)
path.write_text(json_str)

# Load
json_str = path.read_text()
state = SimulationState.model_validate_json(json_str)
```

---

### 2. Atomic File Write Pattern

**Question**: How to prevent checkpoint file corruption during interrupted writes?

**Decision**: Use temporary file + atomic rename pattern

**Rationale**:
- Standard Unix pattern for atomic file updates
- Prevents partial writes from being read as valid checkpoints
- `os.rename()` is atomic on POSIX systems (Linux, macOS)
- Explicit `fsync()` ensures data reaches disk before rename
- Temporary file can be cleaned up on next run if orphaned

**Alternatives Considered**:
- **Direct write**: Rejected - not atomic, corruption on interrupt/crash
- **File locking (fcntl)**: Rejected - adds complexity, not needed for single-writer scenario
- **Write-ahead logging**: Rejected - overkill for this use case

**Implementation Pattern**:
```python
def atomic_write(path: Path, content: str) -> None:
    temp_path = path.with_suffix('.tmp')
    with open(temp_path, 'w') as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())  # Ensure written to disk
    temp_path.rename(path)  # Atomic on POSIX
```

**Platform Considerations**:
- POSIX (Linux/macOS): Fully atomic
- Windows: `replace()` method should be used instead of `rename()` for atomicity across platforms
- Solution: Use `Path.replace()` instead of `Path.rename()` (works atomically on both)

---

### 3. Run ID Collision Detection

**Question**: How to ensure unique run IDs when simulations start in the same second?

**Decision**: Check filesystem for existing directory, increment sequence number

**Rationale**:
- Simple and reliable
- Works across process restarts (no in-memory state needed)
- Filesystem is source of truth for collision detection
- Sequence number approach chosen per clarification (vs. milliseconds)
- Two-digit zero-padding supports 99 concurrent starts per second

**Alternatives Considered**:
- **Millisecond precision**: Rejected - clarification explicitly chose sequence numbers
- **UUID suffix**: Rejected - loses human-readable ID structure
- **Lock file**: Rejected - adds complexity, requires cleanup on crash
- **Database**: Rejected - overkill, introduces external dependency

**Implementation Pattern**:
```python
def generate_unique_run_id(base: str, output_dir: Path) -> str:
    """Generate unique run ID by incrementing sequence number."""
    seq = 1
    while (output_dir / f"{base}_{seq:02d}").exists():
        seq += 1
        if seq > 99:
            raise RunIDCollisionError("Too many concurrent runs")
    return f"{base}_{seq:02d}"
```

**Edge Cases**:
- Race condition: Two processes check simultaneously
  - Acceptable: Rare, worst case one fails with clear error on mkdir
- Orphaned directories: Previous run crashed, dir exists
  - Acceptable: Sequence increments, old dir preserved for debugging
- Sequence overflow (>99): Raise error, user waits 1 second

---

### 4. Checkpoint Interval Configuration

**Question**: How should users specify checkpoint intervals in simulation config?

**Decision**: Add `checkpoint_interval` field to `simulation` section of YAML config

**Rationale**:
- Aligns with existing config structure (simulation, agents, engine, validator)
- Optional field (null/omitted = no interval checkpoints, only last/final)
- YAML is already parsed by Pydantic, type validation built-in
- Per-simulation control (different configs can have different intervals)

**Alternatives Considered**:
- **CLI flag**: Rejected - YAML config is primary interface, CLI override could be added later
- **Separate config file**: Rejected - unnecessary file proliferation
- **Engine-level config**: Rejected - checkpointing is orchestrator concern, not engine

**Schema Extension**:
```yaml
simulation:
  name: "EconomicTest"
  max_turns: 100
  checkpoint_interval: 10  # Optional: save every N turns (null = disabled)
  termination:
    max_value: 10000
    min_value: 0
```

**Validation Rules**:
- Type: `int | None`
- Constraint: If provided, must be positive integer (>= 1)
- Semantic: If >= max_turns, equivalent to disabled (only final saved)

---

### 5. Error Handling Strategy

**Question**: What exceptions should be raised and how should errors propagate?

**Decision**: Custom exception hierarchy + fail-fast approach

**Rationale**:
- Clear error messages for debugging (per FR-020)
- Predictable behavior (no silent failures)
- Allows graceful shutdown (save partial results before exit)
- Type-safe exception handling in calling code

**Exception Hierarchy**:
```python
class CheckpointError(Exception):
    """Base exception for checkpoint operations."""
    pass

class CheckpointSaveError(CheckpointError):
    """Raised when checkpoint save fails (I/O, disk space, permissions)."""
    pass

class CheckpointLoadError(CheckpointError):
    """Raised when checkpoint load fails (missing, corrupted, schema mismatch)."""
    pass

class RunIDCollisionError(CheckpointError):
    """Raised when run ID collision cannot be resolved."""
    pass
```

**Error Propagation**:
1. Low-level I/O errors (PermissionError, OSError) → Convert to CheckpointSaveError
2. JSON decode errors (JSONDecodeError) → Convert to CheckpointLoadError
3. Pydantic validation errors (ValidationError) → Convert to CheckpointLoadError
4. All CheckpointError subclasses → Bubble up to orchestrator
5. Orchestrator → Catches, logs, halts simulation with exit code 1

**Error Messages**:
- Include context: file path, turn number, original error
- Example: `CheckpointSaveError: Failed to save checkpoint at turn 15 to 'output/run_01/checkpoints/turn_15.json': Disk quota exceeded`

---

### 6. Directory Creation Safety

**Question**: How to safely create output directories with proper error handling?

**Decision**: Use `Path.mkdir(parents=True, exist_ok=True)`

**Rationale**:
- `parents=True`: Creates parent directories as needed (per clarification A)
- `exist_ok=True`: Idempotent, doesn't fail if directory already exists
- Handles race conditions (another process creates dir between check and create)
- Raises PermissionError if insufficient permissions

**Alternatives Considered**:
- **Check then create**: Rejected - race condition (TOCTOU issue)
- **try/except on exist**: Rejected - `exist_ok=True` handles this cleanly

**Implementation Pattern**:
```python
def ensure_output_directory(run_id: str, output_root: Path = Path("output")) -> Path:
    """Create output directory structure for run."""
    run_dir = output_root / run_id
    checkpoints_dir = run_dir / "checkpoints"

    try:
        checkpoints_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise CheckpointSaveError(
            f"Permission denied creating directory '{checkpoints_dir}': {e}"
        )

    return run_dir
```

**Directory Structure**:
```
output/                          # Created automatically
└── {run_id}/                    # Created by ensure_output_directory
    ├── checkpoints/             # Created with parents=True
    │   ├── turn_5.json
    │   ├── turn_10.json
    │   └── turn_15.json
    └── result.json              # Created by save_results
```

---

## Technology Stack Summary

**No new dependencies required** - all functionality can be implemented with Python standard library + existing dependencies:

| Capability | Technology | Status |
|------------|-----------|---------|
| Data modeling | Pydantic 2.x | Existing |
| JSON serialization | Pydantic + json module | Existing |
| File I/O | pathlib + open() | Standard lib |
| Atomic writes | os.rename() / Path.replace() | Standard lib |
| Datetime handling | datetime | Standard lib |
| Error handling | Custom exceptions | Standard lib |
| Logging | structlog 24.x | Existing |
| Testing | pytest | Existing |

**Configuration**: Extends existing PyYAML-based config, no new config format needed.

---

## Implementation Risks & Mitigations

### Risk 1: Large Checkpoint Files
**Concern**: Checkpoints could grow large with many agents
**Mitigation**:
- JSON compression optional future enhancement
- For now, fail fast if save takes >10s (timeout)
- Document size expectations in user guide

### Risk 2: Platform Differences (Windows vs. Unix)
**Concern**: Atomic rename behavior differs on Windows
**Mitigation**: Use `Path.replace()` instead of `Path.rename()` (atomic on both platforms)

### Risk 3: State Model Evolution
**Concern**: Checkpoints from old code versions may not load in new versions
**Mitigation**:
- Phase 1: Accept incompatibility (deferred clarification)
- Future: Add schema version field, migration logic
- Document breaking changes in release notes

---

## Research Conclusions

All technical unknowns resolved. Ready to proceed to Phase 1 (Design & Contracts) with:
- ✅ Serialization strategy (Pydantic JSON)
- ✅ File safety (atomic writes)
- ✅ Collision detection (sequence numbers)
- ✅ Configuration approach (YAML extension)
- ✅ Error handling (custom exceptions + fail-fast)
- ✅ Directory management (mkdir with parents)

No new dependencies needed. Implementation can begin after Phase 1 contracts are defined.
