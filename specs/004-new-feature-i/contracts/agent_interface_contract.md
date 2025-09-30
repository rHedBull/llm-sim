# Agent LLM Interface Contract

**Components**:
- `llm_sim.agents.llm_agent.LLMAgent` (new abstract class)
- `llm_sim.agents.econ_llm_agent.EconLLMAgent` (new concrete class)

**Purpose**: Defines LLM reasoning infrastructure for agents and economic domain implementation

## Inheritance Hierarchy

```
Agent (existing ABC)
  ↓ inherits from
LLMAgent (new ABC) - adds LLM infrastructure
  ↓ inherits from
EconLLMAgent (concrete) - economic domain implementation
```

---

## LLMAgent (Abstract Base Class)

### Purpose
Adds LLM infrastructure to Agent ABC. Provides common LLM client management, prompt construction helpers, and retry logic. Domain-agnostic.

### Abstract Methods (must be implemented by subclasses)

#### `@abstractmethod def _construct_prompt(state: SimulationState) -> str`
**Purpose**: Domain-specific prompt construction
**Returns**: Full prompt string (system + user messages) for LLM

#### `@abstractmethod def _validate_decision(decision: PolicyDecision) -> bool`
**Purpose**: Domain-specific decision validation
**Returns**: True if decision is acceptable for this domain

### Concrete Methods (provided by LLMAgent)

#### `async def decide_action(state: SimulationState) -> Action`

**Description**: Agent observes simulation state, uses LLM to reason about it, generates policy action.

**Input Parameters**:
- `state` (SimulationState): Current simulation state with economic indicators

**Output**:
- Returns: `Action` object with:
  - `action_string`: Flexible policy description (per spec FR-013)
  - `policy_decision`: LLM-generated PolicyDecision with reasoning
  - `reasoning_chain_id`: Reference to logged LLMReasoningChain

**Behavior Guarantees**:
1. **Extract indicators** from state (GDP, inflation, unemployment, interest rate)
2. **Construct CoT prompt** with "think step-by-step" instruction (per research findings)
3. **Call LLM via LLMClient** with `PolicyDecision` response model
4. **Parse response** into PolicyDecision (action + reasoning + confidence)
5. **Log reasoning chain** at DEBUG level (per spec FR-017)
6. **Create Action** with `action_string` from PolicyDecision
7. **Retry once** on LLM failure, abort if second attempt fails (per spec FR-014, FR-016)

**Error Conditions**:
- `LLMFailureException`: Propagated from LLMClient if both LLM attempts fail (per spec FR-015, FR-016)
- `ValidationError`: If LLM response doesn't match PolicyDecision schema (triggers retry in LLMClient)

**Performance**:
- Target: <5s per decision
- Maximum: ~120s (60s × 2 attempts with backoff)

---

## EconLLMAgent (Concrete Implementation)

### Purpose
Economic domain implementation of LLMAgent. Provides economic-specific prompts and validation.

### Implemented Methods

#### `_construct_prompt(state: SimulationState) -> str`
Constructs economic policy prompt with GDP, inflation, unemployment, interest rate indicators.

#### `_validate_decision(decision: PolicyDecision) -> bool`
Validates that decision is economically relevant (mentions rates, fiscal policy, trade, etc.).

### Configuration
- **domain**: "economic"
- **prompt_style**: Chain-of-Thought with economic indicators
- **validation**: Keyword-based relevance check

---

## Prompt Templates

### LLMAgent Base (Abstract)
Provides prompt construction framework. Subclasses override with domain-specific content.

### EconLLMAgent Prompts

#### System Message
```
You are an economic policy advisor for a nation.
Analyze the current economic state and propose ONE specific policy action.
Think step-by-step about the economic situation and reasoning behind your recommendation.

Return your response as JSON with this structure:
{
  "action": "specific policy action string",
  "reasoning": "step-by-step explanation of why this action is appropriate",
  "confidence": 0.0-1.0
}
```

### User Message Format
```
Current economic state:
- GDP Growth: {gdp_growth}%
- Inflation: {inflation}%
- Unemployment: {unemployment}%
- Interest Rate: {interest_rate}%

Think step-by-step:
1. What is the most pressing economic issue?
2. What policy action would address this issue?
3. What are the expected effects?

Propose ONE specific economic policy action.
```

---

## Contract Tests

### Test 1: Successful Policy Generation
```python
@pytest.mark.asyncio
async def test_agent_generates_policy_with_llm():
    """Agent uses LLM to generate policy from state"""
    # Given: Agent with mocked LLM returning valid PolicyDecision
    mock_llm_response = PolicyDecision(
        action="Lower interest rates by 0.5%",
        reasoning="High unemployment (8%) indicates weak demand. Lower rates stimulate borrowing.",
        confidence=0.85
    )
    agent = NationAgent(name="TestNation", llm_client=mock_llm_client(mock_llm_response))

    # And: Simulation state with economic indicators
    state = SimulationState(
        turn=1,
        agents={"TestNation": AgentState(name="TestNation", economic_strength=100.0)},
        global_state=GlobalState(interest_rate=2.5, total_economic_value=1000.0)
    )

    # When: Agent decides action
    action = await agent.decide_action(state)

    # Then: Returns Action with LLM-generated policy
    assert action.agent_name == "TestNation"
    assert action.action_string == "Lower interest rates by 0.5%"
    assert action.policy_decision.reasoning.startswith("High unemployment")
    assert action.policy_decision.confidence == 0.85
    # And: Action is not yet validated
    assert action.validated is False
```

