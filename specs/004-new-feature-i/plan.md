
# Implementation Plan: LLM-Based Reasoning in Simulation Components

**Branch**: `004-new-feature-i` | **Date**: 2025-09-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/home/hendrik/coding/llm_sim/llm_sim/specs/004-new-feature-i/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Integrate LLM-based reasoning (Ollama gemma:3) into Agent, Validator, and Engine components to enable explainable decision-making in simulations. Agents use LLMs to generate flexible action strings from observed state, Validators use LLM reasoning to determine domain validity, and Engines use LLM reasoning to compute state updates from validated actions. The system maintains existing architecture with minimal class adaptations while adding comprehensive error handling (retry-once-then-abort) and debug-level reasoning chain logging.

## Technical Context
**Language/Version**: Python 3.12
**Primary Dependencies**: Pydantic 2.x, PyYAML 6.x, structlog 24.x, ollama Python client (new), httpx (for async LLM calls)
**Storage**: In-memory only (no persistence until simulation end)
**Testing**: pytest 8.x with contract/integration/unit test structure
**Target Platform**: Linux server (development/execution environment)
**Project Type**: single (existing src/ structure)
**Performance Goals**: LLM response time <5s per call, simulation step <30s for 10 agents
**Constraints**: Retry LLM once on failure then abort; log all reasoning chains at DEBUG level; maintain existing Action → Validator → Engine flow
**Scale/Scope**: 10-100 agents per simulation, 100-1000 turns, flexible action strings (no type constraints)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Project constitution at `.specify/memory/constitution.md` is currently a template (not populated). Proceeding with Python ecosystem best practices:

- ✅ **Type Safety**: Using Pydantic models for all data structures (existing pattern)
- ✅ **Test Coverage**: Contract tests for LLM interactions, unit tests for retry logic
- ✅ **Dependency Management**: Using uv/pip for package management (pyproject.toml exists)
- ✅ **Error Handling**: Explicit retry-once-then-abort pattern with structured logging
- ✅ **Observability**: DEBUG-level reasoning chains, prominent error logs
- ✅ **Minimal Change**: Adapting existing classes, not creating new architecture

**Complexity Justification**: No violations. Adding new dependency (ollama client) is justified for LLM integration requirements.

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
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
│   ├── action.py           # Extend with LLM reasoning fields
│   ├── state.py            # Extend with reasoning chain history
│   ├── config.py           # Add LLM config section
│   └── llm_models.py       # NEW: PolicyDecision, ValidationResult, StateUpdateDecision, LLMReasoningChain
├── agents/
│   ├── base.py             # Existing Agent ABC (no changes)
│   ├── llm_agent.py        # NEW: LLMAgent ABC (adds LLM reasoning)
│   ├── econ_llm_agent.py   # NEW: EconLLMAgent (concrete economic implementation)
│   └── nation.py           # Existing NationAgent (legacy, no changes)
├── validators/
│   ├── base.py             # Existing Validator ABC (no changes)
│   ├── llm_validator.py    # NEW: LLMValidator ABC (adds LLM validation)
│   ├── econ_llm_validator.py  # NEW: EconLLMValidator (concrete economic implementation)
│   └── always_valid.py     # Existing AlwaysValidValidator (legacy, no changes)
├── engines/
│   ├── base.py             # Existing Engine ABC (no changes)
│   ├── llm_engine.py       # NEW: LLMEngine ABC (adds LLM reasoning)
│   ├── econ_llm_engine.py  # NEW: EconLLMEngine (concrete economic implementation)
│   └── economic.py         # Existing EconomicEngine (legacy, no changes)
├── utils/
│   ├── llm_client.py       # NEW: Ollama client with retry logic
│   └── logging.py          # Extend for reasoning chain logging
└── orchestrator.py         # Update to support new agent/validator/engine types

