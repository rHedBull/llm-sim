# Engine LLM Interface Contract

**Components**:
- `llm_sim.engines.llm_engine.LLMEngine` (new abstract class)
- `llm_sim.engines.econ_llm_engine.EconLLMEngine` (new concrete class)

**Purpose**: Defines LLM state update infrastructure and economic domain implementation

## Inheritance Hierarchy

```
Engine (existing ABC)
  ↓ inherits from
LLMEngine (new ABC) - adds LLM state reasoning infrastructure
  ↓ inherits from
EconLLMEngine (concrete) - economic domain implementation
```

---

## LLMEngine (Abstract Base Class)

### Purpose
Adds LLM state reasoning infrastructure to Engine ABC. Provides common LLM client management, state update prompt framework, and reasoning chain aggregation. Domain-agnostic.

### Abstract Methods (must be implemented by subclasses)

#### `@abstractmethod def _construct_state_update_prompt(action: Action, current_state: GlobalState) -> str`
**Purpose**: Domain-specific state update prompt construction
**Returns**: Full prompt string for LLM state reasoning

#### `@abstractmethod def _apply_state_update(decision: StateUpdateDecision, current_state: SimulationState) -> SimulationState`
**Purpose**: Domain-specific state update application
**Returns**: New SimulationState with updates applied

### Concrete Methods (provided by LLMEngine)

#### `async def run_turn(validated_actions: List[Action]) -> SimulationState`

**Description**: Processes validated actions using LLM reasoning to compute new simulation state.

**Input Parameters**:
- `validated_actions` (List[Action]): Actions marked as validated by Validator

**Output**:
- Returns: New `SimulationState` with updated interest rate and reasoning chains

**Behavior Guarantees**:
1. **Filter to validated actions only** (skip actions with `validated=False` per spec FR-008)
2. **For each validated action**:
   - Construct state update prompt with current state + action
   - Call LLM via LLMClient with `StateUpdateDecision` response model
   - Parse response into StateUpdateDecision (new_interest_rate + reasoning)
   - Log reasoning chain at DEBUG level (per spec FR-017)
3. **Apply state updates** to create new SimulationState
4. **Attach all reasoning chains** to new state (for auditability per spec FR-017)
5. **Retry once** on LLM failure, abort if second attempt fails (per spec FR-014, FR-016)
6. **Log INFO message** when skipping unvalidated action (per spec FR-008)

**Error Conditions**:
- `LLMFailureException`: Propagated from LLMClient if both LLM attempts fail (aborts turn per spec FR-016)
- `ValidationError`: If LLM response doesn't match StateUpdateDecision schema (triggers retry in LLMClient)

**Performance**:
- Target: <5s per action processing
- Maximum: ~120s per action (60s × 2 attempts with backoff)

---

## EconLLMEngine (Concrete Implementation)

### Purpose
Economic domain implementation of LLMEngine. Handles interest rate updates based on economic policy actions.

### Implemented Methods

#### `_construct_state_update_prompt(action: Action, current_state: GlobalState) -> str`
Constructs economic state update prompt with current rate, economic indicators, and policy action.

#### `_apply_state_update(decision: StateUpdateDecision, current_state: SimulationState) -> SimulationState`
Applies interest rate change from StateUpdateDecision to create new SimulationState. Updates turn counter and attaches reasoning chains.

### Configuration
- **domain**: "economic"
- **state_fields**: ["interest_rate"] (primary field modified)
- **aggregation_strategy**: Sequential (apply actions one-by-one)

---

## Prompt Templates

### LLMEngine Base (Abstract)
Provides state update prompt framework. Subclasses override with domain-specific state fields.

### EconLLMEngine Prompts

#### System Message
```
You are an economic simulation engine.
Given a validated policy action, determine the new interest rate based on economic theory.

Consider:
- Current economic indicators
- Policy action effects
- Monetary policy principles

Return JSON:
{
  "new_interest_rate": float,
  "reasoning": "step-by-step explanation of how you calculated the new rate",
  "confidence": 0.0-1.0
}
```

### User Message Format
```
Current state:
- Interest Rate: {current_rate}%
- Inflation: {inflation}%
- GDP Growth: {gdp}%

Validated action: "{action_string}"

Think step-by-step:
1. How does this action affect monetary policy?
2. What interest rate adjustment is appropriate?
3. What is the new interest rate?

Calculate the new interest rate.
```

---

## Contract Tests

