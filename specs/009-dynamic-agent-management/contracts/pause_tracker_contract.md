# Contract: PauseTracker

**Component**: `llm_sim.infrastructure.lifecycle.pause_tracker.PauseTracker`
**Role**: Track paused agent state and auto-resume metadata
**Dependencies**: None (standalone component)

## Interface Contract

### Method: `pause`

**Signature**:
```python
def pause(
    self,
    agent_name: str,
    auto_resume_turns: Optional[int] = None
) -> None
```

**Preconditions**:
- `agent_name` is non-empty string
- `auto_resume_turns` is `None` or positive integer (≥ 1)
- Agent not already paused (caller's responsibility to check)

**Postconditions**:
- `agent_name` added to `self.paused_agents` set
- If `auto_resume_turns` provided, `self.auto_resume[agent_name] = auto_resume_turns`
- If `auto_resume_turns` is `None`, `agent_name` not added to `self.auto_resume`

**Side Effects**:
- Modifies `self.paused_agents`
- May modify `self.auto_resume`

**Error Handling**:
- No validation performed (assumes pre-validated by caller)
- If called on already-paused agent, overwrites auto_resume value if provided

---

### Method: `resume`

**Signature**:
```python
def resume(
    self,
    agent_name: str
) -> bool
```

**Preconditions**:
- `agent_name` is non-empty string

**Postconditions**:
- Returns `True` if agent was paused and resumed, `False` if not paused
- If agent was paused:
  - `agent_name` removed from `self.paused_agents`
  - `agent_name` removed from `self.auto_resume` if present
- If agent was not paused, no changes made

**Side Effects**:
- May modify `self.paused_agents`
- May modify `self.auto_resume`

**Error Handling**: None (returns `False` for non-paused agent)

---

### Method: `is_paused`

**Signature**:
```python
def is_paused(
    self,
    agent_name: str
) -> bool
```

**Preconditions**:
- `agent_name` is non-empty string

**Postconditions**:
- Returns `True` if `agent_name` in `self.paused_agents`, else `False`
- No state modifications

**Side Effects**: None (read-only)

**Error Handling**: None (cannot fail)

---

### Method: `tick_auto_resume`

**Signature**:
```python
def tick_auto_resume() -> List[str]
```

**Preconditions**: None (operates on current state)

**Postconditions**:
- Returns list of agent names auto-resumed this tick
- For each `(agent_name, turns_remaining)` in `self.auto_resume`:
  - Decrements `turns_remaining` by 1
  - If `turns_remaining` reaches 0:
    - Removes `agent_name` from `self.paused_agents`
    - Removes `agent_name` from `self.auto_resume`
    - Adds `agent_name` to returned list

**Side Effects**:
- Modifies `self.auto_resume` (decrements all counters)
- Modifies `self.paused_agents` (removes auto-resumed agents)

**Error Handling**: None (operates on existing metadata)

**Example**:
```python
# Initial state
tracker.paused_agents = {"agent1", "agent2", "agent3"}
tracker.auto_resume = {"agent1": 2, "agent2": 1}

# First tick
resumed = tracker.tick_auto_resume()
# resumed = ["agent2"]
# tracker.paused_agents = {"agent1", "agent3"}
# tracker.auto_resume = {"agent1": 1}

# Second tick
resumed = tracker.tick_auto_resume()
# resumed = ["agent1"]
# tracker.paused_agents = {"agent3"}
# tracker.auto_resume = {}
```

---

### Method: `get_paused_count`

**Signature**:
```python
def get_paused_count() -> int
```

**Preconditions**: None

**Postconditions**:
- Returns `len(self.paused_agents)`
- No state modifications

**Side Effects**: None (read-only)

**Error Handling**: None (cannot fail)

---

### Method: `clear`

**Signature**:
```python
def clear() -> None
```

**Preconditions**: None

**Postconditions**:
- `self.paused_agents` cleared (empty set)
- `self.auto_resume` cleared (empty dict)

**Side Effects**:
- Modifies `self.paused_agents` (clears)
- Modifies `self.auto_resume` (clears)

**Error Handling**: None (cannot fail)

**Use Case**: Reset tracker for new simulation run

---

## Invariants

1. **Auto-Resume Subset**: `self.auto_resume.keys() ⊆ self.paused_agents`
2. **Positive Counters**: All `self.auto_resume.values() ≥ 1` (decremented before zero-check in `tick_auto_resume`)
3. **Bounded Size**: `len(self.paused_agents) ≤ 25` (enforced externally by agent limit)

## Serialization Contract

### To Dict

**Signature**:
```python
def to_dict() -> Dict[str, Any]
```

**Output Format**:
```python
{
    "paused_agents": ["agent1", "agent2"],  # sorted list for determinism
    "auto_resume": {
        "agent1": 5,
        "agent2": 3
    }
}
```

### From Dict

**Signature**:
```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> PauseTracker
```

**Input Format**: Same as `to_dict()` output

**Validation**:
- All `auto_resume` keys must be in `paused_agents` list
- All `auto_resume` values must be positive integers

## Performance Contract

- `pause`: O(1)
- `resume`: O(1)
- `is_paused`: O(1)
- `tick_auto_resume`: O(p) where p = paused agent count ≤ 25
- `get_paused_count`: O(1)
- `clear`: O(1)
- `to_dict`: O(p) where p ≤ 25
- `from_dict`: O(p) where p ≤ 25

All operations complete in microseconds for p ≤ 25.

## Thread Safety

**Not thread-safe.** Assumes single-threaded simulation execution (per Constitution - simple over complex).

## Usage Example

```python
tracker = PauseTracker()

# Pause agent indefinitely
tracker.pause("agent1")
assert tracker.is_paused("agent1") == True

# Pause agent with auto-resume
tracker.pause("agent2", auto_resume_turns=3)

# Tick through turns
resumed = tracker.tick_auto_resume()  # returns []
resumed = tracker.tick_auto_resume()  # returns []
resumed = tracker.tick_auto_resume()  # returns ["agent2"]

assert tracker.is_paused("agent1") == True   # still paused
assert tracker.is_paused("agent2") == False  # auto-resumed

# Manual resume
tracker.resume("agent1")
assert tracker.is_paused("agent1") == False
```