tests/
├── contract/
│   ├── test_llm_client_contract.py        # NEW: LLM client interface tests
│   ├── test_llm_agent_contract.py         # NEW: LLMAgent abstract interface tests
│   ├── test_llm_validator_contract.py     # NEW: LLMValidator abstract interface tests
│   └── test_llm_engine_contract.py        # NEW: LLMEngine abstract interface tests
├── integration/
│   ├── test_simulation.py                 # Update with LLM mocking
│   ├── test_llm_reasoning_flow.py         # NEW: End-to-end reasoning flow
│   ├── test_llm_error_handling.py         # NEW: Retry and abort behavior
│   └── test_validation_rejection.py       # NEW: Skip unvalidated actions
└── unit/
    ├── test_llm_client.py                 # NEW: Retry logic tests
    ├── test_llm_models.py                 # NEW: Pydantic model tests
    ├── test_econ_llm_agent.py             # NEW: EconLLMAgent tests
    ├── test_econ_llm_validator.py         # NEW: EconLLMValidator tests
    └── test_econ_llm_engine.py            # NEW: EconLLMEngine tests
```

**Structure Decision**: Three-tier inheritance hierarchy:
- **Base layer** (existing): `Agent`, `Validator`, `Engine` ABCs - no changes
- **LLM layer** (new): `LLMAgent`, `LLMValidator`, `LLMEngine` ABCs - add LLM infrastructure
- **Concrete layer** (new): `EconLLMAgent`, `EconLLMValidator`, `EconLLMEngine` - economic domain implementations

**New Files**:
- `llm_models.py` (LLM-specific Pydantic models)
- `llm_client.py` (Ollama client utility)
- `llm_agent.py`, `econ_llm_agent.py` (agent hierarchy)
- `llm_validator.py`, `econ_llm_validator.py` (validator hierarchy)
- `llm_engine.py`, `econ_llm_engine.py` (engine hierarchy)

**Legacy Preserved**: `nation.py`, `always_valid.py`, `economic.py` remain unchanged for backward compatibility.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. **Contract Test Tasks** (from contracts/ directory):
   - test_llm_client_contract.py → LLM client interface tests [P]
   - test_llm_agent_contract.py → LLMAgent ABC interface tests [P]
   - test_llm_validator_contract.py → LLMValidator ABC interface tests [P]
   - test_llm_engine_contract.py → LLMEngine ABC interface tests [P]

2. **Data Model Tasks** (from data-model.md):
   - Create llm_models.py with all LLM Pydantic models [P]:
     * LLMReasoningChain
     * PolicyDecision
     * ValidationResult
     * StateUpdateDecision
   - Extend Action model with action_string + policy_decision fields
   - Extend SimulationState model with reasoning_chains field
   - Create LLMConfig model in config.py [P]
   - Extend ValidatorConfig model with domain + permissive fields

3. **Core Implementation Tasks** (three-tier hierarchy, dependency order):
   - Implement LLMClient with retry logic (depends on: LLMConfig model)
   - **Agent Tier**:
     * Implement LLMAgent ABC (depends on: LLMClient, PolicyDecision)
     * Implement EconLLMAgent concrete class (depends on: LLMAgent)
   - **Validator Tier**:
     * Implement LLMValidator ABC (depends on: LLMClient, ValidationResult)
     * Implement EconLLMValidator concrete class (depends on: LLMValidator)
   - **Engine Tier**:
     * Implement LLMEngine ABC (depends on: LLMClient, StateUpdateDecision)
     * Implement EconLLMEngine concrete class (depends on: LLMEngine)
   - Update Orchestrator to support new component types (econ_llm_agent, econ_llm_validator, econ_llm_engine)

4. **Integration Test Tasks** (from quickstart.md):
   - test_llm_reasoning_flow.py → full Agent→Validator→Engine flow
   - test_llm_error_handling.py → retry and abort behavior
   - test_validation_rejection.py → skip unvalidated actions
   - test_multi_turn_llm_simulation.py → end-to-end with multiple turns

5. **Configuration & Logging Tasks**:
   - Add LLM config section to config.yaml schema
   - Extend logging for DEBUG-level reasoning chains
   - Create prompt template constants

**Ordering Strategy**:
- **Phase A**: Contract tests (all [P] parallel) → ensure interfaces defined for abstract classes
- **Phase B**: Data models (all [P] parallel) → foundation for implementation
- **Phase C**: LLMClient implementation → shared by all components
- **Phase D**: Abstract class implementations (can be [P] parallel, share LLMClient):
  1. LLMAgent ABC (depends on LLMClient, PolicyDecision)
  2. LLMValidator ABC (depends on LLMClient, ValidationResult)
  3. LLMEngine ABC (depends on LLMClient, StateUpdateDecision)
- **Phase E**: Concrete class implementations (can be [P] parallel, depend on respective ABCs):
  1. EconLLMAgent (depends on LLMAgent)
  2. EconLLMValidator (depends on LLMValidator)
  3. EconLLMEngine (depends on LLMEngine)
- **Phase F**: Orchestrator update (depends on all concrete classes)
- **Phase G**: Integration tests → validate end-to-end flow
- **Phase H**: Configuration & logging → production readiness

**Dependency Graph**:
```
Contract Tests [P] ──┐
Data Models [P] ──────┤
                      ├─→ LLMClient ─┬─→ LLMAgent ABC ────────→ EconLLMAgent ───┐
                      │              ├─→ LLMValidator ABC ─────→ EconLLMValidator ├─→ Orchestrator ─→ Integration Tests
                      │              └─→ LLMEngine ABC ────────→ EconLLMEngine ──┘
                      └─→ Config/Logging [P]
