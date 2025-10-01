# Tasks: Persistent Simulation State Storage

**Input**: Design documents from `/specs/006-persistent-storage-specifically/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
2. Load design documents ✓
   → data-model.md: 3 new entities (RunMetadata, Checkpoint, SimulationResults)
   → contracts/: 3 contracts (CheckpointManager, RunIDGenerator, JSONStorage)
   → research.md: 6 technical decisions
3. Generate tasks by category ✓
4. Apply TDD ordering ✓
5. Number tasks sequentially ✓
6. Mark parallel execution [P] ✓
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
Single project structure:
- Source: `src/llm_sim/`
- Tests: `tests/contract/`, `tests/integration/`, `tests/unit/`
- Output: `output/` (created by system)

---

## Phase 3.1: Setup

- [ ] **T001** Create persistence module directory structure
  - Create `src/llm_sim/persistence/__init__.py`
  - Create `src/llm_sim/models/checkpoint.py` (empty placeholder)
  - Create `output/` directory at project root (if not exists)
  - Add `output/` to `.gitignore`

- [ ] **T002** Add checkpoint interval field to SimulationConfig
  - Modify `src/llm_sim/models/config.py`
  - Add `checkpoint_interval: int | None = None` to simulation section
  - Add validation: must be positive integer if provided
  - Ensure field is parsed from YAML configs

- [ ] **T003** [P] Create custom exception classes
  - Create `src/llm_sim/persistence/exceptions.py`
  - Define `CheckpointError(Exception)` base class
  - Define `CheckpointSaveError(CheckpointError)`
  - Define `CheckpointLoadError(CheckpointError)`
  - Define `RunIDCollisionError(CheckpointError)`
  - Each with descriptive docstrings

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (Parallel - Different Files)

- [ ] **T004** [P] Contract test for JSONStorage in `tests/contract/test_storage_contract.py`
  - Test `save_json()` uses atomic write pattern (temp + rename)
  - Test `load_json()` returns validated Pydantic model
  - Test `load_json()` raises CheckpointLoadError on missing file
  - Test `load_json()` raises CheckpointLoadError on invalid JSON
  - Test `load_json()` raises CheckpointLoadError on schema mismatch
  - Test `ensure_directory()` creates parents
  - Test `ensure_directory()` is idempotent
  - Test `ensure_directory()` raises CheckpointSaveError on permission denied
  - Tests MUST fail (no implementation yet)

- [ ] **T005** [P] Contract test for RunIDGenerator in `tests/contract/test_run_id_generator_contract.py`
  - Test `generate()` format matches `{name}_{N}agents_{YYYYMMDD}_{HHMMSS}_{seq}`
  - Test sequence increments when directory exists (collision detection)
  - Test handles special characters in simulation name (sanitization)
  - Test raises RunIDCollisionError when sequence exceeds 99
  - Tests MUST fail (no implementation yet)

- [ ] **T006** [P] Contract test for CheckpointManager in `tests/contract/test_checkpoint_manager_contract.py`
  - Test `should_save_checkpoint()` returns True at intervals
  - Test `should_save_checkpoint()` always True for final turn
  - Test `should_save_checkpoint()` respects disabled interval (None)
  - Test `save_checkpoint()` creates file at correct path
  - Test `save_checkpoint()` validates content round-trip (save/load)
  - Test `save_checkpoint()` raises CheckpointSaveError on I/O failure
  - Test `load_checkpoint()` returns SimulationState
  - Test `load_checkpoint()` raises CheckpointLoadError on missing file
  - Test `load_checkpoint()` raises CheckpointLoadError on corrupted file
  - Test `list_checkpoints()` returns sorted list of available turns
  - Test `save_results()` creates result.json file
  - Tests MUST fail (no implementation yet)

### Integration Tests (Parallel - Different Files)

- [ ] **T007** [P] Integration test for full simulation with checkpoints in `tests/integration/test_checkpoint_save_resume.py`
  - Test: Run 15-turn simulation with checkpoint_interval=5
  - Assert: Checkpoint files exist at turns 5, 10, 15
  - Assert: result.json exists with checkpoint list
  - Test: Load checkpoint at turn 10 and resume
  - Assert: Simulation continues from turn 11
  - Assert: Final state matches as if run continuously
  - Test MUST fail (orchestrator integration not implemented)

- [ ] **T008** [P] Integration test for run ID uniqueness in `tests/integration/test_run_id_uniqueness.py`
  - Test: Create two simulations with same config in same second (mock time)
  - Assert: Different run IDs (sequence incremented)
  - Assert: Both output directories exist
  - Test MUST fail (run ID generation not integrated)

- [ ] **T009** [P] Integration test for checkpoint failure handling in `tests/integration/test_checkpoint_failures.py`
  - Test: Simulate disk full during save (mock write_text)
  - Assert: CheckpointSaveError raised
  - Assert: Simulation halts with exit code 1
  - Test: Corrupt checkpoint file, attempt resume
  - Assert: CheckpointLoadError raised with clear message
  - Tests MUST fail (error handling not implemented)

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Data Models (Parallel - Different Classes)

- [ ] **T010** [P] Create RunMetadata model in `src/llm_sim/models/checkpoint.py`
  - Define Pydantic model with all fields from data-model.md
  - Fields: run_id, simulation_name, num_agents, start_time, end_time, checkpoint_interval, config_snapshot
  - Add Field validators (run_id format, positive num_agents)
  - Add docstrings for all fields
  - Verify JSON serialization with model_dump_json()

- [ ] **T011** [P] Create Checkpoint model in `src/llm_sim/models/checkpoint.py`
  - Define Pydantic model with all fields from data-model.md
  - Fields: turn, checkpoint_type (Literal["interval", "last", "final"]), state (SimulationState), timestamp
  - Add validator: turn must match state.turn
  - Add docstrings
  - Verify nested SimulationState serialization

- [ ] **T012** [P] Create SimulationResults model in `src/llm_sim/models/checkpoint.py`
  - Define Pydantic model with all fields from data-model.md
  - Fields: run_metadata (RunMetadata), final_state (SimulationState), checkpoints (list[int]), summary_stats (dict)
  - Add validator: checkpoints list must be sorted
  - Add validator: final_state.turn must match last checkpoint
  - Add docstrings

- [ ] **T013** Verify SimulationState JSON serialization in `src/llm_sim/models/state.py`
  - Add unit test: SimulationState round-trip (model_dump_json + model_validate_json)
  - Ensure all nested fields (AgentState, GlobalState) serialize correctly
  - Verify no circular references
  - Add test to `tests/unit/test_state_serialization.py`

### Storage Layer (Sequential - Builds on Each Other)

- [ ] **T014** Implement JSONStorage in `src/llm_sim/persistence/storage.py`
  - Implement `save_json(path, data)` with atomic write pattern:
    - Write to `{path}.tmp`
    - Call `f.flush()` and `os.fsync(f.fileno())`
    - Use `Path.replace()` for atomic rename (cross-platform)
  - Implement `load_json(path, model)` with error handling:
    - Catch FileNotFoundError → CheckpointLoadError
    - Catch JSONDecodeError → CheckpointLoadError
    - Catch ValidationError → CheckpointLoadError
  - Implement `ensure_directory(path)` with `mkdir(parents=True, exist_ok=True)`
  - Catch PermissionError → CheckpointSaveError
  - All contract tests should now pass

- [ ] **T015** Implement RunIDGenerator in `src/llm_sim/persistence/run_id_generator.py`
  - Implement `generate(simulation_name, num_agents, start_time, output_root)`
  - Format: `{name}_{N}agents_{YYYYMMDD}_{HHMMSS}_{seq}`
  - Sanitize simulation_name (replace `/` and spaces with `_`)
  - Collision detection: check if `output_root/{base}_{seq:02d}` exists
  - Increment sequence from 01 to 99
  - Raise RunIDCollisionError if all 99 sequences occupied
  - All contract tests should now pass

- [ ] **T016** Implement CheckpointManager in `src/llm_sim/persistence/checkpoint_manager.py`
  - Implement `__init__(run_id, checkpoint_interval, output_root)`
    - Store parameters, call ensure_directory for run subdirectory
  - Implement `should_save_checkpoint(turn, is_final)`
    - Return True if is_final
    - Return True if checkpoint_interval not None and turn % checkpoint_interval == 0
    - Return False otherwise
  - Implement `save_checkpoint(state, checkpoint_type)`
    - Create Checkpoint object with timestamp
    - Determine filename: `turn_{turn}.json` or `last.json`
    - Use JSONStorage.save_json() with full path
    - Return Path to saved file
  - Implement `load_checkpoint(run_id, turn)`
    - Build path to checkpoint file
    - Use JSONStorage.load_json(path, Checkpoint)
    - Return state from loaded checkpoint
  - Implement `list_checkpoints(run_id)`
    - Scan checkpoints directory for `turn_*.json` files
    - Parse turn numbers from filenames
    - Return sorted list
  - Implement `save_results(results)`
    - Use JSONStorage.save_json() to write result.json
    - Return path to result file
  - All contract tests should now pass

### Orchestrator Integration (Sequential - Modifies Shared File)

- [ ] **T017** Extend SimulationOrchestrator with checkpoint support in `src/llm_sim/orchestrator.py`
  - Add `from llm_sim.persistence.checkpoint_manager import CheckpointManager`
  - Add `from llm_sim.persistence.run_id_generator import RunIDGenerator`
  - In `__init__()`: Generate run_id using RunIDGenerator
  - In `__init__()`: Create CheckpointManager instance
  - In `__init__()`: Create RunMetadata object
  - In `run()` method after each turn:
    - Check `checkpoint_manager.should_save_checkpoint(turn, is_final)`
    - If True: Call `checkpoint_manager.save_checkpoint(state, type)`
    - Always save "last" checkpoint (overwrite each turn)
  - After simulation completes:
    - Create SimulationResults object
    - Call `checkpoint_manager.save_results(results)`
  - Wrap checkpoint saves in try/except, convert errors to CheckpointSaveError

- [ ] **T018** Add resume-from-checkpoint functionality to orchestrator in `src/llm_sim/orchestrator.py`
  - Add class method `from_checkpoint(run_id, turn, output_root)`
  - Load checkpoint using CheckpointManager.load_checkpoint()
  - Extract config_snapshot from checkpoint
  - Reconstruct SimulationConfig from config_snapshot
  - Initialize agents and engine from loaded state
  - Resume simulation from turn+1
  - Generate new run_id for resumed execution (sequence incremented)
  - Return orchestrator instance ready to continue

- [ ] **T019** Add CLI support for checkpoint resume in `main.py`
  - Add argparse options: `--resume-from RUN_ID`, `--resume-turn TURN`
  - If resume flags provided:
    - Use `SimulationOrchestrator.from_checkpoint()`
  - Else:
    - Use existing `SimulationOrchestrator.from_yaml()`
  - Handle errors with clear messages
  - Integration test T007 should now pass

---

## Phase 3.4: Integration & Polish

### Additional Tests (Parallel - Different Files)

- [ ] **T020** [P] Unit tests for data models in `tests/unit/test_checkpoint_models.py`
  - Test RunMetadata validation (positive num_agents, run_id format)
  - Test Checkpoint validation (turn matches state.turn)
  - Test SimulationResults validation (sorted checkpoints list)
  - Test all models round-trip JSON serialization
  - Test invalid data raises ValidationError

- [ ] **T021** [P] Unit tests for file operations in `tests/unit/test_file_operations.py`
  - Test atomic write pattern (verify temp file created then renamed)
  - Test fsync called before rename
  - Test directory creation edge cases (already exists, nested parents)
  - Test error conversion (PermissionError → CheckpointSaveError)

### Documentation & Polish (Parallel)

- [ ] **T022** [P] Add configuration examples to documentation
  - Update README.md or docs/ with checkpoint_interval examples
  - Add example YAML configs with checkpointing enabled
  - Document resume-from-checkpoint CLI usage
  - Add troubleshooting section (disk full, permissions)

- [ ] **T023** [P] Add type hints and docstrings
  - Verify all public methods have complete docstrings
  - Add Examples sections to docstrings
  - Run mypy type checking (if configured)
  - Fix any type hint issues

### Final Validation

- [ ] **T024** Run full test suite and verify coverage
  - Run `pytest tests/ -v`
  - Verify all 32+ contract tests pass
  - Verify all 7+ integration tests pass
  - Check coverage: `pytest --cov=src/llm_sim/persistence tests/`
  - Target: >90% coverage for persistence module

- [ ] **T025** Manual testing with quickstart scenarios
  - Follow `specs/006-persistent-storage-specifically/quickstart.md`
  - Execute all 7 scenarios manually
  - Verify output files match expected structure
  - Test on different platforms (Linux/macOS/Windows if available)
  - Document any platform-specific issues

---

## Dependencies

**Setup before everything**:
- T001 → all other tasks (creates structure)
- T002 → T017 (orchestrator needs config field)
- T003 → T004-T006 (tests need exception classes)

**Tests before implementation (TDD)**:
- T004-T009 → T014-T019 (all tests must fail first)

**Models before services**:
- T010-T012 → T016 (CheckpointManager uses models)
- T013 → T016 (CheckpointManager saves SimulationState)

**Storage before managers**:
- T014 → T015, T016 (JSONStorage used by both)
- T015 → T017 (RunIDGenerator used by orchestrator)

**Core before integration**:
- T014-T016 → T017 (orchestrator depends on all persistence modules)
- T017 → T018 (resume depends on save logic)
- T018 → T019 (CLI depends on resume method)

**Everything before polish**:
- T001-T019 → T020-T025 (polish tasks validate completion)

---

## Parallel Execution Examples

### Setup Phase (Sequential)
```bash
# Must run in order
Task T001: Create persistence module directory structure
Task T002: Add checkpoint interval field to SimulationConfig
Task T003: Create custom exception classes
```

### Contract Tests Phase (Parallel - All can run together)
```bash
# Launch T004-T006 in parallel:
Task T004: Contract test for JSONStorage
Task T005: Contract test for RunIDGenerator
Task T006: Contract test for CheckpointManager
```

### Integration Tests Phase (Parallel - All can run together)
```bash
# Launch T007-T009 in parallel:
Task T007: Integration test for full simulation with checkpoints
Task T008: Integration test for run ID uniqueness
Task T009: Integration test for checkpoint failure handling
```

### Data Models Phase (Parallel - Different classes)
```bash
# Launch T010-T012 in parallel:
Task T010: Create RunMetadata model
Task T011: Create Checkpoint model
Task T012: Create SimulationResults model
# T013 runs separately (modifies existing file)
Task T013: Verify SimulationState JSON serialization
```

### Storage Implementation (Sequential - Dependencies)
```bash
# Must run in order:
Task T014: Implement JSONStorage
Task T015: Implement RunIDGenerator (depends on T014)
Task T016: Implement CheckpointManager (depends on T014)
```

### Orchestrator Integration (Sequential - Same file)
```bash
# Must run in order (all modify orchestrator.py):
Task T017: Extend SimulationOrchestrator with checkpoint support
Task T018: Add resume-from-checkpoint functionality
Task T019: Add CLI support for checkpoint resume
```

### Polish Phase (Parallel - Different files)
```bash
# Launch T020-T023 in parallel:
Task T020: Unit tests for data models
Task T021: Unit tests for file operations
Task T022: Add configuration examples
Task T023: Add type hints and docstrings
```

### Final Validation (Sequential)
```bash
# Run in order:
Task T024: Run full test suite and verify coverage
Task T025: Manual testing with quickstart scenarios
```

---

## Notes

- **[P] tasks** = Different files, no dependencies, can run in parallel
- **No [P]** = Sequential (same file or dependencies)
- **Verify tests fail** before implementing (TDD)
- **Commit after each task** for clean history
- **All paths** are relative to repository root (`/home/hendrik/coding/llm_sim/llm_sim/`)

## Task Completion Tracking

Mark tasks complete by changing `[ ]` to `[x]` as you finish them. This helps track progress through the 25 tasks.

---

**Estimated Effort**: 25 tasks
- Setup: 3 tasks (~1 hour)
- Tests: 6 tasks (~3 hours)
- Models: 4 tasks (~2 hours)
- Storage: 3 tasks (~3 hours)
- Integration: 3 tasks (~4 hours)
- Polish: 6 tasks (~2 hours)

**Total**: ~15 hours for complete implementation with TDD approach
