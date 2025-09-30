# Validator LLM Interface Contract

**Components**:
- `llm_sim.validators.llm_validator.LLMValidator` (new abstract class)
- `llm_sim.validators.econ_llm_validator.EconLLMValidator` (new concrete class)

**Purpose**: Defines LLM validation infrastructure and economic domain implementation

## Inheritance Hierarchy

```
Validator (existing ABC)
  ↓ inherits from
LLMValidator (new ABC) - adds LLM validation infrastructure
  ↓ inherits from
EconLLMValidator (concrete) - economic domain implementation
```

---

## LLMValidator (Abstract Base Class)

### Purpose
Adds LLM validation infrastructure to Validator ABC. Provides common LLM client management, validation prompt framework, and reasoning chain logging. Domain-agnostic.

### Abstract Methods (must be implemented by subclasses)

#### `@abstractmethod def _construct_validation_prompt(action: Action) -> str`
**Purpose**: Domain-specific validation prompt construction
**Returns**: Full prompt string for LLM domain validation

#### `@abstractmethod def _get_domain_description() -> str`
**Purpose**: Returns domain boundaries description
**Returns**: String describing what's in/out of domain (used in prompts)

### Concrete Methods (provided by LLMValidator)

#### `async def validate_actions(actions: List[Action], state: SimulationState) -> List[Action]`

**Description**: Validates each action using LLM reasoning to determine domain validity, marks valid actions.

**Input Parameters**:
- `actions` (List[Action]): List of agent actions to validate
- `state` (SimulationState): Current simulation state (for context, if needed)

**Output**:
- Returns: List of actions with `validated` field updated and `validation_result` populated
- Same length as input (does not filter, only marks validation status)

**Behavior Guarantees**:
1. **Iterate through actions** and validate each independently
2. **Construct domain validation prompt** with action string and domain guidelines
3. **Call LLM via LLMClient** with `ValidationResult` response model
4. **Parse response** into ValidationResult (is_valid + reasoning + confidence)
5. **Mark action as validated** if `is_valid` is True (per spec FR-007)
6. **Log reasoning chain** at DEBUG level (per spec FR-017)
7. **Use permissive validation** approach (accept if ANY domain impact, per spec FR-005a)
8. **Retry once** on LLM failure, abort if second attempt fails (per spec FR-014, FR-016)

**Error Conditions**:
- `LLMFailureException`: Propagated from LLMClient if both LLM attempts fail (aborts simulation per spec FR-016)
- `ValidationError`: If LLM response doesn't match ValidationResult schema (triggers retry in LLMClient)

**Performance**:
- Target: <5s per action validation
- Maximum: ~120s per action (60s × 2 attempts with backoff)

---

## EconLLMValidator (Concrete Implementation)

### Purpose
Economic domain implementation of LLMValidator. Defines economic domain boundaries and validation logic.

### Implemented Methods

#### `_construct_validation_prompt(action: Action) -> str`
Constructs validation prompt with economic domain boundaries and action to evaluate.

#### `_get_domain_description() -> str`
Returns: "Economic domain includes: interest rates, fiscal policy, trade policy, taxation, monetary policy, economic sanctions. NON-economic domains: military actions, social policy, foreign diplomacy (unless economically focused)."

### Configuration
- **domain**: "economic"
- **permissive**: True (per spec FR-005a - accept if ANY economic impact)

---

## Prompt Templates

### LLMValidator Base (Abstract)
Provides validation prompt framework. Subclasses override with domain-specific boundaries.

### EconLLMValidator Prompts

#### System Message
```
You are a policy domain validator.
Determine if a proposed action falls within the ECONOMIC policy domain.

Economic domain includes: interest rates, fiscal policy, trade policy, taxation, monetary policy, economic sanctions.
NON-economic domains: military actions, social policy, foreign diplomacy (unless economically focused).

Use permissive validation: accept if the action has ANY significant economic impact, even if it touches other domains.

Return JSON:
{
  "is_valid": true/false,
  "reasoning": "step-by-step explanation of domain determination",
  "confidence": 0.0-1.0
}
```

