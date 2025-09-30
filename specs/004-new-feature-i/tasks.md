# Tasks: LLM-Based Reasoning in Simulation Components

**Feature**: 004-new-feature-i
**Branch**: `004-new-feature-i`
**Input**: Design documents from `/home/hendrik/coding/llm_sim/llm_sim/specs/004-new-feature-i/`

---

## Execution Summary

This task list implements a **three-tier inheritance architecture**:
- **Tier 1**: Base ABCs (Agent, Validator, Engine) - no changes
- **Tier 2**: LLM Abstract classes (LLMAgent, LLMValidator, LLMEngine) - add LLM infrastructure
- **Tier 3**: Concrete implementations (EconLLMAgent, EconLLMValidator, EconLLMEngine) - economic domain

**Key Dependencies**:
- ollama Python client (new)
- httpx (for async LLM calls)
- tenacity (for retry logic)
- pytest-asyncio (for async tests)

**Tech Stack**: Python 3.12, Pydantic 2.x, structlog 24.x, pytest 8.x

---

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- File paths are absolute from repository root

---

## Phase 3.1: Setup & Dependencies

### T001: ✅ Add LLM dependencies to pyproject.toml
**File**: `/home/hendrik/coding/llm_sim/llm_sim/pyproject.toml`
**Action**: Add new dependencies to `[project.dependencies]`:
```toml
"ollama>=0.1.0",
"httpx>=0.25.0",
"tenacity>=8.0"
```
And to `[project.optional-dependencies]` dev section:
```toml
"pytest-asyncio>=0.23.0",
"pytest-mock>=3.12.0"
```
**Success**: Dependencies added, ready for `uv pip install -e ".[dev]"`

---

### T002: ✅ Install dependencies and verify environment
**Command**: `uv pip install -e ".[dev]"`
**Verify**:
- `python -c "import ollama; import httpx; import tenacity"` succeeds
- `pytest --version` shows pytest 8.x
**Success**: All dependencies installed without errors

---

### T003: ✅ [P] Create test directory structure
**Directories to create**:
- `/home/hendrik/coding/llm_sim/llm_sim/tests/contract/` (if not exists)
- `/home/hendrik/coding/llm_sim/llm_sim/tests/integration/` (if not exists)
**Files to create**:
- `tests/contract/__init__.py`
- `tests/integration/__init__.py`
**Success**: Directory structure ready for tests

---

## Phase 3.2: Data Models (TDD Foundation)

### T004: ✅ [P] Create llm_models.py with all LLM Pydantic models
**File**: `/home/hendrik/coding/llm_sim/llm_sim/src/llm_sim/models/llm_models.py`
**Models to implement**:
1. `LLMReasoningChain` - fields: component, agent_name (optional), prompt, response, reasoning, timestamp, duration_ms, model, retry_count
2. `PolicyDecision` - fields: action (str, 1-500 chars), reasoning (str, 10-2000 chars), confidence (float 0-1)
3. `ValidationResult` - fields: is_valid (bool), reasoning (str), confidence (float), action_evaluated (str)
4. `StateUpdateDecision` - fields: new_interest_rate (float), reasoning (str), confidence (float), action_applied (str)

**Validation rules** (from data-model.md):
- All confidence values: 0.0 ≤ x ≤ 1.0
- Reasoning strings: 10-2000 characters
- Action strings: 1-500 characters, no newlines
- retry_count: must be 0 or 1

**Success**: All 4 models defined with Pydantic validation, imports clean

---

### T005: ✅ [P] Extend Action model with LLM fields
**File**: `/home/hendrik/coding/llm_sim/llm_sim/src/llm_sim/models/action.py`
**Add fields**:
- `action_string: Optional[str] = None` (replaces action_type for LLM mode)
- `policy_decision: Optional[PolicyDecision] = None` (from llm_models)
- `validation_result: Optional[ValidationResult] = None` (populated by validator)
- `reasoning_chain_id: Optional[str] = None` (reference to LLMReasoningChain)

**Keep existing fields** (backward compatibility):
- `agent_name`, `action_type`, `parameters`, `validated`, `validation_timestamp`

**Import**: `from llm_sim.models.llm_models import PolicyDecision, ValidationResult`

**Success**: Action model extended, existing tests still pass

---

### T006: ✅ [P] Extend SimulationState model with reasoning chains
**File**: `/home/hendrik/coding/llm_sim/llm_sim/src/llm_sim/models/state.py`
**Add field**:
- `reasoning_chains: List[LLMReasoningChain] = Field(default_factory=list)` (for auditability)