### Test 2: LLM Reasoning Chain Logged
```python
@pytest.mark.asyncio
async def test_agent_logs_reasoning_chain(caplog):
    """Agent logs full LLM reasoning at DEBUG level"""
    # Given: Agent with mocked LLM
    mock_decision = PolicyDecision(
        action="Increase taxes",
        reasoning="High inflation requires demand reduction",
        confidence=0.7
    )
    agent = NationAgent(name="TestNation", llm_client=mock_llm_client(mock_decision))

    # And: DEBUG logging enabled
    caplog.set_level(logging.DEBUG)

    # When: Agent decides action
    await agent.decide_action(state)

    # Then: Reasoning chain logged at DEBUG level
    debug_logs = [r for r in caplog.records if r.levelname == "DEBUG"]
    assert any("llm_reasoning_chain" in r.message for r in debug_logs)
    assert any("component=agent" in r.message for r in debug_logs)
    assert any("High inflation requires demand reduction" in r.message for r in debug_logs)
```

### Test 3: LLM Failure Triggers Abort
```python
@pytest.mark.asyncio
async def test_agent_aborts_on_llm_failure():
    """Agent propagates LLM failure exception to abort simulation step"""
    # Given: Agent with LLM that fails twice
    mock_client = Mock()
    mock_client.call_with_retry.side_effect = LLMFailureException(
        reason="timeout",
        attempts=2,
        component="agent"
    )
    agent = NationAgent(name="TestNation", llm_client=mock_client)

    # When: Agent attempts to decide action
    with pytest.raises(LLMFailureException) as exc_info:
        await agent.decide_action(state)

    # Then: Exception propagated (simulation step aborts per spec FR-016)
    assert exc_info.value.reason == "timeout"
    assert exc_info.value.attempts == 2
    # And: Prominent error logged (checked in LLMClient tests)
```

### Test 4: Flexible Action String (Not Enum)
```python
@pytest.mark.asyncio
async def test_agent_produces_flexible_action_string():
    """Agent action is flexible string, not typed enum"""
    # Given: Agent with LLM returning non-standard action
    mock_decision = PolicyDecision(
        action="Implement trade sanctions on neighboring countries to boost domestic production",
        reasoning="Economic independence strategy",
        confidence=0.6
    )
    agent = NationAgent(name="TestNation", llm_client=mock_llm_client(mock_decision))

    # When: Agent decides action
    action = await agent.decide_action(state)

    # Then: Action string is flexible (not limited to predefined types per spec FR-013)
    assert isinstance(action.action_string, str)
    assert "trade sanctions" in action.action_string
    assert len(action.action_string) > 20  # Descriptive, not enum-like
```

### Test 5: Prompt Construction Includes CoT
```python
@pytest.mark.asyncio
async def test_agent_constructs_cot_prompt(mocker):
    """Agent constructs prompt with Chain-of-Thought triggers"""
    # Given: Agent with spy on LLM client
    spy_client = mocker.spy(LLMClient, 'call_with_retry')
    agent = NationAgent(name="TestNation", llm_client=LLMClient(config))

    # When: Agent decides action
    await agent.decide_action(state)

    # Then: Prompt contains CoT trigger phrases
    called_prompt = spy_client.call_args[1]['prompt']
    assert "Think step-by-step" in called_prompt
    assert "What is the most pressing economic issue?" in called_prompt
    # And: Prompt includes current state indicators
    assert "GDP Growth:" in called_prompt
    assert "Inflation:" in called_prompt
```

---

## Integration Points

**Uses**:
- `llm_sim.utils.llm_client.LLMClient` → for LLM interaction with retry
- `llm_sim.models.llm_models.PolicyDecision` → response model for LLM
- `llm_sim.utils.logging` → for DEBUG-level reasoning chain logging

**Produces**:
- `Action` with `action_string` and `policy_decision` → consumed by Validator

**Configuration**: Inherits LLM config from SimulationConfig

---

## Migration from Existing Implementation

### Current Implementation (ActionType Enum)
```python
def decide_action(self, state: SimulationState) -> Action:
    # Hardcoded strategy-based decision
    if self.strategy == "grow":
        return Action(
            agent_name=self.name,
            action_type=ActionType.GROW,
            parameters={}
        )
```

### New LLM Implementation
```python
async def decide_action(self, state: SimulationState) -> Action:
    # LLM-based reasoning
    prompt = self._construct_policy_prompt(state)

    try:
        decision = await self.llm_client.call_with_retry(
            prompt=prompt,
            response_model=PolicyDecision
        )
    except LLMFailureException as e:
        logger.error("LLM_FAILURE", component="agent", agent=self.name, error=str(e))
        raise  # Abort simulation step

    # Log reasoning chain at DEBUG
    logger.debug(
        "llm_reasoning_chain",
        component="agent",
        agent_id=self.name,
        reasoning=decision.reasoning,
        confidence=decision.confidence
    )

    return Action(
        agent_name=self.name,
        action_string=decision.action,
        policy_decision=decision,
        validated=False
    )
```

---

## Version: 1.0.0
**Status**: Draft
**Last Updated**: 2025-09-30