# Quickstart: Using the Reorganized Simulation Infrastructure

**Feature**: 005-we-want-to | **Date**: 2025-09-30

## Overview

This quickstart demonstrates how to use the reorganized simulation infrastructure to create a new domain implementation.

## Prerequisites

- Python 3.12+
- llm_sim package with reorganized structure
- Basic understanding of abstract classes and inheritance

## Scenario: Creating a Military Simulation Domain

We'll create a simple military simulation with:
- Military agent that makes strategic decisions
- Military engine that processes combat actions
- Military validator that checks action legality

### Step 1: Understand the Available Abstract Classes

**Check infrastructure documentation**:
```bash
ls docs/patterns/
# base_classes.md - Minimal interfaces (BaseAgent, BaseEngine, BaseValidator)
# llm_pattern.md - LLM-enabled patterns (LLMAgent, LLMEngine, LLMValidator)
```

**Decision**: For our military simulation, we'll:
- Use `BaseAgent` for a scripted strategy agent (like NationAgent)
- Use `BaseEngine` for deterministic combat resolution
- Use `BaseValidator` for rule-based validation

### Step 2: Create Military Agent Implementation

**Create file**: `src/llm_sim/implementations/agents/military_agent.py`

```python
"""Military agent implementation."""

from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState

class MilitaryAgent(BaseAgent):
    """Agent that makes military strategic decisions."""

    def __init__(self, name: str, strategy: str = "defensive") -> None:
        """Initialize military agent.

        Args:
            name: Agent name
            strategy: Military strategy (defensive/aggressive/balanced)
        """
        super().__init__(name)
        self.strategy = strategy

    def decide_action(self, state: SimulationState) -> Action:
        """Decide military action based on strategy.

        Args:
            state: Current simulation state

        Returns:
            Action representing military decision
        """
        # Simple strategy-based logic
        if self.strategy == "aggressive":
            action_name = "attack"
        elif self.strategy == "defensive":
            action_name = "fortify"
        else:
            action_name = "patrol"

        return Action(
            agent_name=self.name,
            action_name=action_name,
            parameters={"strength": state.agents[self.name].military_strength}
        )
```

**Key points**:
- ✅ Filename: `military_agent.py` (snake_case)
- ✅ Class name: `MilitaryAgent` (PascalCase of filename)
- ✅ Extends `BaseAgent`
- ✅ Implements `decide_action` abstract method

### Step 3: Create Military Engine Implementation

**Create file**: `src/llm_sim/implementations/engines/military_engine.py`

```python
"""Military simulation engine."""

from typing import List

from llm_sim.infrastructure.base.engine import BaseEngine
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState, AgentState, GlobalState
from llm_sim.models.config import SimulationConfig

class MilitaryEngine(BaseEngine):
    """Engine that processes military actions."""

    def initialize_state(self) -> SimulationState:
        """Create initial military simulation state."""
        agents = {}
        for agent_config in self.config.agents:
            agents[agent_config.name] = AgentState(
                name=agent_config.name,
                military_strength=agent_config.initial_military_strength
            )

        return SimulationState(
            turn=0,
            agents=agents,
            global_state=GlobalState(total_military_power=sum(
                a.military_strength for a in agents.values()
            ))
        )

    def apply_actions(self, actions: List[Action]) -> SimulationState:
        """Apply military actions to state."""
        new_state = self._state.model_copy(deep=True)

        for action in actions:
            if action.action_name == "attack":
                # Reduce target strength
                pass  # Implement combat logic
            elif action.action_name == "fortify":
                # Increase own strength
                pass

        return new_state

    def apply_engine_rules(self, state: SimulationState) -> SimulationState:
        """Apply military simulation rules."""
        # Attrition, logistics, etc.
        return state

    def check_termination(self, state: SimulationState) -> bool:
        """Check if simulation should end."""
        return state.turn >= self.config.simulation.max_turns
```

### Step 4: Create Military Validator Implementation

**Create file**: `src/llm_sim/implementations/validators/military_validator.py`

```python
"""Military action validator."""

from llm_sim.infrastructure.base.validator import BaseValidator
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState

class MilitaryValidator(BaseValidator):
    """Validates military actions."""

    def validate_action(self, action: Action, state: SimulationState) -> bool:
        """Check if military action is legal."""
        # Check agent exists
        if action.agent_name not in state.agents:
            return False

        # Check action is valid military action
        valid_actions = ["attack", "defend", "fortify", "patrol"]
        if action.action_name not in valid_actions:
            return False

        # Check agent has sufficient strength
        agent_state = state.agents[action.agent_name]
        if agent_state.military_strength <= 0:
            return False

        return True
```

### Step 5: Create YAML Configuration

**Create file**: `configs/military_sim.yaml`

