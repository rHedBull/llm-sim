# LLM Pattern Documentation

The LLM patterns provide abstract base classes that integrate LLM reasoning into the simulation framework. These patterns handle LLM infrastructure (client management, retry logic, logging) while requiring domain-specific implementations.

## Overview

The LLM pattern classes extend the base classes and add:
- LLM client integration with retry logic
- Structured prompt construction
- Reasoning chain tracking
- Confidence scoring
- Async operation support

## LLMAgent Pattern

The `LLMAgent` pattern enables agents to use LLM reasoning for decision-making.

**Location**: `llm_sim.infrastructure.patterns.llm_agent`

### Interface

```python
from abc import abstractmethod
from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.models.action import Action, LLMAction
from llm_sim.models.llm_models import PolicyDecision
from llm_sim.models.state import SimulationState
from llm_sim.utils.llm_client import LLMClient

class LLMAgent(BaseAgent):
    """Abstract base class for agents that use LLM reasoning."""

    def __init__(self, name: str, llm_client: LLMClient):
        super().__init__(name=name)
        self.llm_client = llm_client

    @abstractmethod
    def _construct_prompt(self, state: SimulationState) -> str:
        """Construct domain-specific prompt for LLM."""
        pass

    @abstractmethod
    def _validate_decision(self, decision: PolicyDecision) -> bool:
        """Validate that decision is within domain boundaries."""
        pass

    async def decide_action(self, state: SimulationState) -> Action:
        """Generate action using LLM reasoning (implemented)."""
        # Handles: prompt construction, LLM call, validation, logging
        pass
```

### Required Methods

- **`_construct_prompt(state) -> str`**: Build the prompt with domain context
- **`_validate_decision(decision) -> bool`**: Check if decision fits domain rules

### What the Pattern Provides

The `decide_action()` method handles:
1. Prompt construction via `_construct_prompt()`
2. LLM API call with automatic retry
3. Response parsing into `PolicyDecision`
4. Decision validation via `_validate_decision()`
5. Reasoning chain logging (DEBUG level)
6. Action creation with metadata

### Example Implementation

```python
from llm_sim.infrastructure.patterns.llm_agent import LLMAgent
from llm_sim.models.llm_models import PolicyDecision
from llm_sim.models.state import SimulationState

class EconomicPolicyAgent(LLMAgent):
    """Agent that generates economic policy using LLM."""

    ECONOMIC_KEYWORDS = ["tax", "spend", "invest", "save", "trade"]

    def _construct_prompt(self, state: SimulationState) -> str:
        """Build economic context prompt."""
        agent_state = state.agents[self.name]

        return f"""You are an economic policy advisor.

Current State:
- Economic Strength: {agent_state.economic_strength}
- Interest Rate: {state.global_state.interest_rate}
- Turn: {state.turn}

Propose ONE economic policy action. Use keywords: {', '.join(self.ECONOMIC_KEYWORDS)}

Return JSON:
{{
  "action": "policy action string",
  "reasoning": "step-by-step explanation",
  "confidence": 0.0-1.0
}}"""

    def _validate_decision(self, decision: PolicyDecision) -> bool:
        """Check if action uses economic keywords."""
        action_lower = decision.action.lower()
        return any(keyword in action_lower for keyword in self.ECONOMIC_KEYWORDS)
```

### Best Practices

1. **Keep prompts focused**: Clearly state the domain and expected output
2. **Provide examples**: Show the LLM what good decisions look like
3. **Use structured output**: Request JSON for reliable parsing
4. **Validate loosely**: Use `_validate_decision()` for sanity checks, not strict enforcement
5. **Include confidence**: Help debug low-confidence decisions

## LLMEngine Pattern

The `LLMEngine` pattern enables engines to use LLM reasoning for state updates.

**Location**: `llm_sim.infrastructure.patterns.llm_engine`

### Interface

