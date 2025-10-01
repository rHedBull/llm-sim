# Creating Custom Implementations

This guide walks you through creating custom agents, engines, and validators for the simulation framework.

## Directory Structure

The framework uses a discovery-based architecture:

```
src/llm_sim/
├── infrastructure/          # Framework code (don't modify)
│   ├── base/               # Abstract base classes
│   │   ├── agent.py        # BaseAgent
│   │   ├── engine.py       # BaseEngine
│   │   └── validator.py    # BaseValidator
│   └── patterns/           # LLM integration patterns
│       ├── llm_agent.py    # LLMAgent
│       ├── llm_engine.py   # LLMEngine
│       └── llm_validator.py # LLMValidator
│
└── implementations/        # Your custom implementations
    ├── agents/            # Custom agent implementations
    │   ├── nation.py      # → NationAgent class
    │   └── econ_llm_agent.py → EconLLMAgent class
    ├── engines/           # Custom engine implementations
    │   ├── economic.py    # → EconomicEngine class
    │   └── econ_llm_engine.py → EconLLMEngine class
    └── validators/        # Custom validator implementations
        ├── always_valid.py # → AlwaysValidValidator class
        └── econ_llm_validator.py → EconLLMValidator class
```

## Naming Conventions

The framework automatically discovers implementations using filename-to-classname mapping:

| Filename | Expected Class Name |
|----------|---------------------|
| `nation.py` | `NationAgent` |
| `economic.py` | `EconomicEngine` |
| `always_valid.py` | `AlwaysValidValidator` |
| `econ_llm_agent.py` | `EconLLMAgent` |

**Rules**:
- Filenames use `snake_case`
- Class names use `PascalCase`
- Conversion: `economic_nation.py` → `EconomicNationAgent`

## Discovery Mechanism

The `ComponentDiscovery` class automatically loads implementations:

```python
from llm_sim.discovery import ComponentDiscovery
from pathlib import Path

# Initialize discovery
discovery = ComponentDiscovery(Path(__file__).parent)

# List available implementations
agents = discovery.list_agents()       # ['nation', 'econ_llm_agent']
engines = discovery.list_engines()     # ['economic', 'econ_llm_engine']
validators = discovery.list_validators() # ['always_valid', 'econ_llm_validator']

# Load by filename (without .py)
NationAgent = discovery.load_agent('nation')
EconomicEngine = discovery.load_engine('economic')

# Discovery validates inheritance automatically
agent = NationAgent(name="Nation_A")  # ✓ Inherits from BaseAgent
```

### Discovery Rules

1. **Files must be in the correct directory**:
   - Agents: `implementations/agents/`
   - Engines: `implementations/engines/`
   - Validators: `implementations/validators/`

2. **Class must match filename** (after case conversion)

3. **Class must inherit from correct base**:
   - Agents: `BaseAgent` or `LLMAgent`
   - Engines: `BaseEngine` or `LLMEngine`
   - Validators: `BaseValidator` or `LLMValidator`

4. **Validation errors** are descriptive:
   ```
   FileNotFoundError: Agent 'my_agent' not found at implementations/agents/my_agent.py
   AttributeError: Module does not contain class 'MyAgent'
   TypeError: MyAgent does not inherit from BaseAgent
   ```

## Quick Start: Create a Simple Agent

### Step 1: Choose Your Base

- Use **`BaseAgent`** for rule-based agents
- Use **`LLMAgent`** for AI-driven agents

### Step 2: Create the File

Create `src/llm_sim/implementations/agents/my_trader.py`:

```python
"""My custom trading agent."""

from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState


class MyTrader(BaseAgent):
    """Agent that trades based on economic strength."""

    def __init__(self, name: str, risk_tolerance: float = 0.5):
        """Initialize trader with risk preference.

        Args:
            name: Agent name
            risk_tolerance: 0.0 (conservative) to 1.0 (aggressive)
        """
        super().__init__(name=name)
        self.risk_tolerance = risk_tolerance

    def decide_action(self, state: SimulationState) -> Action:
        """Decide whether to invest or save based on current strength.

        Args:
            state: Current simulation state

        Returns:
            Action representing trading decision
        """
        agent_state = state.agents[self.name]
        strength = agent_state.economic_strength

        # Risk-based decision
        if strength > 1000 * self.risk_tolerance:
            action_name = "invest"
        else:
            action_name = "save"

        return Action(
            agent_name=self.name,
            action_name=action_name,
            parameters={"amount": strength * 0.1}
        )
```

### Step 3: Use in YAML Config

The filename (without `.py`) is the `type` in config:

```yaml
simulation:
  name: "Trading Simulation"
  max_turns: 10

agents:
  - name: "Trader_A"
    type: "my_trader"  # ← Uses my_trader.py → MyTrader
    risk_tolerance: 0.7

  - name: "Trader_B"
    type: "my_trader"
    risk_tolerance: 0.3

engine:
  type: "economic"

validator:
  type: "always_valid"
```

### Step 4: Test It

```python
from llm_sim.orchestrator import SimulationOrchestrator

orchestrator = SimulationOrchestrator.from_yaml("config.yaml")
result = orchestrator.run()

print(f"Final state: {result['final_state']}")
```

## Quick Start: Create an LLM Agent

### Step 1: Create the File

Create `src/llm_sim/implementations/agents/diplomatic_agent.py`:

```python
"""LLM-powered diplomatic agent."""

from llm_sim.infrastructure.patterns.llm_agent import LLMAgent
from llm_sim.models.llm_models import PolicyDecision
from llm_sim.models.state import SimulationState


class DiplomaticAgent(LLMAgent):
    """Agent that uses LLM for diplomatic decisions."""

    DIPLOMATIC_KEYWORDS = ["negotiate", "ally", "treaty", "embargo", "sanction"]

    def _construct_prompt(self, state: SimulationState) -> str:
        """Build diplomatic context prompt for LLM."""
        agent_state = state.agents[self.name]

        # Get other nations' strengths for context
        other_nations = {
            name: agent.economic_strength
            for name, agent in state.agents.items()
            if name != self.name
        }

        return f"""You are the diplomatic advisor for {self.name}.

Your Nation:
- Economic Strength: {agent_state.economic_strength}

Other Nations:
{chr(10).join(f'- {name}: {strength}' for name, strength in other_nations.items())}

Global Context:
- Turn: {state.turn}
- Interest Rate: {state.global_state.interest_rate}

Propose ONE diplomatic action. Use keywords: {', '.join(self.DIPLOMATIC_KEYWORDS)}

Return JSON:
{{
  "action": "specific diplomatic action",
  "reasoning": "step-by-step strategic reasoning",
  "confidence": 0.0-1.0
}}"""

    def _validate_decision(self, decision: PolicyDecision) -> bool:
        """Check if action uses diplomatic keywords."""
        action_lower = decision.action.lower()
        return any(keyword in action_lower for keyword in self.DIPLOMATIC_KEYWORDS)
```

### Step 2: Use in YAML Config

```yaml
agents:
  - name: "Diplomat_A"
    type: "diplomatic_agent"  # ← Uses diplomatic_agent.py → DiplomaticAgent
    llm_model: "gpt-4o-mini"  # LLM config handled by orchestrator

engine:
  type: "economic"

validator:
  type: "always_valid"

llm:
  model: "gpt-4o-mini"
  temperature: 0.7
  max_retries: 3
```

## Creating Custom Engines

### Example: Simple Turn-Based Engine

Create `src/llm_sim/implementations/engines/turn_based.py`:

```python
"""Simple turn-based game engine."""

from typing import List
from llm_sim.infrastructure.base.engine import BaseEngine
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState, AgentState, GlobalState


class TurnBasedEngine(BaseEngine):
    """Engine with fixed turn progression."""

    def initialize_state(self) -> SimulationState:
        """Create initial state from config."""
        agents = {
            agent_config.name: AgentState(
                name=agent_config.name,
                economic_strength=agent_config.initial_economic_strength
            )
            for agent_config in self.config.agents
        }

        total_value = sum(a.economic_strength for a in agents.values())

        return SimulationState(
            turn=0,
            agents=agents,
            global_state=GlobalState(
                interest_rate=self.config.engine.interest_rate,
                total_economic_value=total_value
            )
        )

    def apply_actions(self, actions: List[Action]) -> SimulationState:
        """Apply actions to state."""
        new_agents = dict(self._state.agents)

        for action in actions:
            if not action.validated:
                continue

            agent_state = new_agents[action.agent_name]

            # Simple action processing
            if action.action_name == "grow":
                new_agents[action.agent_name] = agent_state.model_copy(
                    update={"economic_strength": agent_state.economic_strength * 1.1}
                )
            elif action.action_name == "decline":
                new_agents[action.agent_name] = agent_state.model_copy(
                    update={"economic_strength": agent_state.economic_strength * 0.9}
                )

        return self._state.model_copy(update={"agents": new_agents})

    def apply_engine_rules(self, state: SimulationState) -> SimulationState:
        """Apply global rules."""
        # Apply interest to all agents
        interest_rate = state.global_state.interest_rate
        new_agents = {}

        for name, agent in state.agents.items():
            new_strength = agent.economic_strength * (1 + interest_rate)
            new_agents[name] = agent.model_copy(
                update={"economic_strength": new_strength}
            )

        return state.model_copy(update={"agents": new_agents})

    def check_termination(self, state: SimulationState) -> bool:
        """Check if simulation should end."""
        # End after max turns or if any agent reaches threshold
        if state.turn >= self.config.simulation.max_turns:
            return True

        termination = self.config.simulation.termination
        for agent in state.agents.values():
            if agent.economic_strength > termination.max_value:
                return True
            if agent.economic_strength < termination.min_value:
                return True

        return False
```

## Creating Custom Validators

### Example: Keyword Validator

Create `src/llm_sim/implementations/validators/keyword_validator.py`:

```python
"""Validator that checks for required keywords."""

from typing import List
from llm_sim.infrastructure.base.validator import BaseValidator
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState


class KeywordValidator(BaseValidator):
    """Validates actions contain specific keywords."""

    def __init__(self, allowed_keywords: List[str]):
        """Initialize with list of allowed keywords.

        Args:
            allowed_keywords: List of keywords actions must contain
        """
        super().__init__()
        self.allowed_keywords = [k.lower() for k in allowed_keywords]

    def validate_action(self, action: Action, state: SimulationState) -> bool:
        """Check if action contains any allowed keyword.

        Args:
            action: Action to validate
            state: Current simulation state

        Returns:
            True if action contains at least one allowed keyword
        """
        action_lower = action.action_name.lower()
        return any(keyword in action_lower for keyword in self.allowed_keywords)
```

Use in Python (requires programmatic setup):

```python
from llm_sim.implementations.validators.keyword_validator import KeywordValidator

validator = KeywordValidator(allowed_keywords=["trade", "invest", "save"])
```

## Common Pitfalls

### 1. Filename Doesn't Match Class Name

❌ **Wrong**:
```python
# File: implementations/agents/trader.py
class MyTraderAgent(BaseAgent):  # ← Class name doesn't match!
    pass
```

✓ **Correct**:
```python
# File: implementations/agents/trader.py
class TraderAgent(BaseAgent):  # ← Matches filename
    pass
```

### 2. Forgot to Call `super().__init__()`

❌ **Wrong**:
```python
class MyAgent(BaseAgent):
    def __init__(self, name: str):
        self.name = name  # ← Doesn't call super().__init__()
```

✓ **Correct**:
```python
class MyAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name=name)  # ← Calls parent constructor
```

### 3. Wrong Base Class

❌ **Wrong**:
```python
# File: implementations/agents/my_agent.py
from llm_sim.infrastructure.base.engine import BaseEngine

class MyAgent(BaseEngine):  # ← Agent inheriting from BaseEngine!
    pass
```