### User Message Format
```
Proposed action: "{action_string}"

Think step-by-step:
1. What is the primary domain of this action?
2. Does it have significant economic impact?
3. Is it within the economic policy domain?

Validate this action.
```

---

## Contract Tests

### Test 1: Valid Economic Action
```python
@pytest.mark.asyncio
async def test_validator_accepts_economic_action():
    """Validator accepts action with clear economic domain"""
    # Given: Validator with mocked LLM returning valid result
    mock_validation = ValidationResult(
        is_valid=True,
        reasoning="Action targets interest rates, which is core economic policy.",
        confidence=0.95,
        action_evaluated="Lower interest rates by 0.5%"
    )
    validator = LLMValidator(llm_client=mock_llm_client(mock_validation), domain="economic")

    # And: Action from agent
    action = Action(
        agent_name="TestNation",
        action_string="Lower interest rates by 0.5%",
        policy_decision=PolicyDecision(...)
    )

    # When: Validating actions
    validated = await validator.validate_actions([action], state)

    # Then: Action marked as validated
    assert validated[0].validated is True
    assert validated[0].validation_result.is_valid is True
    assert "interest rates" in validated[0].validation_result.reasoning
```

### Test 2: Invalid Military Action
```python
@pytest.mark.asyncio
async def test_validator_rejects_military_action():
    """Validator rejects action outside economic domain"""
    # Given: Validator with mocked LLM rejecting military action
    mock_validation = ValidationResult(
        is_valid=False,
        reasoning="Action is military deployment, no significant economic impact detected.",
        confidence=0.9,
        action_evaluated="Deploy military forces to border"
    )
    validator = LLMValidator(llm_client=mock_llm_client(mock_validation), domain="economic")

    # And: Military action from agent
    action = Action(
        agent_name="TestNation",
        action_string="Deploy military forces to border",
        policy_decision=PolicyDecision(...)
    )

    # When: Validating actions
    validated = await validator.validate_actions([action], state)

    # Then: Action marked as NOT validated
    assert validated[0].validated is False
    assert validated[0].validation_result.is_valid is False
    assert "military" in validated[0].validation_result.reasoning.lower()
```

### Test 3: Permissive Validation for Boundary Case
```python
@pytest.mark.asyncio
async def test_validator_uses_permissive_approach():
    """Validator accepts action with mixed domains if economic impact exists"""
    # Given: Validator with permissive validation enabled
    mock_validation = ValidationResult(
        is_valid=True,
        reasoning="Trade sanctions have significant economic impact (trade balance, GDP), accepted under permissive validation.",
        confidence=0.7,
        action_evaluated="Implement trade sanctions on neighboring countries"
    )
    validator = LLMValidator(
        llm_client=mock_llm_client(mock_validation),
        domain="economic",
        permissive=True
    )

    # And: Action that touches multiple domains
    action = Action(
        agent_name="TestNation",
        action_string="Implement trade sanctions on neighboring countries",
        policy_decision=PolicyDecision(...)
    )

    # When: Validating actions
    validated = await validator.validate_actions([action], state)

    # Then: Action accepted due to permissive mode (per spec FR-005a)
    assert validated[0].validated is True
    assert "economic impact" in validated[0].validation_result.reasoning.lower()
```

### Test 4: Reasoning Chain Logged
```python
@pytest.mark.asyncio
async def test_validator_logs_reasoning_chain(caplog):
    """Validator logs full LLM reasoning at DEBUG level"""
    # Given: Validator with mocked LLM
    mock_validation = ValidationResult(
        is_valid=True,
        reasoning="Fiscal policy action, clearly economic domain.",
        confidence=0.95,
        action_evaluated="Increase government spending"
    )
    validator = LLMValidator(llm_client=mock_llm_client(mock_validation), domain="economic")

    # And: DEBUG logging enabled
    caplog.set_level(logging.DEBUG)

    # When: Validating action
    await validator.validate_actions([action], state)

    # Then: Reasoning chain logged at DEBUG level
    debug_logs = [r for r in caplog.records if r.levelname == "DEBUG"]
    assert any("llm_reasoning_chain" in r.message for r in debug_logs)
    assert any("component=validator" in r.message for r in debug_logs)
    assert any("Fiscal policy action" in r.message for r in debug_logs)
```