```yaml
simulation:
  name: "Military Simulation"
  max_turns: 50

agents:
  - name: "RedForce"
    type: "military_agent"        # References military_agent.py
    initial_military_strength: 100
    strategy: "aggressive"

  - name: "BlueForce"
    type: "military_agent"
    initial_military_strength: 100
    strategy: "defensive"

engine:
  type: "military_engine"         # References military_engine.py

validator:
  type: "military_validator"      # References military_validator.py
```

**Key points**:
- `type` fields reference filenames (without .py)
- No changes to YAML schema
- Discovery mechanism handles loading

### Step 6: Run the Simulation

```bash
# From project root
python main.py configs/military_sim.yaml
```

**Expected output**:
```
Loading configuration from: configs/military_sim.yaml
Simulation name: Military Simulation
Max turns: 50
Number of agents: 2

=== Simulation Complete ===
Final Turn: 50
...
```

## Verification Steps

### 1. Test Discovery Mechanism

```python
from pathlib import Path
from llm_sim.orchestrator import ComponentDiscovery

discovery = ComponentDiscovery(Path("src/llm_sim"))

# List available implementations
print("Available agents:", discovery.list_agents())
# Should include: ['econ_llm_agent', 'nation', 'military_agent']

# Load your new agent
MilitaryAgentClass = discovery.load_agent("military_agent")
print(f"Loaded: {MilitaryAgentClass.__name__}")  # Should print: MilitaryAgent
```

### 2. Test Agent Instantiation

```python
agent = MilitaryAgentClass(name="TestAgent", strategy="defensive")
print(f"Agent created: {agent.name} with strategy {agent.strategy}")
```

### 3. Run Integration Test

```bash
pytest tests/integration/test_military_simulation.py -v
```

## Common Patterns

### Using LLM Pattern for Intelligent Agents

Instead of `BaseAgent`, extend `LLMAgent` for LLM-powered decision making:

```python
from llm_sim.infrastructure.patterns.llm_agent import LLMAgent

class IntelligentMilitaryAgent(LLMAgent):
    """LLM-powered military strategist."""

    def _construct_prompt(self, state: SimulationState) -> str:
        """Build prompt for LLM."""
        return f"""You are a military commander. Current situation:
        Your forces: {state.agents[self.name].military_strength}
        Enemy forces: {state.agents['enemy'].military_strength}

        Choose action: attack, defend, fortify, or patrol
        Provide reasoning and confidence."""

    def _validate_decision(self, decision: PolicyDecision) -> bool:
        """Validate LLM decision."""
        valid_actions = ["attack", "defend", "fortify", "patrol"]
        return decision.action in valid_actions
```

### Mixing Agent Types

You can use different agent types in the same simulation:

```yaml
agents:
  - name: "ScriptedAgent"
    type: "military_agent"        # Simple rule-based
    strategy: "defensive"

  - name: "IntelligentAgent"
    type: "intelligent_military_agent"  # LLM-powered
```

## Troubleshooting

### Error: "No implementation found for 'agents' with filename 'military_agent'"

**Cause**: File doesn't exist or is in wrong directory

**Solution**:
```bash
# Check file exists
ls src/llm_sim/implementations/agents/military_agent.py

# Check you're in correct directory when running
pwd  # Should be project root
```

### Error: "Class 'MilitaryAgent' does not inherit from BaseAgent"

**Cause**: Incorrect inheritance

**Solution**: Verify your class definition:
```python
from llm_sim.infrastructure.base.agent import BaseAgent

class MilitaryAgent(BaseAgent):  # Must extend BaseAgent
    ...
```

### Error: "Module 'military_agent' does not contain expected class 'MilitaryAgent'"

**Cause**: Class name doesn't match filename convention

**Solution**: Ensure class name is PascalCase of filename:
- `military_agent.py` → `MilitaryAgent`
- `my_custom_agent.py` → `MyCustomAgent`

## Next Steps

1. **Add tests**: Create contract tests for your implementations
2. **Document patterns**: Add to `docs/patterns/` if you created reusable patterns
3. **Share examples**: Add your simulation to examples directory
4. **Extend functionality**: Add more sophisticated logic to your agents/engines

## Reference Documentation

- **Abstract Classes**: See `docs/patterns/base_classes.md`
- **LLM Patterns**: See `docs/patterns/llm_pattern.md`
- **Discovery API**: See `specs/005-we-want-to/contracts/discovery_api_contract.md`
- **Full API**: Run `python -m pydoc llm_sim`

## Validation Checklist

After completing this quickstart, verify:

- [ ] New agent implementation in `implementations/agents/`
- [ ] New engine implementation in `implementations/engines/`
- [ ] New validator implementation in `implementations/validators/`
- [ ] YAML config references correct filenames
- [ ] Simulation runs without errors
- [ ] All tests pass: `pytest tests/`
- [ ] Code follows naming conventions (snake_case file → PascalCase class)
- [ ] Implementations extend appropriate abstract classes

## Success Criteria

✅ You can create a new simulation domain without modifying infrastructure code
✅ Discovery mechanism automatically finds your implementations
✅ YAML configs work with filename references
✅ Tests pass and simulation runs successfully