✓ **Correct**:
```python
# File: implementations/agents/my_agent.py
from llm_sim.infrastructure.base.agent import BaseAgent

class MyAgent(BaseAgent):  # ← Correct base class
    pass
```

### 4. Not Implementing Abstract Methods

❌ **Wrong**:
```python
class MyAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name=name)
    # ← Missing decide_action() implementation!
```

✓ **Correct**:
```python
class MyAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name=name)

    def decide_action(self, state: SimulationState) -> Action:
        # Implementation here
        pass
```

### 5. Modifying State In-Place

❌ **Wrong**:
```python
def apply_actions(self, actions: List[Action]) -> SimulationState:
    self._state.agents["A"].economic_strength += 100  # ← Mutates state!
    return self._state
```

✓ **Correct**:
```python
def apply_actions(self, actions: List[Action]) -> SimulationState:
    new_agents = dict(self._state.agents)
    new_agents["A"] = new_agents["A"].model_copy(
        update={"economic_strength": new_agents["A"].economic_strength + 100}
    )
    return self._state.model_copy(update={"agents": new_agents})  # ← New state
```

## Testing Your Implementation

### Unit Test Template

```python
"""Tests for MyTrader agent."""

import pytest
from llm_sim.implementations.agents.my_trader import MyTrader
from llm_sim.models.state import SimulationState, AgentState, GlobalState


def test_trader_initialization():
    """Test creating a trader."""
    trader = MyTrader(name="Trader_A", risk_tolerance=0.5)
    assert trader.name == "Trader_A"
    assert trader.risk_tolerance == 0.5


def test_trader_invests_when_strong():
    """Test trader invests when economically strong."""
    trader = MyTrader(name="Trader_A", risk_tolerance=0.5)

    state = SimulationState(
        turn=1,
        agents={
            "Trader_A": AgentState(name="Trader_A", economic_strength=2000.0)
        },
        global_state=GlobalState(interest_rate=0.05, total_economic_value=2000.0)
    )

    action = trader.decide_action(state)
    assert action.action_name == "invest"
    assert action.agent_name == "Trader_A"


def test_trader_saves_when_weak():
    """Test trader saves when economically weak."""
    trader = MyTrader(name="Trader_A", risk_tolerance=0.5)

    state = SimulationState(
        turn=1,
        agents={
            "Trader_A": AgentState(name="Trader_A", economic_strength=100.0)
        },
        global_state=GlobalState(interest_rate=0.05, total_economic_value=100.0)
    )

    action = trader.decide_action(state)
    assert action.action_name == "save"
```

## Advanced: Custom LLM Patterns

If you need to customize LLM behavior beyond what `LLMAgent/Engine/Validator` provide, you can:

1. **Extend the pattern classes** with additional methods
2. **Override `decide_action()`** / `run_turn()` / `validate_actions()`
3. **Add caching** for LLM responses
4. **Implement multi-step reasoning** with chained prompts

Example:
```python
class MultiStepLLMAgent(LLMAgent):
    """Agent with multi-step reasoning."""

    async def decide_action(self, state: SimulationState) -> Action:
        # Step 1: Analyze situation
        analysis_prompt = self._construct_analysis_prompt(state)
        analysis = await self.llm_client.call_with_retry(
            prompt=analysis_prompt,
            response_model=SituationAnalysis
        )

        # Step 2: Generate decision based on analysis
        decision_prompt = self._construct_decision_prompt(state, analysis)
        decision = await self.llm_client.call_with_retry(
            prompt=decision_prompt,
            response_model=PolicyDecision
        )

        return self._create_action(decision)
```

## Next Steps

- Read [Base Classes Reference](base_classes.md) for interface details
- Read [LLM Pattern Documentation](llm_pattern.md) for LLM integration
- See `implementations/` directory for more examples
- Check [Migration Guide](../MIGRATION.md) if updating existing code