### Test 5: Multiple Actions Validated Independently
```python
@pytest.mark.asyncio
async def test_validator_processes_multiple_actions():
    """Validator validates each action independently"""
    # Given: Validator with LLM returning different results per action
    validator = LLMValidator(llm_client=mock_llm_client_sequence([
        ValidationResult(is_valid=True, reasoning="Economic", confidence=0.9, action_evaluated="action1"),
        ValidationResult(is_valid=False, reasoning="Military", confidence=0.85, action_evaluated="action2")
    ]), domain="economic")

    # And: Multiple actions
    actions = [
        Action(agent_name="Nation1", action_string="Lower interest rates", ...),
        Action(agent_name="Nation2", action_string="Deploy troops", ...)
    ]

    # When: Validating all actions
    validated = await validator.validate_actions(actions, state)

    # Then: Each action has independent validation result
    assert validated[0].validated is True
    assert validated[1].validated is False
    assert len(validated) == 2  # Same length as input
```

### Test 6: LLM Failure Aborts Validation
```python
@pytest.mark.asyncio
async def test_validator_aborts_on_llm_failure():
    """Validator propagates LLM failure to abort simulation"""
    # Given: Validator with LLM that fails twice
    mock_client = Mock()
    mock_client.call_with_retry.side_effect = LLMFailureException(
        reason="timeout",
        attempts=2,
        component="validator"
    )
    validator = LLMValidator(llm_client=mock_client, domain="economic")

    # When: Attempting to validate action
    with pytest.raises(LLMFailureException) as exc_info:
        await validator.validate_actions([action], state)

    # Then: Exception propagated (simulation step aborts per spec FR-016)
    assert exc_info.value.reason == "timeout"
    assert exc_info.value.component == "validator"
```

---

## Integration Points

**Uses**:
- `llm_sim.utils.llm_client.LLMClient` → for LLM interaction with retry
- `llm_sim.models.llm_models.ValidationResult` → response model for LLM
- `llm_sim.utils.logging` → for DEBUG-level reasoning chain logging

**Consumes**:
- `Action` with `action_string` and `policy_decision` from Agent

**Produces**:
- `Action` with `validated=True/False` and `validation_result` populated → consumed by Engine

**Configuration**: Reads `ValidatorConfig` with domain and permissive fields

---

## Engine Integration (Rejection Handling)

Per spec FR-008, when Validator marks action as `validated=False`:

```python
# In Engine.run_turn()
for action in validated_actions:
    if not action.validated:
        logger.info(
            "agent_skipped",
            agent=action.agent_name,
            reason="unvalidated_action",
            message=f"SKIPPED Agent [{action.agent_name}] due to unvalidated Action"
        )
        continue  # Skip this agent, proceed to next

    # Process validated action
    ...
```

---

## Validator Statistics

Validator should track validation statistics for observability:

```python
def get_stats(self) -> Dict[str, int]:
    return {
        "total_validated": self.total_count,
        "accepted": self.accepted_count,
        "rejected": self.rejected_count,
        "rejection_rate": self.rejected_count / self.total_count if self.total_count > 0 else 0
    }
```

---

## Prompt Customization by Domain

The validator system message should be configurable per domain:

```python
DOMAIN_PROMPTS = {
    "economic": """
    Economic domain includes: interest rates, fiscal policy, trade policy, taxation, monetary policy, economic sanctions.
    NON-economic domains: military actions, social policy, foreign diplomacy (unless economically focused).
    """,
    "military": """
    Military domain includes: troop deployment, defense systems, military alliances, combat operations.
    NON-military domains: economic policy, social programs, unless directly supporting military operations.
    """,
    # Additional domains can be added
}
```

---

## Version: 1.0.0
**Status**: Draft
**Last Updated**: 2025-09-30