# Contract: LifecycleManager

**Component**: `llm_sim.infrastructure.lifecycle.manager.LifecycleManager`
**Role**: Coordinate all agent lifecycle operations (add, remove, pause, resume)
**Dependencies**: `LifecycleValidator`, `PauseTracker`

## Interface Contract

### Method: `add_agent`

**Signature**:
```python
def add_agent(
    self,
    name: str,
    agent: Agent,
    initial_state: Dict[str, Any],
    state: SimulationState
) -> str
```

**Preconditions**:
- `name` is non-empty string
- `agent` is valid Agent instance
- `initial_state` is valid dict for agent's state schema
- `state` is current simulation state

**Postconditions**:
- Returns resolved agent name (may differ from input if collision)
- Agent added to `state.agents` dict with resolved name
- If `len(state.agents) >= 25` before call, validation fails and agent not added
- If `name` already exists, appends `_1`, `_2`, etc. until unique
- Logs info-level message with resolved name

**Side Effects**:
- Modifies `state.agents` dict
- Logs lifecycle operation

**Error Handling**:
- Validation failure → logs warning, returns original name without adding
- Invalid agent instance → may raise Pydantic validation error

---

### Method: `remove_agent`

**Signature**:
```python
def remove_agent(
    self,
    name: str,
    state: SimulationState
) -> bool
```

**Preconditions**:
- `name` is non-empty string
- `state` is current simulation state

**Postconditions**:
- Returns `True` if agent was removed, `False` if validation failed
- If agent exists and validation passes:
  - Agent removed from `state.agents` dict
  - Agent removed from `state.paused_agents` if paused
  - Agent removed from `state.auto_resume` if present
- If agent doesn't exist, validation fails, returns `False`

**Side Effects**:
- Modifies `state.agents`, `state.paused_agents`, `state.auto_resume`
- Logs lifecycle operation (info on success, warning on failure)

**Error Handling**:
- Non-existent agent → validation fails, logs warning, returns `False`

---

### Method: `pause_agent`

**Signature**:
```python
def pause_agent(
    self,
    name: str,
    auto_resume_turns: Optional[int],
    state: SimulationState
) -> bool
```

**Preconditions**:
- `name` is non-empty string
- `auto_resume_turns` is `None` or positive integer (≥ 1)
- `state` is current simulation state

**Postconditions**:
- Returns `True` if agent was paused, `False` if validation failed
- If validation passes:
  - Agent name added to `state.paused_agents`
  - If `auto_resume_turns` provided, added to `state.auto_resume` with value
- If agent already paused or doesn't exist, validation fails

**Side Effects**:
- Modifies `state.paused_agents` and optionally `state.auto_resume`
- Logs lifecycle operation

**Error Handling**:
- Already paused → validation fails, logs warning, returns `False`
- Non-existent agent → validation fails, logs warning, returns `False`
- Invalid `auto_resume_turns` (0 or negative) → validation fails

---

### Method: `resume_agent`

**Signature**:
```python
def resume_agent(
    self,
    name: str,
    state: SimulationState
) -> bool
```

**Preconditions**:
- `name` is non-empty string
- `state` is current simulation state

**Postconditions**:
- Returns `True` if agent was resumed, `False` if validation failed
- If validation passes:
  - Agent name removed from `state.paused_agents`
  - Agent name removed from `state.auto_resume` if present
- If agent not paused or doesn't exist, validation fails

**Side Effects**:
- Modifies `state.paused_agents` and `state.auto_resume`
- Logs lifecycle operation

**Error Handling**:
- Not paused → validation fails, logs warning, returns `False`
- Non-existent agent → validation fails, logs warning, returns `False`

---

### Method: `get_active_agents`

**Signature**:
```python
def get_active_agents(
    self,
    state: SimulationState
) -> Dict[str, Agent]
```

**Preconditions**:
- `state` is current simulation state

**Postconditions**:
- Returns dict of agents excluding paused agents
- Equivalent to: `{name: agent for name, agent in state.agents.items() if name not in state.paused_agents}`
- Original `state` unmodified

**Side Effects**: None (read-only operation)

**Error Handling**: None (cannot fail with valid state)

---

### Method: `process_auto_resume`

**Signature**:
```python
def process_auto_resume(
    self,
    state: SimulationState
) -> List[str]
```

**Preconditions**:
- `state` is current simulation state
- Called once per turn (typically at turn start)

**Postconditions**:
- Returns list of agent names that were auto-resumed this turn
- For each agent in `state.auto_resume`:
  - Decrements counter by 1
  - If counter reaches 0, resumes agent (removes from paused set and auto_resume dict)
- Logs info message for each auto-resumed agent

**Side Effects**:
- Modifies `state.auto_resume` (decrements counters)
- Modifies `state.paused_agents` (removes auto-resumed agents)
- Logs auto-resume events

**Error Handling**: None (operates on existing auto_resume metadata)

---

## Invariants

1. **Uniqueness**: All agent names in `state.agents` dict are unique (enforced by dict keys)
2. **Pause Subset**: `state.paused_agents ⊆ state.agents.keys()`
3. **Auto-Resume Subset**: `state.auto_resume.keys() ⊆ state.paused_agents`
4. **Max Count**: `len(state.agents) ≤ 25` after any operation
5. **Positive Counters**: All values in `state.auto_resume` are positive integers (≥ 1)

## Logging Contract

All lifecycle operations log structured messages with fields:

**Info-level (successful operations)**:
```python
logger.info(
    "lifecycle_operation",
    operation="add_agent" | "remove_agent" | "pause_agent" | "resume_agent",
    agent_name=name,
    resolved_name=resolved_name,  # for add_agent only
    auto_resume_turns=turns,      # for pause_agent only
    turn=current_turn
)
```

**Warning-level (validation failures)**:
```python
logger.warning(
    "lifecycle_validation_failed",
    operation="add_agent" | "remove_agent" | "pause_agent" | "resume_agent",
    agent_name=name,
    reason=validation_result.reason,
    turn=current_turn
)
```

## Integration with Orchestrator

`SimulationOrchestrator` exposes lifecycle methods that delegate to `LifecycleManager`:

```python
class SimulationOrchestrator:
    def add_agent(self, name: str, agent: Agent, initial_state: Dict) -> str:
        return self.lifecycle_manager.add_agent(name, agent, initial_state, self.state)

    def remove_agent(self, name: str) -> bool:
        return self.lifecycle_manager.remove_agent(name, self.state)

    def pause_agent(self, name: str, auto_resume_turns: Optional[int] = None) -> bool:
        return self.lifecycle_manager.pause_agent(name, auto_resume_turns, self.state)

    def resume_agent(self, name: str) -> bool:
        return self.lifecycle_manager.resume_agent(name, self.state)
```

## Performance Contract

- `add_agent`: O(k) where k = collision count (typically 0-2)
- `remove_agent`: O(1)
- `pause_agent`: O(1)
- `resume_agent`: O(1)
- `get_active_agents`: O(n) where n ≤ 25
- `process_auto_resume`: O(p) where p = paused agent count ≤ 25

All operations complete in < 1ms for n ≤ 25.
