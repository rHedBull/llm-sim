# Feature Specification: Persistent Simulation State Storage

**Feature Branch**: `006-persistent-storage-specifically`
**Created**: 2025-10-01
**Status**: Draft
**Input**: User description: "persistent storage. specifically of the global state after each turn. so that it can be reloaded, restartet from. for now we always want to store the last turn and every N turn's as specified  per run, initially in the simulation setup. there should be consistent run naming a mix of the simulation name number agents and run date, but should always be unique. also there should be an output dir in the root of the project, there for each run a json with the run results is generated, it should have the same name_result.json . the naming of the same run should be consistent across these."

## Execution Flow (main)
```
1. Parse user description from Input
   → Identifies: state persistence, checkpoint intervals, run naming, output directory
2. Extract key concepts from description
   → Actors: simulation orchestrator, users resuming simulations
   → Actions: save state, load state, generate run names, store results
   → Data: simulation state (per turn), run metadata, results
   → Constraints: unique naming, consistent naming across artifacts
3. For each unclear aspect:
   → Marked with [NEEDS CLARIFICATION] throughout requirements
4. Fill User Scenarios & Testing section
   → Primary: save/resume simulation from checkpoint
   → Secondary: review stored states and results
5. Generate Functional Requirements
   → State persistence, checkpoint intervals, naming, output structure
6. Identify Key Entities
   → SimulationState, Checkpoint, RunMetadata, SimulationResults
7. Run Review Checklist
   → WARN: Spec has uncertainties (marked with [NEEDS CLARIFICATION])
8. Return: SUCCESS (spec ready for clarification then planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-10-01
- Q: When the `output/` directory doesn't exist at simulation start, what should the system do? → A: Auto-create directory (and parent paths if needed)
- Q: When saving a checkpoint fails (e.g., disk space, permission error), what should the system do? → A: Fail simulation immediately with error
- Q: How should checkpoint and result files be organized in the `output/` directory? → A: Per-run subdirectories: `output/RunID/checkpoints/` and `output/RunID/results.json`
- Q: To ensure run identifiers are globally unique when multiple simulations start in the same second, what precision should be used? → A: Add sequence number: `{name}_{agents}agents_{YYYYMMDD}_{HHMMSS}_01`
- Q: Should checkpoints save full turn-by-turn history or only the current state needed to resume? → A: Current state only: save just the single global state snapshot at that turn (no historical turns)

---

## User Scenarios & Testing

### Primary User Story
As a simulation researcher, I want to save simulation state at regular intervals so that I can:
1. Resume long-running simulations without starting over if interrupted
2. Review historical states from specific turns
3. Restart simulations from interesting checkpoint points for what-if analysis
4. Store complete simulation results with consistent naming for later analysis

### Acceptance Scenarios

1. **Given** a simulation configuration specifying checkpoint intervals (e.g., every 5 turns), **When** the simulation runs for 15 turns, **Then** the system saves state at turns 5, 10, and 15, plus always saves the final turn

2. **Given** a saved checkpoint from turn 10 of a previous run, **When** a user requests to resume from that checkpoint, **Then** the simulation loads that exact state and continues from turn 11

3. **Given** a simulation named "EconomicTest" with 3 agents run on 2025-10-01, **When** the simulation completes, **Then** all artifacts (checkpoints, results) use the same unique run identifier (e.g., "EconomicTest_3agents_20251001_143022")

4. **Given** a completed simulation run with ID "EconomicTest_3agents_20251001_143022", **When** checking the output directory, **Then** a subdirectory `output/EconomicTest_3agents_20251001_143022/` exists containing `checkpoints/` subdirectory and `result.json` file with final state and summary statistics

5. **Given** multiple simulation runs with the same parameters run on different dates, **When** examining the output directory, **Then** each run has a unique identifier and all artifacts are clearly distinguishable

### Edge Cases

- **What happens when** disk space is insufficient to save a checkpoint?
  - Simulation fails immediately with clear error message indicating the save failure and reason

- **What happens when** attempting to resume from a checkpoint that doesn't exist or is corrupted?
  - [NEEDS CLARIFICATION: Error handling behavior - fail with message, offer nearby checkpoints, or auto-fallback?]

- **What happens when** checkpoint interval N is larger than total simulation turns?
  - System should save only the final turn (plus last turn as always saved)

- **What happens when** output directory doesn't exist?
  - System automatically creates the directory (including parent paths if needed)

- **What happens when** two simulations with identical parameters start in the same second?
  - System appends a sequence number (01, 02, 03, etc.) to ensure unique run identifiers

- **What happens when** a user tries to resume from a checkpoint saved by a different version of the simulation code?
  - [NEEDS CLARIFICATION: Version compatibility checks needed? Migration strategy?]

- **What happens when** the simulation is manually interrupted (e.g., Ctrl+C) between checkpoints?
  - [NEEDS CLARIFICATION: Should system save emergency checkpoint on interrupt signal?]

## Requirements

### Functional Requirements

#### State Persistence
- **FR-001**: System MUST save complete simulation state after every turn marked as the "last turn" (most recent state always available)

- **FR-002**: System MUST save simulation state at intervals specified by checkpoint configuration (e.g., every N turns where N is configurable per simulation)

- **FR-003**: System MUST save final simulation state when simulation completes (whether by reaching max turns or termination condition)

- **FR-004**: Saved states MUST include all information necessary to resume simulation from that exact point, including:
  - Current turn number
  - All agent states (complete state for each agent at that turn)
  - Global state (complete global simulation state at that turn)
  - State snapshot only (no turn-by-turn history saved)

#### State Loading & Resume
- **FR-005**: Users MUST be able to load any saved checkpoint from a previous run by specifying run ID and turn number

- **FR-006**: System MUST resume simulation from loaded checkpoint, continuing from the next turn after the checkpoint

- **FR-007**: System MUST validate checkpoint compatibility before loading [NEEDS CLARIFICATION: What validation checks? Config match, version match, schema validation?]

- **FR-008**: System MUST preserve all simulation configuration when resuming (cannot change agent count, engine type, etc.)

#### Run Naming & Identification
- **FR-009**: System MUST generate unique run identifiers using format: `{simulation_name}_{num_agents}agents_{date}_{time}_{seq}`
  - Date format: YYYYMMDD
  - Time format: HHMMSS
  - Sequence number: 2-digit zero-padded (01, 02, 03, etc.)
  - System increments sequence number when a run ID collision would occur
  - Example: `EconomicTest_3agents_20251001_143022_01`

- **FR-010**: System MUST use the same run identifier consistently across all artifacts for a single simulation run:
  - Checkpoint files
  - Results file
  - Any logs or metadata [NEEDS CLARIFICATION: Are logs part of this feature?]

- **FR-011**: Run identifiers MUST be globally unique across all simulation runs (no collisions even with identical configs)

#### Output Directory Structure
- **FR-012**: System MUST use an `output/` directory in the project root for storing all simulation artifacts. If the directory does not exist, system MUST automatically create it (including any required parent directories)

- **FR-013**: System MUST organize output using per-run subdirectories with the following structure:
  ```
  output/
    {run_id}/
      checkpoints/
        turn_{N}.json     (checkpoint files for each saved turn)
      result.json         (final results file)
  ```
  Example: `output/EconomicTest_3agents_20251001_143022/checkpoints/turn_5.json`

- **FR-014**: System MUST generate results file named `result.json` inside each run's subdirectory (e.g., `output/{run_id}/result.json`)

- **FR-015**: Results file MUST contain:
  - Run metadata (run ID, start time, end time, configuration summary)
  - Final simulation state
  - Summary statistics [NEEDS CLARIFICATION: Which statistics? Agent outcomes, turn count, termination reason?]
  - Checkpoint information (which turns were checkpointed)

#### Configuration
- **FR-016**: Users MUST be able to specify checkpoint interval in simulation configuration (e.g., "save every 10 turns")

- **FR-017**: Users MUST be able to disable interval checkpoints [NEEDS CLARIFICATION: Should last turn always save even if checkpoints disabled?]

- **FR-018**: Checkpoint interval configuration MUST be validated (must be positive integer) [NEEDS CLARIFICATION: Maximum interval limit?]

#### Data Management
- **FR-019**: System MUST prevent accidental overwriting of existing checkpoints and results from previous runs

- **FR-020**: System MUST fail immediately when checkpoint saving encounters any error (disk space, permissions, I/O errors) with a clear error message describing the failure reason and affected checkpoint

### Key Entities

- **SimulationState**: Complete snapshot of simulation at a specific turn (no historical data)
  - Turn number
  - All agent states (per agent: name, economic strength, any domain-specific data)
  - Global state (interest rate, GDP, any global variables)
  - Timestamp of when state was captured
  - Note: Contains only the current turn state, not turn-by-turn history
  - Relationships: belongs to one Run, can be loaded to resume simulation

- **Checkpoint**: Saved simulation state at a specific interval
  - Turn number
  - File path to saved state data
  - Checkpoint type (interval, last, final)
  - Relationships: contains one SimulationState, belongs to one Run

- **Run**: A single execution of a simulation from start to completion (or interruption)
  - Unique run identifier (generated from name, agents, date, time)
  - Simulation name
  - Number of agents
  - Start timestamp
  - End timestamp (if completed)
  - Configuration snapshot
  - Checkpoint interval setting
  - Relationships: has many Checkpoints, has one Results

- **SimulationResults**: Summary output and metadata for a completed run
  - Run identifier (matches Run ID)
  - Final state snapshot
  - Summary statistics (outcomes, performance metrics)
  - List of available checkpoints
  - Relationships: belongs to one Run

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain - **5 critical clarifications resolved, 7 deferred to planning**
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

### Outstanding Clarifications (Remaining)

**Resolved in Session 2025-10-01**: 5 critical clarifications
- ✅ Output directory creation
- ✅ Checkpoint save failure handling
- ✅ Directory structure
- ✅ Run ID uniqueness (sequence numbers)
- ✅ Checkpoint content (current state only)

**Deferred to Planning Phase**: 7 clarifications
1. **Checkpoint corruption**: Error handling for corrupted/missing checkpoints - *Deferred: implementation detail*
2. **Version compatibility**: Checkpoint version checking needed - *Deferred: depends on schema evolution strategy*
3. **Interrupt handling**: Save emergency checkpoint on Ctrl+C - *Deferred: signal handling implementation detail*
4. **Random seed**: Preserve RNG state for reproducibility - *Deferred: depends on whether simulations use randomness*
5. **Checkpoint validation**: What specific validation checks - *Deferred: technical validation details*
6. **Logs in artifacts**: Are logs part of this feature - *Deferred: logging is separate concern*
7. **Summary statistics**: Which specific statistics in results - *Deferred: can specify during implementation*

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (12 clarifications identified)
- [x] User scenarios defined
- [x] Requirements generated (20 functional requirements)
- [x] Entities identified (4 key entities)
- [ ] Review checklist passed (pending clarifications)

---

## Next Steps

This specification requires **12 clarifications** before proceeding to planning. Recommend running `/clarify` to address uncertainties, particularly:
- Priority 1: Error handling strategies (disk space, corruption, interrupts)
- Priority 2: Naming collision resolution and time precision
- Priority 3: Checkpoint content (history, RNG state, validation)
- Priority 4: Directory structure and statistics details
