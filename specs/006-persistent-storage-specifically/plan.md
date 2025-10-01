# Implementation Plan: Persistent Simulation State Storage

**Branch**: `006-persistent-storage-specifically` | **Date**: 2025-10-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-persistent-storage-specifically/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path ✓
2. Fill Technical Context (scan for NEEDS CLARIFICATION) ✓
3. Fill Constitution Check section ✓
4. Evaluate Constitution Check ✓
5. Execute Phase 0 → research.md (in progress)
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
7. Re-evaluate Constitution Check
8. Plan Phase 2 → Describe task generation approach
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 8. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

This feature adds persistent state storage to the simulation framework, enabling:
- **Checkpoint saving** at configurable intervals (every N turns)
- **State resumption** from any saved checkpoint
- **Unique run identification** with collision-free naming scheme
- **Organized output** in per-run subdirectories

Technical approach: Extend existing `SimulationOrchestrator` with checkpoint manager, add Pydantic models for serialization, implement file-based storage with JSON format.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Pydantic 2.x (serialization), PyYAML 6.x (config), structlog 24.x (logging)
**Storage**: File system (JSON files in `output/` directory)
**Testing**: pytest (contract, integration, unit tests)
**Target Platform**: Linux/macOS/Windows (cross-platform file operations)
**Project Type**: single (Python library with CLI)
**Performance Goals**: Checkpoint save <1s for typical simulation state, resume load <500ms
**Constraints**: Fail-fast on I/O errors, no silent data loss, atomic file writes
**Scale/Scope**: Support 100+ agents, 1000+ turns, 10MB+ checkpoint files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution template is not populated with specific rules. Applying standard software engineering principles:

✅ **Modularity**: Checkpoint functionality will be encapsulated in dedicated module (`persistence.py`)
✅ **Testability**: All public methods will have contract tests, TDD approach required
✅ **Error Handling**: Explicit error messages for all failure modes (per FR-020)
✅ **Documentation**: Inline docstrings + quickstart guide for usage
✅ **No Breaking Changes**: Extends existing orchestrator, doesn't modify current behavior

**Initial Assessment**: PASS - No constitutional violations detected

## Project Structure

### Documentation (this feature)
```
specs/006-persistent-storage-specifically/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
src/llm_sim/
├── models/
│   ├── checkpoint.py          # NEW: Checkpoint, RunMetadata models
│   └── state.py               # EXISTING: SimulationState (may need extension)
├── persistence/               # NEW: Checkpoint management
│   ├── __init__.py
│   ├── checkpoint_manager.py  # Save/load checkpoint logic
│   ├── run_id_generator.py    # Unique run ID generation
│   └── storage.py             # File I/O operations
├── orchestrator.py            # MODIFIED: Add checkpoint integration
└── models/
    └── config.py              # MODIFIED: Add checkpoint config fields

tests/
├── contract/
│   ├── test_checkpoint_manager_contract.py    # NEW
│   ├── test_run_id_generator_contract.py      # NEW
│   └── test_storage_contract.py               # NEW
├── integration/
│   ├── test_checkpoint_save_resume.py         # NEW
│   └── test_run_id_uniqueness.py              # NEW
└── unit/
    ├── test_checkpoint_models.py              # NEW
    └── test_file_operations.py                # NEW

output/                        # NEW: Created by system (gitignored)
└── {run_id}/
    ├── checkpoints/
    │   └── turn_{N}.json
    └── result.json
```

**Structure Decision**: Single project structure. This is a core library feature extending the existing `llm_sim` package. New `persistence/` module will handle all checkpoint-related functionality. Output directory will be created at project root (outside `src/`).

## Phase 0: Outline & Research

**Unknowns from Technical Context**: None - all technologies are already in use in the project.

**Research Tasks**:

### 1. JSON Serialization Strategy for SimulationState
- **Decision**: Use Pydantic's built-in `.model_dump_json()` and `.model_validate_json()`
- **Rationale**: SimulationState is already a Pydantic model, provides automatic serialization with validation
- **Alternatives Considered**:
  - Custom JSON encoder: rejected (unnecessary complexity)
  - Pickle: rejected (not human-readable, version fragility)

### 2. Atomic File Write Pattern
- **Decision**: Write to temp file + atomic rename
- **Rationale**: Prevents corruption on interrupted writes, standard Unix pattern
- **Pattern**:
  ```python
  temp_path = f"{target_path}.tmp"
  with open(temp_path, 'w') as f:
      f.write(data)
      f.flush()
      os.fsync(f.fileno())
  os.rename(temp_path, target_path)  # Atomic on POSIX
  ```
