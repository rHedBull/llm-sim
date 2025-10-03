# Data Model: Dynamic Agent Management

**Feature**: 009-dynamic-agent-management
**Date**: 2025-10-02

## Entity Overview

This feature introduces lifecycle management entities and modifies existing state models to support dynamic agent populations.

## Core Entities

### 1. LifecycleAction

Represents an agent-initiated request to modify the agent population.

**Fields**:
- `operation`: Enum[`ADD_AGENT`, `REMOVE_AGENT`, `PAUSE_AGENT`, `RESUME_AGENT`]
- `initiating_agent`: str (name of agent making request, None for external operations)
- `target_agent_name`: str (name of agent affected by operation)
- `initial_state`: Optional[Dict[str, Any]] (for ADD_AGENT only)
- `auto_resume_turns`: Optional[int] (for PAUSE_AGENT only)

**Validation Rules** (FR-009):
- `operation` must be valid enum value
- `target_agent_name` must be non-empty string
- For `ADD_AGENT`: `initial_state` must be provided
- For `PAUSE_AGENT`: `auto_resume_turns` must be None or positive integer
- `initiating_agent` None only for external orchestrator operations

**State Transitions**: N/A (actions are requests, not stateful entities)

**Relationships**:
- Validated by: `LifecycleValidator`
- Applied by: `LifecycleManager`

---

### 2. ValidationResult

Represents the outcome of lifecycle action validation.

**Fields**:
- `valid`: bool (True if action passes validation)
- `reason`: Optional[str] (explanation if validation fails)
- `warnings`: List[str] (non-critical issues, e.g., auto-resume config)

**Validation Rules**: N/A (result object, not validated)

**Relationships**:
- Produced by: `LifecycleValidator.validate()`
- Consumed by: `LifecycleManager.apply_changes()`

---

### 3. PauseTracker

Manages the set of paused agents and auto-resume metadata.

**Fields**:
- `paused_agents`: Set[str] (names of currently paused agents)
- `auto_resume`: Dict[str, int] (agent_name → turns_remaining until auto-resume)

**Validation Rules**:
- All names in `auto_resume` keys must be in `paused_agents` set
- All `auto_resume` values must be positive integers

**State Transitions**:
```
ACTIVE → PAUSED: Add to paused_agents
PAUSED → ACTIVE: Remove from paused_agents + auto_resume
PAUSED (with auto-resume) → PAUSED (decremented): Decrement auto_resume counter
PAUSED (auto-resume = 0) → ACTIVE: Automatic resume
```

**Operations**:
- `pause(agent_name: str, auto_resume_turns: Optional[int]) -> None`
- `resume(agent_name: str) -> bool` (returns False if not paused)
- `is_paused(agent_name: str) -> bool`
- `tick_auto_resume() -> List[str]` (returns names auto-resumed this turn)

**Relationships**:
- Used by: `LifecycleManager`
- Persisted in: `SimulationState` (new fields)

---

### 4. LifecycleManager

Coordinates all lifecycle operations (add, remove, pause, resume).

**Fields**:
- `validator`: LifecycleValidator
- `pause_tracker`: PauseTracker
- `max_agents`: int = 25 (FR-028)
- `logger`: structlog.Logger

**Operations**:
- `add_agent(name: str, agent: Agent, initial_state: Dict) -> str` (returns resolved name)
- `remove_agent(name: str, state: SimulationState) -> bool`
- `pause_agent(name: str, auto_resume_turns: Optional[int]) -> bool`
- `resume_agent(name: str) -> bool`
- `process_lifecycle_requests(requests: List[LifecycleAction], state: SimulationState) -> SimulationState`
- `get_active_agents(state: SimulationState) -> List[Agent]` (excludes paused)

**Validation Rules**: Delegates to `LifecycleValidator`

**Relationships**:
- Uses: `LifecycleValidator`, `PauseTracker`
- Used by: `SimulationOrchestrator`, `Engine`

---

### 5. LifecycleValidator

Validates lifecycle operations against constraints and current state.

**Operations**:
- `validate_add(name: str, state: SimulationState) -> ValidationResult`
  - Check: agent count < max_agents (25)
  - Check: name resolution possible (collision handling)

- `validate_remove(name: str, state: SimulationState) -> ValidationResult`
  - Check: agent exists in state
  - Check: agent is active (not already removed)

- `validate_pause(name: str, auto_resume: Optional[int], state: SimulationState) -> ValidationResult`
  - Check: agent exists
  - Check: agent is active (not already paused)
  - Check: auto_resume is None or positive integer

