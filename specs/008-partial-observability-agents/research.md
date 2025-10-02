# Research: Partial Observability for Agents

**Feature**: 008-partial-observability-agents
**Date**: 2025-10-02

## Research Questions & Findings

### 1. Noise Model Selection

**Question**: What noise model should be used for observation uncertainty?

**Decision**: Deterministic, seeded random noise using Python's `random.Random`

**Rationale**:
- Clarification specified "most testable option"
- Seeded RNG provides deterministic, reproducible noise for testing
- Seed derived from (turn, agent_id, variable_name) ensures consistent per-observation noise
- Allows test assertions like "at turn=5, agent1 observes variable X with noise value Y"

**Implementation Approach**:
```python
def apply_noise(value: float, noise_factor: float, seed_components: tuple) -> float:
    if noise_factor == 0.0:
        return value
    seed = hash(seed_components)
    rng = random.Random(seed)
    noise = rng.uniform(-noise_factor, noise_factor)
    return value * (1.0 + noise)  # Multiplicative noise
```

**Alternatives Considered**:
- **Gaussian additive noise**: More realistic for some domains, but non-deterministic without manual seeding, harder to test
- **Fixed offset**: Too predictable, doesn't simulate uncertainty well
- **Uniform random unseeded**: Non-reproducible, breaks deterministic replay requirement

**References**:
- Python random module documentation: https://docs.python.org/3/library/random.html
- Deterministic testing best practices for stochastic systems

---

### 2. Observation Data Structure

**Question**: What format should agent observations use?

**Decision**: Reuse existing Pydantic state model structure (via `create_agent_state_model`, `create_global_state_model`)

**Rationale**:
- Clarification specified "structurally similar to state model, separate observation representation" (FR-018, FR-019)
- Minimizes agent logic changes - agents work with same BaseModel interface
- Leverages existing validation, serialization, type safety from Pydantic
- Observation constructor creates new instance with filtered fields and noisy values

**Implementation Approach**:
```python
def construct_observation(
    observer_id: str,
    ground_truth: SimulationState,
    observability_config: ObservabilityConfig
) -> SimulationState:
    filtered_agents = {}
    for agent_id, agent_state in ground_truth.agents.items():
        level = get_observability_level(observer_id, agent_id, observability_config)
        if level == ObservabilityLevel.UNAWARE:
            continue  # Exclude completely
        filtered_agents[agent_id] = filter_and_noise_agent(agent_state, level, ...)

    filtered_global = filter_and_noise_global(ground_truth.global_state, ...)

    return SimulationState(
        turn=ground_truth.turn,
        agents=filtered_agents,
        global_state=filtered_global,
        reasoning_chains=[]  # Observations don't include others' reasoning
    )
```

**Alternatives Considered**:
- **Dedicated ObservationState class**: Would duplicate state model logic, violates DRY
- **Dict-based observations**: Loses type safety and validation, breaks agent contracts
- **Partial model with Optional fields**: Confusing semantics (None vs hidden vs missing)

**References**:
- Pydantic model_copy documentation
- Existing state.py factories: create_agent_state_model, create_global_state_model

---

### 3. Variable Visibility Classification

**Question**: How should variables be marked as external vs internal?

**Decision**: Add optional `visibility: "external" | "internal"` field to VariableDefinition, default to "external"

**Rationale**:
- Extends existing configuration pattern in config.py
- Keeps variable metadata co-located (type, min, max, visibility all in VariableDefinition)
- Backward compatible - omitted visibility defaults to "external" (most permissive)
- Validated once at config load time

**Implementation Approach**:
```yaml
state_variables:
  agent_vars:
    economic_strength:
      type: float
      min: 0
      default: 0.0
      visibility: external  # Public variable
    secret_reserves:
      type: float
      min: 0
      default: 0.0
      visibility: internal  # Private variable
```

**Alternatives Considered**:
- **Separate visibility config section**: Spreads variable metadata, harder to maintain
- **Visibility in observability matrix**: Per-pair visibility overrides are too complex
- **All variables external by default with internal list**: Inverse default, less safe

**References**:
- Existing VariableDefinition in config.py
- Pydantic Literal type for enums

---

### 4. Observability Matrix Storage & Lookup

**Question**: How should the observability matrix be stored and queried efficiently?

**Decision**: YAML list of tuples + in-memory dict for O(1) lookup

**Rationale**:
- YAML format matches spec example, human-readable for configuration
- List of [observer, target, level, noise] tuples is compact and scannable
- Convert to dict[(observer, target)] → (level, noise) at startup for fast lookups
- Handles agent-to-agent and agent-to-global with same structure (target="global")