**Import**: `from llm_sim.models.llm_models import LLMReasoningChain`

**Note**: State is frozen (ConfigDict(frozen=True)), so use `model_copy(update={...})` pattern for immutability

**Success**: SimulationState extended, existing tests still pass

---

### T007: ✅ [P] Create LLMConfig in config.py
**File**: `/home/hendrik/coding/llm_sim/llm_sim/src/llm_sim/models/config.py`
**Add model**:
```python
class LLMConfig(BaseModel):
    model: str = "gemma:3"
    host: str = "http://localhost:11434"
    timeout: float = 60.0
    max_retries: int = 1  # Per spec FR-014
    temperature: float = 0.7
    stream: bool = True
```

**Add to SimulationConfig**:
- `llm: Optional[LLMConfig] = None` (optional for backward compatibility)

**Success**: LLMConfig defined, SimulationConfig extended

---

### T008: ✅ [P] Extend ValidatorConfig with domain fields
**File**: `/home/hendrik/coding/llm_sim/llm_sim/src/llm_sim/models/config.py`
**Extend ValidatorConfig**:
- `domain: Optional[str] = None` (e.g., "economic", required for llm_validator)
- `permissive: bool = True` (per spec FR-005a)

**Success**: ValidatorConfig extended

---

## Phase 3.3: Contract Tests (TDD - Tests MUST FAIL before implementation)

### T009: ✅ [P] Write LLMClient contract test
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/contract/test_llm_client_contract.py`
**Tests to implement** (from contracts/llm_client_contract.md):
1. `test_llm_client_successful_first_attempt` - mock successful response, verify PolicyDecision returned, 1 call
2. `test_llm_client_retry_on_timeout` - mock timeout then success, verify 2 calls, backoff occurred
3. `test_llm_client_permanent_failure` - mock 2 failures, verify LLMFailureException raised with details
4. `test_llm_client_invalid_response_format` - mock non-JSON responses, verify retry then exception
5. `test_llm_client_fallback_json_extraction` - mock JSON wrapped in text, verify extraction works
6. `test_llm_client_no_retry_on_client_error` - mock 404, verify only 1 attempt (no retry on 4xx)

**Use**: `pytest-asyncio` for async tests, `unittest.mock.AsyncMock` for mocking

**Success**: All 6 tests written, all FAIL (LLMClient not yet implemented)

---

### T010: ✅ [P] Write LLMAgent abstract contract test
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/contract/test_llm_agent_contract.py`
**Tests to implement** (from contracts/agent_interface_contract.md):
1. `test_llm_agent_calls_abstract_methods` - verify `_construct_prompt` and `_validate_decision` are abstract
2. `test_llm_agent_decide_action_workflow` - mock LLM, verify decide_action calls prompt→LLM→log→create_action
3. `test_llm_agent_logs_reasoning_chain` - verify DEBUG log with reasoning chain created
4. `test_llm_agent_propagates_llm_failure` - mock LLM failure, verify exception propagated

**Note**: Test against a mock concrete subclass since LLMAgent is abstract

**Success**: All 4 tests written, all FAIL (LLMAgent not yet implemented)

---

### T011: ✅ [P] Write EconLLMAgent contract test
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/contract/test_econ_llm_agent_contract.py`
**Tests to implement**:
1. `test_econ_agent_generates_policy_with_llm` - mock LLM returning PolicyDecision, verify Action created
2. `test_econ_agent_constructs_economic_prompt` - verify prompt includes GDP, inflation, unemployment, interest rate
3. `test_econ_agent_validates_economic_keywords` - verify `_validate_decision` checks for economic keywords
4. `test_econ_agent_flexible_action_string` - verify action is string, not enum

**Success**: All 4 tests written, all FAIL (EconLLMAgent not yet implemented)

---

### T012: ✅ [P] Write LLMValidator abstract contract test
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/contract/test_llm_validator_contract.py`
**Tests to implement** (from contracts/validator_interface_contract.md):
1. `test_llm_validator_calls_abstract_methods` - verify `_construct_validation_prompt` and `_get_domain_description` are abstract
2. `test_llm_validator_validate_actions_workflow` - mock LLM, verify validation loop marks actions correctly
3. `test_llm_validator_logs_reasoning_chain` - verify DEBUG log for each validation
4. `test_llm_validator_returns_same_length_list` - verify output list length == input length