- `validate_resume(name: str, state: SimulationState) -> ValidationResult`
  - Check: agent exists
  - Check: agent is paused (can't resume active agent)

**Validation Rules**:
- All validations return `ValidationResult` (never raise exceptions)
- Failed validations populate `reason` field
- Warnings populate `warnings` list

**Relationships**:
- Used by: `LifecycleManager`

---

## Modified Entities

### SimulationState (MODIFIED)

**Changed Fields**:
- `agents`: **BEFORE**: `List[Agent]` → **AFTER**: `Dict[str, Agent]` (keyed by name)

**New Fields**:
- `paused_agents`: Set[str] (names of paused agents)
- `auto_resume`: Dict[str, int] (auto-resume metadata)

**Migration Impact**:
- All code accessing `state.agents` as list must update
- Iteration: `for agent in state.agents` → `for agent in state.agents.values()`
- Lookup: `state.agents[index]` → `state.agents[name]`
- Count: `len(state.agents)` unchanged (dict length)

**Validation Rules** (existing + new):
- All agent names in `agents` dict must match their `.name` attribute
- All names in `paused_agents` must exist in `agents` dict
- All keys in `auto_resume` must exist in `paused_agents`

---

### Agent (EXISTING - No Changes)

**Note**: Agent model unchanged. Lifecycle status tracked externally in `SimulationState.paused_agents` to avoid modifying agent interface (preserves simplicity per Constitution Principle 1).

---

## Entity Relationships Diagram

```
┌─────────────────────────┐
│  SimulationOrchestrator │
└────────────┬────────────┘
             │ uses
             ▼
┌─────────────────────────┐
│   LifecycleManager      │
│  ┌──────────────────┐   │
│  │ PauseTracker     │   │
│  │ - paused_agents  │   │
│  │ - auto_resume    │   │
│  └──────────────────┘   │
└────────────┬────────────┘
             │ uses
             ▼
┌─────────────────────────┐
│  LifecycleValidator     │
│  - validate_add()       │
│  - validate_remove()    │
│  - validate_pause()     │
│  - validate_resume()    │
└─────────────────────────┘

┌─────────────────────────┐
│   SimulationState       │
│  ┌──────────────────┐   │
│  │ agents: Dict     │   │◄─── Modified from List
│  │ paused_agents    │   │◄─── New
│  │ auto_resume      │   │◄─── New
│  └──────────────────┘   │
└─────────────────────────┘

┌─────────────────────────┐
│   LifecycleAction       │
│  - operation           │
│  - initiating_agent     │
│  - target_agent_name    │
│  - initial_state        │
│  - auto_resume_turns    │
└─────────────────────────┘
             │ validated by
             ▼
┌─────────────────────────┐
│   ValidationResult      │
│  - valid                │
│  - reason               │
│  - warnings             │
└─────────────────────────┘
```

## Serialization Format

### Checkpoint JSON Structure

```json
{
  "turn": 42,
  "agents": {
    "agent1": {
      "name": "agent1",
      "state": {...}
    },
    "agent2": {
      "name": "agent2",
      "state": {...}
    },
    "researcher_1": {
      "name": "researcher_1",
      "state": {...}
    }
  },
  "paused_agents": ["agent2"],
  "auto_resume": {
    "agent2": 3
  },
  "global_state": {...}
}
```

**Notes**:
- Dict keys (agent names) must match nested `name` field
- Numeric suffixes (`_1`) indicate collision resolution occurred
- Paused agents remain in `agents` dict (not removed)

## Validation Summary

| Entity | Validation Rules | Enforced By |
|--------|-----------------|-------------|
| LifecycleAction | Operation enum, non-empty names, conditional fields | Pydantic model |
| PauseTracker | auto_resume keys ⊆ paused_agents, positive counters | PauseTracker class invariants |
| SimulationState | Agent names match dict keys, paused ⊆ agents, auto_resume keys ⊆ paused | SimulationState validation |
| Add operation | Count < 25, unique name resolution | LifecycleValidator |
| Remove operation | Agent exists, not already removed | LifecycleValidator |
| Pause operation | Agent exists, not already paused, auto_resume ≥ 0 or None | LifecycleValidator |
| Resume operation | Agent exists, is paused | LifecycleValidator |

## Type Definitions

### Enums

```python
class LifecycleOperation(str, Enum):
    ADD_AGENT = "add_agent"
    REMOVE_AGENT = "remove_agent"
    PAUSE_AGENT = "pause_agent"
    RESUME_AGENT = "resume_agent"
```

### Type Aliases

```python
AgentName = str
AgentDict = Dict[AgentName, Agent]
PausedSet = Set[AgentName]
AutoResumeMap = Dict[AgentName, int]  # turns_remaining
```

## Constraints

- **MAX_AGENTS**: 25 (FR-028)
- **Auto-resume turns**: Must be positive integer or None
- **Agent names**: Non-empty strings, uniqueness enforced by dict keys
- **Name collision resolution**: Append `_1`, `_2`, etc. until unique (FR-026)

## Edge Case Handling

| Scenario | Behavior |
|----------|----------|
| Add agent with duplicate name | Auto-rename with `_N` suffix |
| Remove last agent | Allowed (simulation can have 0 agents) |
| Pause already paused agent | Validation fails, logged warning |
| Resume non-paused agent | Validation fails, logged warning |
| Add when at max (25) agents | Validation fails, logged warning |
| Auto-resume turns = 0 | Invalid (must be None or ≥ 1) |
| Agent self-removal | Allowed if validation passes |
| Multiple lifecycle requests in one turn | All validated before any applied (atomic) |