```python
from abc import abstractmethod
from llm_sim.infrastructure.base.engine import BaseEngine
from llm_sim.models.action import Action
from llm_sim.models.llm_models import StateUpdateDecision
from llm_sim.models.state import SimulationState
from llm_sim.utils.llm_client import LLMClient

class LLMEngine(BaseEngine):
    """Abstract base class for engines that use LLM reasoning."""

    def __init__(self, config, llm_client: LLMClient):
        super().__init__(config=config)
        self.llm_client = llm_client
        self.current_state = None

    @abstractmethod
    def _construct_state_update_prompt(self, action: Action, state) -> str:
        """Construct domain-specific state update prompt."""
        pass

    @abstractmethod
    def _apply_state_update(self, decision: StateUpdateDecision, state: SimulationState) -> SimulationState:
        """Apply LLM decision to create new state."""
        pass

    async def run_turn(self, validated_actions: List[Action]) -> SimulationState:
        """Process validated actions using LLM (implemented)."""
        # Handles: filtering, prompt construction, LLM calls, state updates
        pass
```

### Required Methods

- **`initialize_state() -> SimulationState`**: Create initial state (from BaseEngine)
- **`check_termination(state) -> bool`**: Check end condition (from BaseEngine)
- **`_construct_state_update_prompt(action, state) -> str`**: Build update prompt
- **`_apply_state_update(decision, state) -> SimulationState`**: Apply LLM-suggested changes

### What the Pattern Provides

The `run_turn()` method handles:
1. Filtering to validated actions only
2. Sequential processing of each action
3. Prompt construction via `_construct_state_update_prompt()`
4. LLM API call with retry
5. State update via `_apply_state_update()`
6. Reasoning chain collection
7. Turn counter increment

### Example Implementation

```python
from llm_sim.infrastructure.patterns.llm_engine import LLMEngine
from llm_sim.models.llm_models import StateUpdateDecision
from llm_sim.models.state import SimulationState, AgentState

class EconomicLLMEngine(LLMEngine):
    """Engine that uses LLM to compute economic effects."""

    def initialize_state(self) -> SimulationState:
        """Create initial economic state from config."""
        # Implementation similar to BaseEngine example
        pass

    def check_termination(self, state: SimulationState) -> bool:
        """Check if max turns reached."""
        return state.turn >= self.config.simulation.max_turns

    def _construct_state_update_prompt(self, action: Action, state) -> str:
        """Build prompt for computing economic effects."""
        agent_name = action.agent_name
        current_strength = state["agents"][agent_name]["economic_strength"]

        return f"""Calculate the economic effect of this action.

Agent: {agent_name}
Current Strength: {current_strength}
Action: {action.action_string}

Determine the new economic strength after this action.

Return JSON:
{{
  "new_strength": <number>,
  "reasoning": "explanation of calculation",
  "confidence": 0.0-1.0
}}"""

    def _apply_state_update(self, decision: StateUpdateDecision, state: SimulationState) -> SimulationState:
        """Update agent's economic strength."""
        # Parse decision.new_strength and update state
        # Return new SimulationState with updated values
        pass
```

### Best Practices

1. **One action at a time**: Process actions sequentially for consistency
2. **Include relevant context**: Give LLM current state snapshot
3. **Request specific values**: Ask for exact numbers, not relative changes
4. **Validate outputs**: Check that LLM responses are reasonable
5. **Log reasoning**: Track why LLM made each decision

## LLMValidator Pattern

The `LLMValidator` pattern enables validation using LLM reasoning.

**Location**: `llm_sim.infrastructure.patterns.llm_validator`

### Interface

