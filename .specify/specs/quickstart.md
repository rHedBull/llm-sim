# Quickstart Guide: Simulation Loop

## Installation

```bash
# Clone repository
git clone <repo-url>
cd llm_sim

# Install dependencies with uv
uv sync

# Run tests to verify installation
uv run pytest
```

## Basic Usage

### 1. Create Configuration File

Create `config.yaml`:

```yaml
simulation:
  name: "Economic Growth Demo"
  max_turns: 10
  termination:
    min_value: 0
    max_value: 1000000

engine:
  type: "EconomicEngine"
  interest_rate: 0.05  # 5% growth per turn

agents:
  - name: "Nation_A"
    type: "NationAgent"
    initial_economic_strength: 1000
  - name: "Nation_B"
    type: "NationAgent"
    initial_economic_strength: 1500

validator:
  type: "AlwaysValidValidator"

logging:
  level: "INFO"
  format: "json"
```

### 2. Run Simulation

```python
from llm_sim.simulation import run_simulation

# Run simulation with config file
results = run_simulation("config.yaml")

# Results include final state and history
print(f"Final turn: {results.final_state.turn}")
print(f"Nation A: {results.final_state.agents['Nation_A'].economic_strength}")
print(f"Nation B: {results.final_state.agents['Nation_B'].economic_strength}")
```

### 3. Command Line Usage

```bash
# Run simulation
uv run python -m llm_sim.main config.yaml

# With debug logging
uv run python -m llm_sim.main config.yaml --debug

# Output to file
uv run python -m llm_sim.main config.yaml --output results.json
```

## Example Output

```json
{
  "turn": 10,
  "agents": {
    "Nation_A": {
      "economic_strength": 1628.89
    },
    "Nation_B": {
      "economic_strength": 2443.34
    }
  },
  "global_state": {
    "interest_rate": 0.05,
    "total_economic_value": 4072.23
  }
}
```

## Component Overview

### Engine
Controls simulation flow and state management:
```python
from llm_sim.core.engine import EconomicEngine

engine = EconomicEngine(config)
initial_state = engine.initialize_state()
```

### Agents
Make decisions each turn:
```python
from llm_sim.core.agent import NationAgent

agent = NationAgent("Nation_A")
action = agent.decide_action(current_state)
```

### Validator
Ensures actions are legal:
```python
from llm_sim.core.validator import AlwaysValidValidator

validator = AlwaysValidValidator()
valid_actions = validator.validate_actions(actions, state)
```

## Configuration Options

### Simulation Settings
- `max_turns`: Maximum number of simulation turns
- `termination.min_value`: Stop if any value goes below
- `termination.max_value`: Stop if any value goes above

### Engine Settings
- `type`: Engine implementation class
- `interest_rate`: Growth rate per turn (for EconomicEngine)

### Agent Settings
- `name`: Unique agent identifier
- `type`: Agent implementation class
- `initial_economic_strength`: Starting value

### Logging Settings
- `level`: DEBUG, INFO, WARNING, ERROR
- `format`: json or text

## Development Workflow

### Running Tests
```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=llm_sim

# Specific test file
uv run pytest tests/test_engine.py
```

### Code Quality
```bash
# Format code
uv run black src/

# Lint
uv run ruff check src/

# Type checking
uv run mypy src/
```

### Adding Custom Components

#### Custom Engine
```python
from llm_sim.core.engine import BaseEngine

class CustomEngine(BaseEngine):
    def apply_engine_rules(self, state):
        # Custom logic here
        return new_state
```

#### Custom Agent
```python
from llm_sim.core.agent import BaseAgent

class CustomAgent(BaseAgent):
    def decide_action(self, state):
        # Decision logic here
        return Action(...)
```

## Troubleshooting

### Common Issues

1. **Module not found**
   ```bash
   uv sync  # Reinstall dependencies
   ```

2. **Config validation error**
   - Check YAML syntax
   - Verify required fields
   - Check value ranges

3. **Simulation doesn't terminate**
   - Check termination conditions
   - Verify max_turns is set
   - Check value thresholds

## Next Steps

1. Modify configuration for different scenarios
2. Implement custom agents with strategies
3. Add visualization of results
4. Extend state with additional properties
5. Implement complex validation rules

## API Reference

See individual component documentation:
- [Engine Contract](contracts/engine.md)
- [Agent Contract](contracts/agent.md)
- [Validator Contract](contracts/validator.md)
- [Data Models](data-model.md)