### Test 1: Processes Validated Action with LLM
```python
@pytest.mark.asyncio
async def test_engine_processes_validated_action():
    """Engine uses LLM to compute state update from validated action"""
    # Given: Engine with mocked LLM returning state update
    mock_decision = StateUpdateDecision(
        new_interest_rate=2.0,
        reasoning="Action proposes lowering rates by 0.5%. Current rate 2.5%, new rate 2.0%.",
        confidence=0.9,
        action_applied="Lower interest rates by 0.5%"
    )
    engine = EconomicEngine(config=config, llm_client=mock_llm_client(mock_decision))

    # And: Validated action
    action = Action(
        agent_name="TestNation",
        action_string="Lower interest rates by 0.5%",
        validated=True,
        validation_result=ValidationResult(is_valid=True, ...)
    )

    # And: Current state with 2.5% interest rate
    current_state = SimulationState(
        turn=1,
        agents={...},
        global_state=GlobalState(interest_rate=2.5, total_economic_value=1000.0)
    )
    engine.current_state = current_state

    # When: Running turn with validated action
    new_state = await engine.run_turn([action])

    # Then: New state has updated interest rate
    assert new_state.global_state.interest_rate == 2.0
    assert new_state.turn == 2
    # And: State includes reasoning chain
    assert len(new_state.reasoning_chains) > 0
    assert any("component=engine" in str(chain) for chain in new_state.reasoning_chains)
```

### Test 2: Skips Unvalidated Action
```python
@pytest.mark.asyncio
async def test_engine_skips_unvalidated_action(caplog):
    """Engine skips action with validated=False and logs INFO message"""
    # Given: Engine with LLM client
    engine = EconomicEngine(config=config, llm_client=llm_client)

    # And: Unvalidated action (rejected by Validator)
    action = Action(
        agent_name="TestNation",
        action_string="Deploy military forces",
        validated=False,
        validation_result=ValidationResult(is_valid=False, ...)
    )

    # And: INFO logging enabled
    caplog.set_level(logging.INFO)

    # When: Running turn with unvalidated action
    new_state = await engine.run_turn([action])

    # Then: Action was skipped (state unchanged except turn increment)
    assert new_state.global_state.interest_rate == engine.current_state.global_state.interest_rate
    # And: INFO log message generated (per spec FR-008)
    info_logs = [r.message for r in caplog.records if r.levelname == "INFO"]
    assert any("SKIPPED Agent [TestNation] due to unvalidated Action" in msg for msg in info_logs)
```

### Test 3: Reasoning Chain Logged at DEBUG
```python
@pytest.mark.asyncio
async def test_engine_logs_reasoning_chain(caplog):
    """Engine logs full LLM reasoning at DEBUG level"""
    # Given: Engine with mocked LLM
    mock_decision = StateUpdateDecision(
        new_interest_rate=3.0,
        reasoning="Inflation high, increase rates to cool economy.",
        confidence=0.85,
        action_applied="Increase interest rates"
    )
    engine = EconomicEngine(config=config, llm_client=mock_llm_client(mock_decision))

    # And: DEBUG logging enabled
    caplog.set_level(logging.DEBUG)

    # When: Processing validated action
    await engine.run_turn([validated_action])

    # Then: Reasoning chain logged at DEBUG level (per spec FR-017)
    debug_logs = [r.message for r in caplog.records if r.levelname == "DEBUG"]
    assert any("llm_reasoning_chain" in msg for msg in debug_logs)
    assert any("component=engine" in msg for msg in debug_logs)
    assert any("cool economy" in msg for msg in debug_logs)
```

### Test 4: LLM Failure Aborts Turn
```python
@pytest.mark.asyncio
async def test_engine_aborts_on_llm_failure():
    """Engine propagates LLM failure to abort simulation turn"""
    # Given: Engine with LLM that fails twice
    mock_client = Mock()
    mock_client.call_with_retry.side_effect = LLMFailureException(
        reason="server_error",
        attempts=2,
        component="engine"
    )
    engine = EconomicEngine(config=config, llm_client=mock_client)

    # When: Attempting to run turn
    with pytest.raises(LLMFailureException) as exc_info:
        await engine.run_turn([validated_action])

    # Then: Exception propagated (simulation turn aborts per spec FR-016)
    assert exc_info.value.reason == "server_error"
    assert exc_info.value.component == "engine"
    # And: State remains unchanged (turn not incremented)
```