**Success**: All 4 tests written, all FAIL (LLMValidator not yet implemented)

---

### T013: ✅ [P] Write EconLLMValidator contract test
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/contract/test_econ_llm_validator_contract.py`
**Tests to implement**:
1. `test_econ_validator_accepts_economic_action` - mock LLM returning is_valid=True, verify action marked validated
2. `test_econ_validator_rejects_military_action` - mock LLM returning is_valid=False, verify action not validated
3. `test_econ_validator_uses_permissive_approach` - test boundary case (trade sanctions), verify accepted
4. `test_econ_validator_domain_description` - verify economic domain boundaries in prompt

**Success**: All 4 tests written, all FAIL (EconLLMValidator not yet implemented)

---

### T014: ✅ [P] Write LLMEngine abstract contract test
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/contract/test_llm_engine_contract.py`
**Tests to implement** (from contracts/engine_interface_contract.md):
1. `test_llm_engine_calls_abstract_methods` - verify `_construct_state_update_prompt` and `_apply_state_update` are abstract
2. `test_llm_engine_run_turn_workflow` - mock LLM, verify run_turn processes validated actions, skips unvalidated
3. `test_llm_engine_skips_unvalidated_with_log` - verify INFO log "SKIPPED Agent [name] due to unvalidated Action"
4. `test_llm_engine_attaches_reasoning_chains` - verify new state includes reasoning_chains

**Success**: All 4 tests written, all FAIL (LLMEngine not yet implemented)

---