**Implementation Approach**:
```python
class ObservabilityMatrix:
    def __init__(self, entries: List[ObservabilityEntry], default: DefaultObservability):
        self._matrix = {(e.observer, e.target): (e.level, e.noise) for e in entries}
        self._default = default

    def get_observability(self, observer: str, target: str) -> tuple[ObservabilityLevel, float]:
        return self._matrix.get((observer, target), (self._default.level, self._default.noise))
```

**Alternatives Considered**:
- **Nested dict in YAML (observer → target → settings)**: Less compact, harder to scan entire matrix
- **CSV file**: External file management, parsing complexity
- **Database table**: Overkill for static configuration

**References**:
- Python dict performance characteristics
- YAML nested structure best practices

---

### 5. Integration with Orchestrator

**Question**: Where should observation construction happen in the simulation loop?

**Decision**: Orchestrator constructs observation before passing state to each agent

**Rationale**:
- Minimal change to existing orchestrator flow
- Keeps observation logic isolated in dedicated module
- Agents remain unaware of observability mechanics (clean separation)
- Allows logging of both ground truth and observations for debugging

**Implementation Approach**:
```python
# In orchestrator.py turn loop
for agent_name, agent in self.agents.items():
    if self.observability_config and self.observability_config.enabled:
        observation = construct_observation(agent_name, current_state, self.observability_config)
    else:
        observation = current_state  # Full observability

    action = await agent.decide_action(observation)
    # ... rest of turn logic
```

**Alternatives Considered**:
- **State manager handles observations**: Violates single responsibility (state ≠ observability)
- **Agents request observations**: Agents shouldn't know about observability implementation
- **Validator filters observations**: Wrong layer - validators check actions, not state visibility

**References**:
- Existing orchestrator.py structure
- Single Responsibility Principle (SRP)

---

### 6. Global State Observability

**Question**: How should agents' observability of global state be configured?

**Decision**: Treat global state like any agent, using special target ID "global" in matrix

**Rationale**:
- User clarification: "global state can be treated as an observable entity like agents"
- Reuses existing matrix structure without duplication
- Variable visibility filtering applies same way to global vars
- Maintains consistent observability semantics

**Implementation Approach**:
```yaml
observability:
  enabled: true
  variable_visibility:
    external: [interest_rate, inflation]
    internal: [central_bank_reserves]
  matrix:
    - [Agent1, global, external, 0.1]   # Agent1 sees external global vars with noise
    - [Agent2, global, insider, 0.0]     # Agent2 sees all global vars perfectly
```

**Alternatives Considered**:
- **Separate global_observability config**: Duplicates matrix logic, harder to reason about
- **Always full global visibility**: Contradicts clarification, less flexible
- **Global observability per variable**: Too granular, configuration explosion

**References**:
- User clarification note in spec.md Session 2025-10-02
- FR-006: "observer-target relationships for both other agents and global state"

---

## Technology Stack Decisions

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Configuration models | Pydantic 2.x | Already used for state, validation, type safety |
| Noise generation | Python random.Random | Built-in, deterministic with seeding |
| Matrix lookup | dict | O(1) access, simple |
| Config format | YAML | Human-readable, existing parser |
| Testing | pytest | Project standard, good fixtures |

---

## Open Questions (Deferred to Implementation)

1. **Noise at extreme values (1.0 = 100%)**: Edge case not specified - implement bounded noise (e.g., clamp to [0.01x, 100x] multiplier)
2. **Circular observability**: No validation needed - matrix is just lookup table, circles are valid
3. **Runtime variable visibility changes**: Out of scope for Phase 0 (per clarification: core only)

---

## Dependencies

### New Python Imports
- `enum.Enum` (for ObservabilityLevel)
- `random.Random` (for deterministic noise)
- No new external dependencies

### Modified Modules
- `models/config.py` - add ObservabilityConfig models
- `models/state.py` - no changes (reuse existing)
- `orchestrator.py` - add observation construction call

---

## Performance Considerations

**Observation Construction Cost**:
- O(A × V) where A = number of observable agents, V = avg variables per agent
- For 100 agents with 20 variables each: ~2000 operations per turn per observer
- Dominated by model instantiation, not filtering logic
- Acceptable for target scale (10-100 agents)

**Matrix Lookup Cost**:
- O(1) per lookup via dict
- Negligible compared to observation construction

**Memory Overhead**:
- Each observation is a full state copy (immutable Pydantic models)
- For 10 agents observing 10 agents with 20 vars: ~10 × 200 values = 2K floats (~16KB)
- Acceptable memory footprint

---

*Research complete. All technical unknowns resolved. Ready for Phase 1 design.*