### Test 5: Multiple Actions Processed Sequentially
```python
@pytest.mark.asyncio
async def test_engine_processes_multiple_actions():
    """Engine processes multiple validated actions in sequence"""
    # Given: Engine with LLM returning different updates per action
    engine = EconomicEngine(config=config, llm_client=mock_llm_client_sequence([
        StateUpdateDecision(new_interest_rate=2.0, reasoning="Lower by 0.5%", ...),
        StateUpdateDecision(new_interest_rate=1.8, reasoning="Further lower by 0.2%", ...)
    ]))

    # And: Multiple validated actions
    actions = [
        Action(agent_name="Nation1", action_string="Lower rates 0.5%", validated=True, ...),
        Action(agent_name="Nation2", action_string="Lower rates 0.2%", validated=True, ...)
    ]

    # When: Running turn with multiple actions
    new_state = await engine.run_turn(actions)

    # Then: State reflects cumulative updates
    # (exact behavior depends on aggregation strategy - sum, average, or last-wins)
    assert new_state.global_state.interest_rate != engine.current_state.global_state.interest_rate
    # And: Multiple reasoning chains attached
    assert len(new_state.reasoning_chains) >= 2
```

### Test 6: Reasoning Chains Attached to State
```python
@pytest.mark.asyncio
async def test_engine_attaches_reasoning_chains_to_state():
    """Engine includes all reasoning chains in new state for auditability"""
    # Given: Engine with mocked LLM
    mock_decision = StateUpdateDecision(
        new_interest_rate=2.5,
        reasoning="Maintain current rate due to stable indicators.",
        confidence=0.8,
        action_applied="Maintain interest rates"
    )
    engine = EconomicEngine(config=config, llm_client=mock_llm_client(mock_decision))

    # When: Running turn
    new_state = await engine.run_turn([validated_action])

    # Then: New state contains reasoning chains (per spec FR-017, FR-018)
    assert hasattr(new_state, 'reasoning_chains')
    assert len(new_state.reasoning_chains) > 0
    # And: Chains include engine component
    engine_chains = [c for c in new_state.reasoning_chains if c.component == "engine"]
    assert len(engine_chains) >= 1
    # And: Reasoning is accessible
    assert "stable indicators" in engine_chains[0].reasoning
```

---

## Integration Points

**Uses**:
- `llm_sim.utils.llm_client.LLMClient` → for LLM interaction with retry
- `llm_sim.models.llm_models.StateUpdateDecision` → response model for LLM
- `llm_sim.utils.logging` → for DEBUG-level reasoning chain logging

**Consumes**:
- `Action` with `validated=True` and `validation_result` from Validator

**Produces**:
- `SimulationState` with updated interest rate and reasoning chains → returned to Orchestrator

**Configuration**: Inherits LLM config from SimulationConfig

---

## State Aggregation Strategy

When multiple validated actions exist in a turn, the Engine must decide how to aggregate state updates:

### Option 1: Sequential Application (Recommended)
```python
# Apply each action's update sequentially
current_rate = self.current_state.global_state.interest_rate
for action in validated_actions:
    decision = await self._get_state_update(action, current_rate)
    current_rate = decision.new_interest_rate
    reasoning_chains.append(decision)

new_state = self._create_state(interest_rate=current_rate, reasoning_chains=reasoning_chains)
```

### Option 2: Averaging
```python
# Average all proposed updates
decisions = [await self._get_state_update(action) for action in validated_actions]
avg_rate = sum(d.new_interest_rate for d in decisions) / len(decisions)
new_state = self._create_state(interest_rate=avg_rate, reasoning_chains=decisions)
```

### Option 3: LLM Meta-Reasoning
```python
# Ask LLM to synthesize all proposed updates
all_proposals = [f"Action: {a.action_string} -> Rate: {d.new_interest_rate}" for a, d in zip(actions, decisions)]
final_decision = await self.llm_client.call_with_retry(
    prompt=f"Synthesize these rate proposals: {all_proposals}",
    response_model=FinalStateDecision
)
```

**Decision for this feature**: Use **Sequential Application** for simplicity and clear audit trail.

---

## Prompt Construction Example

```python
def _construct_state_update_prompt(
    self,
    action: Action,
    current_state: GlobalState
) -> str:
    return f"""Current state:
- Interest Rate: {current_state.interest_rate}%
- Total Economic Value: {current_state.total_economic_value}

Validated action: "{action.action_string}"
Agent reasoning: "{action.policy_decision.reasoning}"

Think step-by-step:
1. How does this action affect monetary policy?
2. What interest rate adjustment is appropriate?
3. What is the new interest rate?

Calculate the new interest rate."""
```

---

## Version: 1.0.0
**Status**: Draft
**Last Updated**: 2025-09-30