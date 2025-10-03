# Research: Dynamic Agent Management

**Feature**: 009-dynamic-agent-management
**Date**: 2025-10-02
**Status**: Complete

## Research Objectives

1. Determine optimal data structure for dynamic agent storage
2. Identify lifecycle action separation patterns in turn-based systems
3. Research pause/resume mechanisms in simulation frameworks
4. Evaluate collision resolution strategies for duplicate agent names
5. Assess state consistency patterns for atomic lifecycle changes

## Findings

### 1. Agent Storage: List vs Dict

**Decision**: Use `Dict[str, Agent]` keyed by agent name

**Rationale**:
- **O(1) lookups** by name vs O(n) in list
- **Natural alignment** with state storage pattern (already uses agent names as keys)
- **Simplifies uniqueness** enforcement (dict keys inherently unique)
- **Efficient removal** without index shifting
- **Direct access** for pause/resume operations

**Alternatives Considered**:
- `List[Agent]` with name index: Requires maintaining separate index, violates DRY
- `OrderedDict`: Unnecessary overhead; insertion order not critical for agents
- Custom registry class: Over-engineering; dict is sufficient

**Implementation Notes**:
- Migrate `SimulationState.agents: List[Agent]` → `agents: Dict[str, Agent]`
- Update all agent iteration to use `.values()`
- Update checkpoint serialization to handle dict structure

### 2. Lifecycle Action Separation

**Decision**: Process lifecycle actions in separate phase after regular actions

**Rationale**:
- **Turn atomicity**: All agents decide before population changes
- **Consistent state**: No mid-turn agent addition/removal
- **Deterministic ordering**: Lifecycle changes apply in predictable order
- **Testability**: Clear separation enables isolated testing

**Pattern**:
```
Turn N execution:
1. Active agents decide regular actions (existing logic)
2. Engine validates and applies regular actions (existing logic)
3. Collect lifecycle action requests from agents
4. Validate lifecycle requests (new logic)
5. Apply lifecycle changes atomically (new logic)
6. Update state to reflect new population (new logic)
7. Save checkpoint if needed (existing logic, modified for dict)
```

**Alternatives Considered**:
- Immediate lifecycle processing: Creates inconsistent state mid-turn
- Pre-turn lifecycle processing: Agents can't react to turn N-1 outcomes
- Mixed processing: Violates separation of concerns

### 3. Pause/Resume Mechanism

**Decision**: Track paused agents in `Set[str]` with optional auto-resume metadata

**Rationale**:
- **O(1) pause check** via set membership
- **Minimal memory**: Only stores names, not full agent copies
- **State preservation**: Paused agents remain in main dict
- **Simple resume**: Remove from paused set

**Data Structure**:
```python
@dataclass
class PauseTracker:
    paused_agents: Set[str]
    auto_resume: Dict[str, int]  # agent_name → turns_remaining
```

**Auto-Resume Algorithm**:
```
After each turn:
  For each paused agent with auto-resume:
    Decrement turns_remaining
    If turns_remaining == 0:
      Resume agent (remove from paused set)
```

**Alternatives Considered**:
- Separate paused dict: Duplicates agent data, violates DRY
- Status flag on Agent: Requires modifying agent interface
- Time-based resume: Turn count more predictable for testing

### 4. Duplicate Name Collision Resolution

**Decision**: Auto-increment numeric suffix (`agent`, `agent_1`, `agent_2`, ...)

**Rationale**:
- **Deterministic**: Same names always produce same pattern
- **Preserves intent**: Original name visible in result
- **No conflicts**: Incrementing guarantees uniqueness
- **Simple algorithm**: O(k) where k = collision count (typically small)

**Algorithm**:
```python
def resolve_name_collision(base_name: str, existing: Set[str]) -> str:
    if base_name not in existing:
        return base_name

    counter = 1
    while f"{base_name}_{counter}" in existing:
        counter += 1

    return f"{base_name}_{counter}"
```

**Alternatives Considered**:
- UUID suffix: Loses original name semantics
- Timestamp suffix: Non-deterministic, harder to test
- Reject duplicates: Violates clarification decision (auto-rename, not error)
- Hash suffix: Less human-readable

### 5. Atomic Lifecycle Changes

**Decision**: Buffer lifecycle requests, validate all, apply all or none

**Rationale**:
- **Consistency**: Either all changes apply or none
- **Validation order**: Check all constraints before mutations
- **Rollback unnecessary**: No partial state modifications

