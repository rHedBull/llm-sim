# LLM Simulation Framework

A turn-based simulation framework with YAML configuration support for economic simulations and multi-agent interactions.

## Features

- **Turn-based simulation loop**: Coordinate multiple agents through sequential turns
- **YAML configuration**: Define simulations through simple configuration files
- **Economic engine**: Built-in economic simulation with interest-based growth
- **Extensible architecture**: Abstract base classes for engines, agents, and validators
- **Structured logging**: JSON or console output with detailed event tracking
- **Validation system**: Pluggable validation for agent actions
- **State management**: Immutable state transitions with full history tracking

## Installation

```bash
# Install dependencies using uv
uv sync --all-extras

# Or install for development
uv pip install -e ".[dev]"
```

## Quick Start

Run a simple economic simulation:

```bash
python main.py examples/quick_test.yaml
```

## Usage

### Command Line Interface

```bash
python main.py <config_file> [options]

Options:
  --debug             Enable debug logging
  --output FILE       Save results to JSON file
  --print-history     Print full state history
```

### Example Configuration

```yaml
simulation:
  name: "Economic Simulation"
  max_turns: 100
  termination:
    min_value: 0.0
    max_value: 1000000.0

engine:
  type: economic
  interest_rate: 0.05  # 5% growth per turn

agents:
  - name: Nation_A
    type: nation
    initial_economic_strength: 1000.0
  - name: Nation_B
    type: nation
    initial_economic_strength: 1500.0

validator:
  type: always_valid

logging:
  level: INFO
  format: json
```

### Example Output

```
=== Simulation Complete ===
Final Turn: 5
Total Economic Value: 161.05

Agent Final States:
  TestNation: 161.05

Validation Statistics:
  Total Validated: 5
  Total Rejected: 0
  Acceptance Rate: 100.00%
```

## Architecture

### Core Components

1. **Engine** (`BaseEngine`): Controls simulation state and rules
   - `EconomicEngine`: Implements interest-based economic growth

2. **Agent** (`BaseAgent`): Makes decisions each turn
   - `NationAgent`: Simple agent with fixed strategies (grow/maintain/decline)

3. **Validator** (`BaseValidator`): Validates agent actions
   - `AlwaysValidValidator`: MVP validator that accepts all actions

4. **Orchestrator**: Coordinates all components and manages simulation flow

### Data Models

- **SimulationState**: Immutable state representation
- **Action**: Agent decisions with validation tracking
- **SimulationConfig**: YAML-based configuration structure

## Development

### Running Tests

```bash
# Run all tests with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing

# Run unit tests only
python -m pytest tests/unit/ -v

# Run integration tests
python -m pytest tests/integration/ -v
```

### Code Quality

```bash
# Format code
python -m black src/ tests/ main.py

# Check linting
python -m ruff check src/ tests/ main.py

# Type checking
python -m mypy src/ --ignore-missing-imports
```

## Extending the Framework

### Custom Engine

```python
from src.llm_sim.engines.base import BaseEngine

class CustomEngine(BaseEngine):
    def initialize_state(self) -> SimulationState:
        # Initialize your custom state
        pass

    def apply_engine_rules(self, state: SimulationState) -> SimulationState:
        # Apply your custom rules
        pass
```

### Custom Agent

```python
from src.llm_sim.agents.base import BaseAgent

class CustomAgent(BaseAgent):
    def decide_action(self, state: SimulationState) -> Action:
        # Implement decision logic
        pass
```

### Custom Validator

```python
from src.llm_sim.validators.base import BaseValidator

class CustomValidator(BaseValidator):
    def validate_action(self, action: Action, state: SimulationState) -> bool:
        # Implement validation logic
        pass
```

## Configuration Options

### Simulation Settings

- `name`: Simulation name for logging
- `max_turns`: Maximum number of turns before termination
- `termination.min_value`: Stop if total value falls below threshold
- `termination.max_value`: Stop if total value exceeds threshold

### Engine Settings

- `type`: Engine type (currently only "economic")
- `interest_rate`: Growth rate per turn (-1.0 to 1.0)

### Agent Settings

- `name`: Unique agent identifier
- `type`: Agent type (currently only "nation")
- `initial_economic_strength`: Starting economic value

### Logging Settings

- `level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `format`: Output format ("json" or "console")

## Examples

Several example configurations are provided:

- `examples/quick_test.yaml`: 5-turn test simulation
- `examples/basic_economic.yaml`: 100-turn economic simulation
- `examples/extended_test.yaml`: Extended test with multiple nations

## License

This project is part of the LLM simulation framework.