- **Alternatives Considered**:
  - Direct write: rejected (not atomic)
  - File locking: rejected (adds complexity, not needed for single-writer)

### 3. Run ID Collision Detection
- **Decision**: Check filesystem for existing directory, increment sequence number
- **Rationale**: Simple, reliable, works across process restarts
- **Pattern**:
  ```python
  base_id = f"{name}_{agents}agents_{date}_{time}"
  seq = 1
  while Path(f"output/{base_id}_{seq:02d}").exists():
      seq += 1
  return f"{base_id}_{seq:02d}"
  ```
- **Alternatives Considered**:
  - Database/lock file: rejected (overkill for this use case)
  - Milliseconds in timestamp: rejected (clarification chose sequence numbers)

### 4. Checkpoint Interval Configuration
- **Decision**: Add `checkpoint_interval` field to SimulationConfig
- **Rationale**: Aligns with existing YAML config pattern
- **Schema Addition**:
  ```yaml
  simulation:
    name: "EconomicTest"
    max_turns: 100
    checkpoint_interval: 10  # Save every 10 turns (optional, null = no interval checkpoints)
  ```
- **Validation**: Must be positive integer if provided, null/omitted disables interval saves

### 5. Error Handling Strategy
- **Decision**: Custom exception hierarchy + fail-fast
- **Rationale**: Clear error messages, predictable behavior (per FR-020)
- **Exceptions**:
  - `CheckpointSaveError`: Raised on any save failure
  - `CheckpointLoadError`: Raised on load/corruption
  - `RunIDCollisionError`: Raised if collision detection fails
- **All bubble up to orchestrator, halt simulation**

### 6. Directory Creation Safety
- **Decision**: Use `Path.mkdir(parents=True, exist_ok=True)`
- **Rationale**: Handles missing parents, idempotent (per clarification A)
- **Error Handling**: Catch `PermissionError` and convert to CheckpointSaveError

**Output**: research.md (see above - consolidated inline)

## Phase 1: Design & Contracts

### Data Model (data-model.md to be generated)

**Entities**:

1. **RunMetadata** (NEW Pydantic model)
   - `run_id: str` - Unique identifier
   - `simulation_name: str` - From config
   - `num_agents: int` - Agent count
   - `start_time: datetime` - Simulation start
   - `end_time: datetime | None` - Simulation end (null if incomplete)
   - `checkpoint_interval: int | None` - Config value
   - `config_snapshot: dict` - Full config for validation

2. **Checkpoint** (NEW Pydantic model)
   - `turn: int` - Turn number when saved
   - `checkpoint_type: Literal["interval", "last", "final"]` - Type classification
   - `state: SimulationState` - Complete state snapshot
   - `timestamp: datetime` - When checkpoint was created

3. **SimulationResults** (NEW Pydantic model)
   - `run_metadata: RunMetadata` - Run identification
   - `final_state: SimulationState` - Last turn state
   - `checkpoints: list[int]` - List of saved turn numbers
   - `summary_stats: dict` - Statistics (defined during implementation per deferred clarification)

4. **SimulationState** (EXISTING - may need minor extension)
   - Already contains: `turn`, `agents`, `global_state`
   - Verify: All fields are JSON-serializable via Pydantic

**Relationships**:
- RunMetadata 1:N Checkpoint (one run has many checkpoints)
- RunMetadata 1:1 SimulationResults (one run has one result file)

### API Contracts (contracts/ to be generated)

**CheckpointManager Interface**:
```python
class CheckpointManager:
    def __init__(self, run_id: str, checkpoint_interval: int | None): ...
    def should_save_checkpoint(self, turn: int, is_final: bool) -> bool: ...
    def save_checkpoint(self, state: SimulationState, checkpoint_type: str) -> Path: ...
    def load_checkpoint(self, run_id: str, turn: int) -> SimulationState: ...
    def list_checkpoints(self, run_id: str) -> list[int]: ...
    def save_results(self, results: SimulationResults) -> Path: ...
```

**RunIDGenerator Interface**:
```python
class RunIDGenerator:
    @staticmethod
    def generate(simulation_name: str, num_agents: int, start_time: datetime) -> str: ...
```