### T015: ✅ [P] Write EconLLMEngine contract test
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/contract/test_econ_llm_engine_contract.py`
**Tests to implement**:
1. `test_econ_engine_processes_validated_action` - mock LLM returning new interest rate, verify state updated
2. `test_econ_engine_constructs_economic_prompt` - verify prompt includes current rate and action
3. `test_econ_engine_applies_interest_rate_update` - verify `_apply_state_update` updates only interest_rate field
4. `test_econ_engine_sequential_aggregation` - test multiple actions, verify sequential application

**Success**: All 4 tests written, all FAIL (EconLLMEngine not yet implemented)

---

## Phase 3.4: Core Implementation - Tier 1 (LLM Infrastructure)

### T016: ✅ Implement LLMClient with retry logic
**File**: `/home/hendrik/coding/llm_sim/llm_sim/src/llm_sim/utils/llm_client.py`
**Class**: `LLMClient`
**Methods**:
- `__init__(config: LLMConfig)` - initialize ollama.AsyncClient with config
- `async def call_with_retry(prompt: str, response_model: Type[BaseModel]) -> BaseModel` - main method with retry

**Implementation details** (from research.md):
- Use `tenacity` for retry: `@retry(stop=stop_after_attempt(2), wait=wait_exponential_jitter(initial=1, max=5))`
- Retry only on: 5xx errors, 429, httpx.TimeoutException
- Don't retry on: 4xx (except 429)
- Use `ollama.AsyncClient.chat()` with `format=response_model.model_json_schema()`
- Fallback JSON extraction with regex if LLM wraps JSON in text
- Log prominent ERROR on final failure: `"LLM_FAILURE: Component={component} Error={error}"`
- Always validate with Pydantic after response

**Exception**: Create `LLMFailureException(reason: str, attempts: int, status_code: Optional[int] = None)`

**Success**: T009 contract tests pass (all 6 tests)

---

## Phase 3.5: Core Implementation - Tier 2 (Abstract LLM Classes)

### T017: ✅ Implement LLMAgent abstract base class
**File**: `/home/hendrik/coding/llm_sim/llm_sim/src/llm_sim/agents/llm_agent.py`
**Class**: `LLMAgent(Agent)` - inherits from existing Agent ABC
**Abstract methods**:
- `@abstractmethod def _construct_prompt(self, state: SimulationState) -> str` - domain-specific prompt
- `@abstractmethod def _validate_decision(self, decision: PolicyDecision) -> bool` - domain validation

**Concrete methods**:
- `async def decide_action(self, state: SimulationState) -> Action` - implements Agent.decide_action
  - Call `self._construct_prompt(state)`
  - Call `self.llm_client.call_with_retry(prompt, PolicyDecision)`
  - Log reasoning at DEBUG: `logger.debug("llm_reasoning_chain", component="agent", ...)`
  - Validate decision with `self._validate_decision(decision)`
  - Create and return Action with action_string, policy_decision

**Attributes**:
- `llm_client: LLMClient` (passed in __init__)
- `name: str` (agent name)

**Success**: T010 contract tests pass (all 4 tests)

---

### T018: ✅ Implement LLMValidator abstract base class
**File**: `/home/hendrik/coding/llm_sim/llm_sim/src/llm_sim/validators/llm_validator.py`
**Class**: `LLMValidator(Validator)` - inherits from existing Validator ABC
**Abstract methods**:
- `@abstractmethod def _construct_validation_prompt(self, action: Action) -> str` - domain-specific validation prompt
- `@abstractmethod def _get_domain_description(self) -> str` - domain boundaries

**Concrete methods**:
- `async def validate_actions(self, actions: List[Action], state: SimulationState) -> List[Action]`
  - Loop through actions
  - Call `self._construct_validation_prompt(action)` for each
  - Call `self.llm_client.call_with_retry(prompt, ValidationResult)`
  - Mark action.validated = result.is_valid
  - Set action.validation_result = result
  - Log reasoning at DEBUG: `logger.debug("llm_reasoning_chain", component="validator", ...)`
  - Return modified actions list

**Attributes**:
- `llm_client: LLMClient`
- `domain: str` (e.g., "economic")
- `permissive: bool = True` (per spec FR-005a)

**Success**: T012 contract tests pass (all 4 tests)

---

### T019: ✅ Implement LLMEngine abstract base class
**File**: `/home/hendrik/coding/llm_sim/llm_sim/src/llm_sim/engines/llm_engine.py`
**Class**: `LLMEngine(Engine)` - inherits from existing Engine ABC
**Abstract methods**:
- `@abstractmethod def _construct_state_update_prompt(self, action: Action, state: GlobalState) -> str` - domain prompt
- `@abstractmethod def _apply_state_update(self, decision: StateUpdateDecision, state: SimulationState) -> SimulationState` - domain state changes

**Concrete methods**:
- `async def run_turn(self, validated_actions: List[Action]) -> SimulationState`
  - Filter to validated actions only
  - For unvalidated: log INFO `"SKIPPED Agent [{action.agent_name}] due to unvalidated Action"` (per spec FR-008)
  - For each validated action:
    - Call `self._construct_state_update_prompt(action, self.current_state.global_state)`
    - Call `self.llm_client.call_with_retry(prompt, StateUpdateDecision)`
    - Log reasoning at DEBUG: `logger.debug("llm_reasoning_chain", component="engine", ...)`
    - Accumulate reasoning chains
  - Call `self._apply_state_update(decision, self.current_state)` to create new state
  - Attach reasoning_chains to new state
  - Return new state

**Attributes**:
- `llm_client: LLMClient`
- `current_state: SimulationState` (updated after each turn)

**Success**: T014 contract tests pass (all 4 tests)

---

## Phase 3.6: Core Implementation - Tier 3 (Concrete Economic Classes)

### T020: ✅ Implement EconLLMAgent concrete class
**File**: `/home/hendrik/coding/llm_sim/llm_sim/src/llm_sim/agents/econ_llm_agent.py`
**Class**: `EconLLMAgent(LLMAgent)` - inherits from LLMAgent
**Implement abstract methods**:

`_construct_prompt(state: SimulationState) -> str`:
```python
SYSTEM_MSG = """You are an economic policy advisor for a nation.
Analyze the current economic state and propose ONE specific policy action.
Think step-by-step about the economic situation and reasoning behind your recommendation.

Return your response as JSON with this structure:
{
  "action": "specific policy action string",
  "reasoning": "step-by-step explanation of why this action is appropriate",
  "confidence": 0.0-1.0
}"""

USER_MSG = f"""Current economic state:
- GDP Growth: {state.global_state.gdp_growth}%
- Inflation: {state.global_state.inflation}%
- Unemployment: {state.global_state.unemployment}%
- Interest Rate: {state.global_state.interest_rate}%

Think step-by-step:
1. What is the most pressing economic issue?
2. What policy action would address this issue?
3. What are the expected effects?

Propose ONE specific economic policy action."""