**Pattern**:
```python
# Collect phase
lifecycle_requests = collect_lifecycle_actions(agents)

# Validation phase (no state changes)
validation_results = []
for request in lifecycle_requests:
    result = validator.validate(request, current_state)
    validation_results.append(result)
    if not result.valid:
        logger.warning("lifecycle_validation_failed", ...)

# Application phase (atomic state updates)
for request, result in zip(lifecycle_requests, validation_results):
    if result.valid:
        apply_lifecycle_change(request, state)
```

**Alternatives Considered**:
- Per-request commit: Risk of partial state corruption
- Transaction/rollback: Over-engineering for in-memory state
- Two-phase commit: Unnecessary complexity for single-process

## Technical Constraints

### Maximum Agent Count (25)

**Enforcement Point**: Validation phase before adding agents

**Implementation**:
```python
def validate_add_agent(name: str, state: SimulationState) -> ValidationResult:
    if len(state.agents) >= 25:
        return ValidationResult(
            valid=False,
            reason=f"Maximum agent count (25) reached. Cannot add '{name}'."
        )
    return ValidationResult(valid=True)
```

### Validation Logging

**Requirement**: FR-029 - Log warnings without halting execution

**Implementation**:
```python
if not validation_result.valid:
    logger.warning(
        "lifecycle_validation_failed",
        operation=request.operation,
        agent_name=request.agent_name,
        reason=validation_result.reason,
        turn=current_turn
    )
    # Continue execution - do not raise exception
```

## Integration Points

### Orchestrator Interface

**New Methods**:
- `add_agent(agent: Agent, initial_state: Dict[str, Any]) -> str`: Returns resolved name
- `remove_agent(name: str) -> bool`: Returns success status
- `pause_agent(name: str, auto_resume_turns: Optional[int] = None) -> bool`
- `resume_agent(name: str) -> bool`

### Engine Modifications

**Existing**:
- `run_turn(state: SimulationState) -> SimulationState`

**Modified**:
- Extract regular actions (existing)
- **NEW**: Extract lifecycle actions
- Validate regular actions (existing)
- **NEW**: Validate lifecycle actions
- Apply regular actions (existing)
- **NEW**: Apply lifecycle changes
- Return updated state (existing, now with modified agent dict)

### State Serialization

**Checkpoint Format Change**:
```json
// OLD
{
  "agents": [
    {"name": "agent1", ...},
    {"name": "agent2", ...}
  ]
}

// NEW
{
  "agents": {
    "agent1": {...},
    "agent2": {...}
  },
  "paused_agents": ["agent2"],
  "auto_resume": {"agent2": 5}
}
```

## Performance Considerations

### Time Complexity

- **Add agent**: O(1) dict insert + O(k) collision resolution (k typically 0-2)
- **Remove agent**: O(1) dict delete + O(1) set remove
- **Pause agent**: O(1) set add
- **Resume agent**: O(1) set remove
- **Turn execution**: O(n) where n = active agent count (unchanged from current)

### Space Complexity

- **Agent storage**: O(n) where n ≤ 25 (bounded)
- **Pause tracking**: O(p) where p ≤ 25 (bounded)
- **Auto-resume metadata**: O(a) where a ≤ 25 (bounded)

**Total**: O(25) = O(1) constant bounded space

### Benchmarks

Not applicable for this scale (25 agents max). All operations complete in microseconds.

## Risk Assessment

### Migration Risk: List → Dict

**Risk**: Breaking change to existing code accessing `state.agents` as list

**Mitigation**:
- Constitution Principle 3: No legacy support (explicit breaking change)
- Update all agent iterations: `for agent in state.agents` → `for agent in state.agents.values()`
- Type checker will catch incompatible access patterns
- Integration tests will validate migration completeness

### Edge Case: Last Agent Removal

**Scenario**: Last remaining agent attempts self-removal

**Decision**: Allow removal (simulation can have 0 agents)

**Rationale**:
- No minimum agent count requirement in spec
- Allows simulation to terminate naturally
- Orchestrator can detect empty state and stop if needed

### Edge Case: Concurrent Lifecycle Requests

**Scenario**: Multiple agents spawn new agents in same turn, approaching limit

**Behavior**:
- All spawn requests buffered
- Validation checks current count + pending adds
- First N requests (up to limit) succeed
- Remaining requests fail validation with logged warnings
- No race conditions (single-threaded, sequential processing)

## Dependencies

**No new external dependencies required.**

Uses existing:
- `pydantic`: Data modeling for lifecycle actions
- `structlog`: Logging for lifecycle operations
- `typing`: Type hints for dict-based agent storage

## Conclusion

All technical unknowns resolved. No NEEDS CLARIFICATION markers remain. Design is simple, testable, and constitutional. Ready for Phase 1 (Design & Contracts).