**StorageBackend Interface**:
```python
class JSONStorage:
    def save_json(self, path: Path, data: BaseModel) -> None: ...
    def load_json(self, path: Path, model: Type[T]) -> T: ...
    def ensure_directory(self, path: Path) -> None: ...
```

### Contract Tests (to be generated in contracts/)

1. **test_checkpoint_manager_contract.py**
   - Test `should_save_checkpoint` returns True at correct intervals
   - Test `save_checkpoint` creates file at expected path
   - Test `save_checkpoint` raises CheckpointSaveError on disk full
   - Test `load_checkpoint` returns correct state
   - Test `load_checkpoint` raises CheckpointLoadError on missing file

2. **test_run_id_generator_contract.py**
   - Test format matches `{name}_{N}agents_{YYYYMMDD}_{HHMMSS}_{seq}`
   - Test sequence increments on collision
   - Test handles special characters in simulation name

3. **test_storage_contract.py**
   - Test atomic write (temp file + rename)
   - Test directory creation with parents
   - Test error handling for permission denied

### Integration Test Scenarios (quickstart.md to include)

1. **Full simulation with checkpoints**
   - Run 15-turn simulation with interval=5
   - Verify checkpoints at turns 5, 10, 15 (final)
   - Verify result.json contains checkpoint list

2. **Resume from checkpoint**
   - Save checkpoint at turn 10
   - Load and resume simulation
   - Verify continues from turn 11

3. **Unique run IDs**
   - Start two simulations in same second
   - Verify different run IDs (sequence incremented)

4. **Failure scenarios**
   - Simulate disk full during save
   - Verify simulation halts with error message

### Agent File Update

Will run: `.specify/scripts/bash/update-agent-context.sh claude`

**Technologies to add**:
- Python 3.12 (already present)
- Pydantic 2.x (already present)
- File system operations (pathlib)

**Commands to add**:
- None (existing test commands sufficient)

**Recent changes**:
- 006-persistent-storage-specifically: Added checkpoint persistence, run ID generation, JSON storage

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

1. **From contracts** (9 contract test tasks):
   - T001-T003: CheckpointManager contract tests [P]
   - T004-T006: RunIDGenerator contract tests [P]
   - T007-T009: StorageBackend contract tests [P]

2. **From data model** (4 model tasks):
   - T010: Create RunMetadata model [P]
   - T011: Create Checkpoint model [P]
   - T012: Create SimulationResults model [P]
   - T013: Verify SimulationState serialization

3. **Core implementation** (6 sequential tasks):
   - T014: Implement JSONStorage (atomic writes, directory creation)
   - T015: Implement RunIDGenerator (format, collision detection)
   - T016: Implement CheckpointManager (save/load logic)
   - T017: Extend SimulationConfig (add checkpoint_interval field)
   - T018: Integrate CheckpointManager into Orchestrator
   - T019: Add resume_from parameter to Orchestrator

4. **From user stories** (4 integration test tasks):
   - T020: Test full simulation with interval checkpoints
   - T021: Test resume from checkpoint
   - T022: Test run ID uniqueness
   - T023: Test failure handling (disk full simulation)

5. **Documentation** (2 tasks):
   - T024: Update quickstart.md examples
   - T025: Update CLAUDE.md context

**Ordering Strategy**:
- **TDD**: Contract tests (T001-T009) → Models (T010-T013) → Implementation (T014-T019)
- **Dependencies**: Storage → RunID → CheckpointManager → Orchestrator integration
- **Parallel**: Contract tests can run in parallel [P], models can run in parallel [P]

**Estimated Output**: 25 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation

*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following TDD principles)
**Phase 5**: Validation (run tests, execute quickstart.md scenarios, verify checkpoint files)

## Complexity Tracking

*No constitutional violations detected - table not needed*

## Progress Tracking

*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved (5 critical resolved, 7 deferred to implementation)
- [x] Complexity deviations documented (none)

**Artifacts Generated**:
- [x] research.md - Technical decisions and patterns
- [x] data-model.md - Entity definitions and relationships
- [x] contracts/checkpoint_manager_contract.md - CheckpointManager interface
- [x] contracts/run_id_generator_contract.md - RunIDGenerator interface
- [x] contracts/storage_contract.md - JSONStorage interface
- [x] quickstart.md - Integration test scenarios and user guide
- [x] CLAUDE.md - Updated with feature context

---
*Based on Constitution v[TEMPLATE] - See `.specify/memory/constitution.md`*