```python
from abc import abstractmethod
from llm_sim.infrastructure.base.validator import BaseValidator
from llm_sim.models.action import Action, LLMAction
from llm_sim.models.llm_models import ValidationResult
from llm_sim.models.state import SimulationState
from llm_sim.utils.llm_client import LLMClient

class LLMValidator(BaseValidator):
    """Abstract base class for validators that use LLM reasoning."""

    def __init__(self, llm_client: LLMClient, domain: str, permissive: bool = True):
        super().__init__()
        self.llm_client = llm_client
        self.domain = domain
        self.permissive = permissive

    @abstractmethod
    def _construct_validation_prompt(self, action: LLMAction, state: SimulationState) -> str:
        """Construct domain-specific validation prompt."""
        pass

    @abstractmethod
    def _get_domain_description(self) -> str:
        """Get description of domain boundaries."""
        pass

    async def validate_actions(self, actions: List[LLMAction], state: SimulationState) -> List[LLMAction]:
        """Validate actions using LLM (implemented)."""
        # Handles: prompt construction, LLM calls, marking validated
        pass
```

### Required Methods

- **`_construct_validation_prompt(action, state) -> str`**: Build validation prompt
- **`_get_domain_description() -> str`**: Describe what's in/out of domain

### What the Pattern Provides

The `validate_actions()` method handles:
1. Iterating through all actions
2. Prompt construction via `_construct_validation_prompt()`
3. LLM API call with retry
4. Response parsing into `ValidationResult`
5. Updating action's `validated` field
6. Tracking validation statistics

### Example Implementation

```python
from llm_sim.infrastructure.patterns.llm_validator import LLMValidator
from llm_sim.models.action import LLMAction
from llm_sim.models.state import SimulationState

class EconomicValidator(LLMValidator):
    """Validates that actions are economic in nature."""

    def __init__(self, llm_client, permissive: bool = True):
        super().__init__(
            llm_client=llm_client,
            domain="economic",
            permissive=permissive
        )

    def _get_domain_description(self) -> str:
        """Define economic domain boundaries."""
        return """Economic domain includes:
- Fiscal policy (taxes, spending)
- Monetary policy (interest rates)
- Trade and investment
- Resource allocation

NOT included:
- Military actions
- Diplomatic negotiations
- Social policy"""

    def _construct_validation_prompt(self, action: LLMAction, state: SimulationState) -> str:
        """Build validation prompt with domain context."""
        return f"""Is this action within the economic domain?

Domain: {self._get_domain_description()}

Action: {action.action_string}
Agent Reasoning: {action.policy_decision.reasoning if action.policy_decision else 'N/A'}

Validation Mode: {"Permissive (allow boundary cases)" if self.permissive else "Strict"}

Return JSON:
{{
  "is_valid": true/false,
  "reasoning": "explanation of decision",
  "confidence": 0.0-1.0
}}"""
```

### Best Practices

1. **Use permissive mode**: Allow boundary cases by default
2. **Provide clear boundaries**: Define what IS and ISN'T in the domain
3. **Include agent reasoning**: Help LLM understand intent
4. **Log rejections**: Track what gets rejected for tuning
5. **Balance strictness**: Too strict breaks gameplay, too loose loses theme

## Async Usage

All LLM patterns are async. Use them in async contexts:

```python
import asyncio
from llm_sim.utils.llm_client import LLMClient

async def run_simulation():
    client = LLMClient(config)
    agent = EconomicPolicyAgent(name="Nation_A", llm_client=client)

    # Async call
    action = await agent.decide_action(state)

# Run with asyncio
asyncio.run(run_simulation())
```

## Performance Considerations

1. **Batch validation**: The patterns process actions sequentially
2. **Retry overhead**: Each LLM call has retry logic built-in
3. **Logging**: Reasoning chains are logged at DEBUG level
4. **Caching**: Consider caching responses for repeated prompts

## Error Handling

All patterns handle:
- Network failures (with retry)
- Malformed JSON responses (with retry)
- API rate limits (with exponential backoff)

Unrecoverable errors raise `LLMFailureException`.

## See Also

- [Base Classes Reference](base_classes.md) - Foundation interfaces
- [Creating Implementations](creating_implementations.md) - Step-by-step guide
- [LLM Client Documentation](../utils/llm_client.md) - Configuration and usage