return SYSTEM_MSG + "\n\n" + USER_MSG
```

`_validate_decision(decision: PolicyDecision) -> bool`:
- Check if action contains economic keywords: ['rate', 'rates', 'fiscal', 'tax', 'trade', 'monetary', 'interest']
- Return True if any keyword found, False otherwise

**Success**: T011 contract tests pass (all 4 tests)

---

### T021: ✅ Implement EconLLMValidator concrete class
**File**: `/home/hendrik/coding/llm_sim/llm_sim/src/llm_sim/validators/econ_llm_validator.py`
**Class**: `EconLLMValidator(LLMValidator)` - inherits from LLMValidator
**Implement abstract methods**:

`_get_domain_description() -> str`:
```python
return """Economic domain includes: interest rates, fiscal policy, trade policy, taxation, monetary policy, economic sanctions.
NON-economic domains: military actions, social policy, foreign diplomacy (unless economically focused)."""
```

`_construct_validation_prompt(action: Action) -> str`:
```python
SYSTEM_MSG = """You are a policy domain validator.
Determine if a proposed action falls within the ECONOMIC policy domain.

Economic domain includes: interest rates, fiscal policy, trade policy, taxation, monetary policy, economic sanctions.
NON-economic domains: military actions, social policy, foreign diplomacy (unless economically focused).

Use permissive validation: accept if the action has ANY significant economic impact, even if it touches other domains.

Return JSON:
{
  "is_valid": true/false,
  "reasoning": "step-by-step explanation of domain determination",
  "confidence": 0.0-1.0,
  "action_evaluated": "the action string"
}"""

USER_MSG = f"""Proposed action: "{action.action_string}"

Think step-by-step:
1. What is the primary domain of this action?
2. Does it have significant economic impact?
3. Is it within the economic policy domain?

Validate this action."""

return SYSTEM_MSG + "\n\n" + USER_MSG
```

**Success**: T013 contract tests pass (all 4 tests)

---

### T022: ✅ Implement EconLLMEngine concrete class
**File**: `/home/hendrik/coding/llm_sim/llm_sim/src/llm_sim/engines/econ_llm_engine.py`
**Class**: `EconLLMEngine(LLMEngine)` - inherits from LLMEngine
**Implement abstract methods**:

`_construct_state_update_prompt(action: Action, state: GlobalState) -> str`:
```python
SYSTEM_MSG = """You are an economic simulation engine.
Given a validated policy action, determine the new interest rate based on economic theory.

Consider:
- Current economic indicators
- Policy action effects
- Monetary policy principles

Return JSON:
{
  "new_interest_rate": float,
  "reasoning": "step-by-step explanation of how you calculated the new rate",
  "confidence": 0.0-1.0,
  "action_applied": "the action string"
}"""

USER_MSG = f"""Current state:
- Interest Rate: {state.interest_rate}%
- Inflation: {state.inflation}%
- GDP Growth: {state.gdp}%

Validated action: "{action.action_string}"

Think step-by-step:
1. How does this action affect monetary policy?
2. What interest rate adjustment is appropriate?
3. What is the new interest rate?

Calculate the new interest rate."""

return SYSTEM_MSG + "\n\n" + USER_MSG
```

`_apply_state_update(decision: StateUpdateDecision, state: SimulationState) -> SimulationState`:
```python
# Update only interest_rate (economic domain)
new_global = state.global_state.model_copy(
    update={"interest_rate": decision.new_interest_rate}
)

return SimulationState(
    turn=state.turn + 1,
    agents=state.agents,
    global_state=new_global,
    reasoning_chains=[]  # Will be populated by run_turn
)
```

**Success**: T015 contract tests pass (all 4 tests)

---

## Phase 3.7: Integration - Orchestrator Updates

### T023: ✅ Update Orchestrator to support LLM component types
**File**: `/home/hendrik/coding/llm_sim/llm_sim/src/llm_sim/orchestrator.py`
**Changes needed**:

1. **Import new classes**:
```python
from llm_sim.agents.econ_llm_agent import EconLLMAgent
from llm_sim.validators.econ_llm_validator import EconLLMValidator
from llm_sim.engines.econ_llm_engine import EconLLMEngine
from llm_sim.utils.llm_client import LLMClient
```

2. **Update `_create_agents` method**:
```python
# Initialize shared LLM client if LLM config present
llm_client = None
if self.config.llm:
    llm_client = LLMClient(config=self.config.llm)

for agent_config in self.config.agents:
    if agent_config.type == "nation":
        # Legacy agent
        agent = NationAgent(name=agent_config.name, strategy="grow")
    elif agent_config.type == "econ_llm_agent":
        # NEW: LLM-based economic agent
        if not llm_client:
            raise ValueError("LLM config required for econ_llm_agent")
        agent = EconLLMAgent(name=agent_config.name, llm_client=llm_client)
    else:
        raise ValueError(f"Unknown agent type: {agent_config.type}")
    agents.append(agent)