```

**Estimated Output**: 40-45 numbered, ordered tasks in tasks.md
- 20 test tasks (contract + integration)
- 10 model tasks
- 12 implementation tasks (3 ABC + 3 concrete + LLMClient + Orchestrator + 4 unit test files)
- 3 config/logging tasks

**TDD Enforcement**:
- Every implementation task must follow a corresponding test task
- Tests written first, must fail before implementation begins
- Mark with [TEST_FIRST] prefix to enforce TDD discipline

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

**No violations identified.** All Phase 1 design artifacts align with constitution principles:
- Pydantic models maintain type safety
- Contract tests define clear interfaces
- In-memory storage avoids persistence complexity
- LLM client encapsulates retry logic (single responsibility)
- Existing architecture preserved (minimal adaptations)


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command) - 40 numbered tasks
- [~] Phase 4: Implementation in progress (8/40 tasks complete - 20%)
  - [x] Phase 3.1: Setup & Dependencies (T001-T003)
  - [x] Phase 3.2: Data Models (T004-T008)
  - [ ] Phase 3.3: Contract Tests (T009-T015) - NEXT
  - [ ] Phase 3.4-3.6: Core Implementation (T016-T022)
  - [ ] Phase 3.7-3.11: Integration & Polish (T023-T040)
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved (via research.md)
- [x] Complexity deviations documented (none identified)

**Artifacts Generated**:
- [x] research.md (Phase 0 output)
- [x] data-model.md (Phase 1 output) - updated with three-tier hierarchy
- [x] ARCHITECTURE.md (Phase 1 output) - three-tier inheritance explanation
- [x] contracts/llm_client_contract.md (Phase 1 output)
- [x] contracts/agent_interface_contract.md (Phase 1 output) - updated for LLMAgent/EconLLMAgent
- [x] contracts/validator_interface_contract.md (Phase 1 output) - updated for LLMValidator/EconLLMValidator
- [x] contracts/engine_interface_contract.md (Phase 1 output) - updated for LLMEngine/EconLLMEngine
- [x] quickstart.md (Phase 1 output)
- [x] CLAUDE.md updated (Phase 1 output)
- [x] tasks.md (Phase 3 output) - 40 numbered tasks with TDD discipline
- [x] IMPLEMENTATION_STATUS.md (Phase 4 partial) - handoff document with progress summary

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