```

3. **Update `_create_validator` method**:
```python
if self.config.validator.type == "always_valid":
    return AlwaysValidValidator()
elif self.config.validator.type == "econ_llm_validator":
    # NEW: LLM-based economic validator
    if not self.config.llm:
        raise ValueError("LLM config required for econ_llm_validator")
    llm_client = LLMClient(config=self.config.llm)
    return EconLLMValidator(
        llm_client=llm_client,
        domain=self.config.validator.domain or "economic",
        permissive=self.config.validator.permissive
    )
else:
    raise ValueError(f"Unknown validator type: {self.config.validator.type}")
```

4. **Update `_create_engine` method**:
```python
if self.config.engine.type == "economic":
    # Legacy engine
    return EconomicEngine(self.config)
elif self.config.engine.type == "econ_llm_engine":
    # NEW: LLM-based economic engine
    if not self.config.llm:
        raise ValueError("LLM config required for econ_llm_engine")
    llm_client = LLMClient(config=self.config.llm)
    return EconLLMEngine(config=self.config, llm_client=llm_client)
else:
    raise ValueError(f"Unknown engine type: {self.config.engine.type}")
```

**Success**: Orchestrator can create LLM-based components, existing tests still pass

---

## Phase 3.8: Integration Tests (End-to-End Validation)

### T024: [P] Write LLM reasoning flow integration test
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/integration/test_llm_reasoning_flow.py`
**Test** (from quickstart.md Step 5):
- `test_full_turn_with_llm` - mock LLM for all 3 components (Agent, Validator, Engine)
- Verify full flow: Agent generates policy → Validator validates → Engine updates state
- Assert new state includes reasoning chains from all 3 components
- Assert interest rate changed based on policy
- Assert turn incremented

**Mock responses**:
- Agent: PolicyDecision with "Lower interest rates by 0.5%"
- Validator: ValidationResult with is_valid=True
- Engine: StateUpdateDecision with new_interest_rate=2.0

**Success**: Full turn completes, state updated correctly, reasoning chains attached

---

### T025: [P] Write LLM error handling integration test
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/integration/test_llm_error_handling.py`
**Tests** (from quickstart.md Step 6):
1. `test_llm_retry_and_abort` - mock LLM to fail twice
   - Verify LLMFailureException raised
   - Verify ERROR log: "LLM_FAILURE: Component=agent Agent=TestNation Error=timeout"
   - Verify simulation turn does not complete (state unchanged)

2. `test_llm_timeout_then_success` - mock timeout on first call, success on retry
   - Verify 2 LLM calls made
   - Verify backoff delay occurred
   - Verify turn completes successfully

**Success**: Error handling works per spec FR-014, FR-015, FR-016

---

### T026: [P] Write validation rejection integration test
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/integration/test_validation_rejection.py`
**Test** (from quickstart.md Step 7):
- `test_rejected_action_skipped` - mock Agent to propose military action, Validator to reject
- Verify action.validated = False
- Verify Engine logs INFO: "SKIPPED Agent [TestNation] due to unvalidated Action"
- Verify state unchanged (interest rate same, only turn incremented)
- Verify simulation continues (does not abort)

**Success**: Rejection flow works per spec FR-008

---

### T027: [P] Write multi-turn LLM simulation test
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/integration/test_multi_turn_simulation.py`
**Test**:
- `test_three_turn_simulation_with_llm` - run 3-turn simulation with 2 agents
- Mock LLM to return different policies each turn
- Verify 3 states in history (initial + 3 turns)
- Verify each state has reasoning_chains from all agents
- Verify interest rate evolves over turns
- Verify no LLM failures

**Optional**: Can use real Ollama if available (tagged with `@pytest.mark.integration`)

**Success**: Multi-turn simulation completes, reasoning chains accumulate

---

## Phase 3.9: Logging & Configuration

### T028: [P] Extend logging for DEBUG-level reasoning chains
**File**: `/home/hendrik/coding/llm_sim/llm_sim/src/llm_sim/utils/logging.py`
**Add** (if not exists):
- Ensure structlog configured with DEBUG level option
- Add helper function: `log_reasoning_chain(component: str, reasoning: str, **kwargs)` for consistent formatting

**Format**:
```python
logger.debug(
    "llm_reasoning_chain",
    component=component,  # "agent", "validator", "engine"
    agent_id=agent_id,  # optional
    reasoning=reasoning,
    confidence=confidence,
    duration_ms=duration_ms
)
```

**Success**: DEBUG logs are structured and consistent across components

---

### T029: [P] Create example LLM simulation config YAML
**File**: `/home/hendrik/coding/llm_sim/llm_sim/config_llm_example.yaml`
**Content** (from ARCHITECTURE.md):
```yaml
simulation:
  name: "Economic LLM Simulation"
  max_turns: 10

llm:
  model: "gemma:3"
  host: "http://localhost:11434"
  timeout: 60.0
  max_retries: 1
  temperature: 0.7
  stream: true

agents:
  - name: "USA"
    type: econ_llm_agent
  - name: "EU"
    type: econ_llm_agent

validator:
  type: econ_llm_validator
  domain: economic
  permissive: true

engine:
  type: econ_llm_engine

logging:
  level: DEBUG
  format: json
```

**Success**: Example config created, ready for testing

---

## Phase 3.10: Unit Tests for New Components

### T030: [P] Write unit tests for LLMClient
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/unit/test_llm_client.py`
**Tests**:
- Test retry logic (exponential backoff, jitter)
- Test error classification (retry 5xx, don't retry 4xx)
- Test timeout handling
- Test JSON extraction fallback
- Test Pydantic validation

**Success**: LLMClient thoroughly unit tested

---

### T031: [P] Write unit tests for LLM Pydantic models
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/unit/test_llm_models.py`
**Tests**:
- Test validation rules for all 4 models (LLMReasoningChain, PolicyDecision, ValidationResult, StateUpdateDecision)
- Test confidence bounds (0.0-1.0)
- Test string length constraints
- Test immutability (Pydantic frozen models)

**Success**: All model validation rules enforced

---

### T032: [P] Write unit tests for EconLLMAgent
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/unit/test_econ_llm_agent.py`
**Tests**:
- Test `_construct_prompt` includes all economic indicators
- Test `_validate_decision` recognizes economic keywords
- Test decide_action integration (with mocked LLMClient)

**Success**: EconLLMAgent logic tested independently

---

### T033: [P] Write unit tests for EconLLMValidator
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/unit/test_econ_llm_validator.py`
**Tests**:
- Test `_get_domain_description` returns economic boundaries
- Test `_construct_validation_prompt` includes domain description
- Test permissive validation mode
- Test validate_actions integration (with mocked LLMClient)

**Success**: EconLLMValidator logic tested independently

---

### T034: [P] Write unit tests for EconLLMEngine
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/unit/test_econ_llm_engine.py`
**Tests**:
- Test `_construct_state_update_prompt` includes current rate and action
- Test `_apply_state_update` only updates interest_rate
- Test sequential aggregation (multiple actions)
- Test run_turn integration (with mocked LLMClient)

**Success**: EconLLMEngine logic tested independently

---

## Phase 3.11: Polish & Documentation

### T035: Run quickstart validation
**File**: `/home/hendrik/coding/llm_sim/llm_sim/specs/004-new-feature-i/quickstart.md`
**Action**: Execute all 7 steps from quickstart.md manually:
1. Verify LLM client works
2. Verify Agent LLM integration
3. Verify Validator LLM integration
4. Verify Engine LLM integration
5. End-to-end reasoning flow
6. Error handling validation
7. Validation rejection flow

**Prerequisites**:
- Ollama running locally
- gemma:3 model pulled

**Success**: All quickstart steps pass

---

### T036: [P] Run full test suite and verify coverage
**Command**: `pytest tests/ -v --cov=src/llm_sim --cov-report=term-missing`
**Success criteria**:
- All tests pass
- Coverage >80% for new files (llm_client.py, llm_agent.py, econ_llm_agent.py, etc.)
- No flaky tests

**Success**: Test suite green, coverage acceptable

---

### T037: [P] Update project README with LLM feature
**File**: `/home/hendrik/coding/llm_sim/llm_sim/README.md`
**Add section**: "LLM-Based Reasoning"
- Describe three-tier architecture
- Link to ARCHITECTURE.md
- Show example config with econ_llm_agent
- Prerequisites (Ollama, gemma:3)
- Quick start command

**Success**: README updated, users can understand LLM feature

---

### T038: Performance validation (LLM latency)
**Action**: Run a 10-turn simulation with 10 agents, measure:
- Average LLM call time (<5s target per spec)
- Average simulation step time (<30s target per spec)
- Total simulation time

**Log results**: Document actual performance vs. targets

**Success**: Performance meets or approaches targets (within 20%)

---

### T039: Code quality check
**Commands**:
- `black src/ tests/` (format code)
- `ruff check src/ tests/` (lint code)
- `mypy src/llm_sim` (type checking)

**Success**: No linting errors, type checking passes

---

### T040: Final integration test with real Ollama (optional)
**File**: `/home/hendrik/coding/llm_sim/llm_sim/tests/e2e/test_llm_real_simulation.py`
**Test** (tagged `@pytest.mark.slow`):
- Run 3-turn simulation with real Ollama (no mocks)
- Verify LLM generates realistic policies
- Verify reasoning chains are coherent
- Verify state updates are logical

**Prerequisites**: Ollama running, gemma:3 available

**Success**: Real LLM simulation works end-to-end

---

## Dependencies Graph

```
Setup (T001-T003)
  ↓
Data Models [P] (T004-T008)
  ↓
Contract Tests [P] (T009-T015) ← MUST FAIL before implementation
  ↓
LLM Infrastructure (T016)
  ↓
Abstract Classes [P] (T017-T019)
  ↓
Concrete Classes [P] (T020-T022)
  ↓
Orchestrator (T023)
  ↓
Integration Tests [P] (T024-T027)
  ↓
Config & Logging [P] (T028-T029)
  ↓
Unit Tests [P] (T030-T034)
  ↓
Polish [P] (T035-T040)
```

---

## Parallel Execution Examples

### Launch all contract tests together (T009-T015):
```bash
# All 7 contract test files can run in parallel (different files)
pytest tests/contract/test_llm_client_contract.py \
      tests/contract/test_llm_agent_contract.py \
      tests/contract/test_econ_llm_agent_contract.py \
      tests/contract/test_llm_validator_contract.py \
      tests/contract/test_econ_llm_validator_contract.py \
      tests/contract/test_llm_engine_contract.py \
      tests/contract/test_econ_llm_engine_contract.py \
      -n 7  # pytest-xdist for parallel execution
```

### Launch abstract class implementations together (T017-T019):
```bash
# Can implement all 3 abstract classes in parallel (different files)
# T017: src/llm_sim/agents/llm_agent.py
# T018: src/llm_sim/validators/llm_validator.py
# T019: src/llm_sim/engines/llm_engine.py
```

### Launch concrete class implementations together (T020-T022):
```bash
# Can implement all 3 concrete classes in parallel (different files)
# T020: src/llm_sim/agents/econ_llm_agent.py
# T021: src/llm_sim/validators/econ_llm_validator.py
# T022: src/llm_sim/engines/econ_llm_engine.py
```

---

## Validation Checklist

- [x] All 4 contracts have corresponding tests (T009-T015)
- [x] All 4 entities have model tasks (T004-T008)
- [x] All tests come before implementation (Phase 3.3 before 3.4-3.6)
- [x] Parallel tasks truly independent (different files, marked [P])
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] TDD enforced: Contract tests MUST FAIL before implementation

---

## Notes

- **Backward compatibility**: Legacy components (NationAgent, AlwaysValidValidator, EconomicEngine) unchanged
- **Three-tier pattern**: Enables future domains (military, social) by extending abstract LLM classes
- **TDD discipline**: All contract tests (T009-T015) must fail before implementation starts
- **Ollama requirement**: Tests can mock LLM, but real validation requires Ollama + gemma:3
- **Async everywhere**: All LLM calls are async (use pytest-asyncio)
- **Error handling**: Retry once, abort on second failure with prominent log (spec FR-014-FR-016)
- **Logging**: DEBUG level for reasoning chains (spec FR-017), INFO for skipped agents (spec FR-008)

---

**Total Tasks**: 40
**Estimated Parallel Tasks**: 24 (marked [P])
**Estimated Sequential Tasks**: 16

**Execution Time Estimate**:
- Setup: 10 minutes
- Contract tests: 2 hours (TDD)
- Implementation: 6-8 hours (T016-T023)
- Integration/Unit tests: 3 hours
- Polish: 1 hour
- **Total**: 12-14 hours (with parallel execution where possible)

---

**Ready for execution**. Use `/implement` or execute tasks manually in order.