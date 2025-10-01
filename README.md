# LLM-Sim Framework

**A pure infrastructure library for building turn-based multi-agent simulations with LLM-based reasoning.**

> **Note:** This is the framework library only. For concrete implementations and runnable examples, see [llm-sim-economic](../llm-sim-economic).

---

## Overview

`llm-sim` provides the core infrastructure for building multi-agent simulations:

- **Base classes** for agents, engines, and validators
- **LLM integration patterns** for reasoning agents
- **State management** with dynamic variables
- **Checkpoint system** with schema validation
- **Orchestration** for running simulations
- **Component discovery** mechanism

This library is designed to be extended - you implement domain-specific agents/engines in separate repositories.

---

## Installation

```bash
# Install as dependency in your simulation project
pip install -e git+https://github.com/your-org/llm-sim.git#egg=llm-sim

# Or for local development
pip install -e .
```

---

## Quick Start

### 1. Create Your Simulation Repository

```bash
mkdir my-simulation
cd my-simulation
```

### 2. Define Dependencies

```toml
# pyproject.toml
[project]
name = "my-simulation"
dependencies = ["llm-sim>=0.1.0"]
```

### 3. Implement Your Domain

```python
# src/my_simulation/agents/my_agent.py
from llm_sim.infrastructure.base import BaseAgent
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState

class MyAgent(BaseAgent):
    def decide_action(self, state: SimulationState) -> Action:
        # Your decision logic here
        return Action(agent_name=self.name, action_name="my_action")
```

### 4. Configure & Run

```yaml
# config.yaml
agents:
  - name: Agent_1
    type: my_agent

engine:
  type: my_engine

# ... rest of config
```

```python
# main.py
from llm_sim.orchestrator import SimulationOrchestrator

orchestrator = SimulationOrchestrator.from_yaml("config.yaml")
result = orchestrator.run()
```

See [llm-sim-economic](../llm-sim-economic) for a complete reference implementation.

---

## Architecture

### Three-Tier Inheritance

```
BaseAgent              BaseEngine              BaseValidator
    ↓                      ↓                        ↓
LLMAgent               LLMEngine               LLMValidator
(abstract)             (abstract)              (abstract)
    ↓                      ↓                        ↓
MyCustomAgent          MyCustomEngine          MyCustomValidator
(your implementation)  (your implementation)   (your implementation)
```

### Core Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **Base Classes** | Abstract interfaces | `infrastructure/base/` |
| **LLM Patterns** | LLM-based reasoning | `infrastructure/patterns/` |
| **Models** | State, config, actions | `models/` |
| **Persistence** | Checkpointing | `persistence/` |
| **Orchestrator** | Simulation runner | `orchestrator.py` |
| **Discovery** | Component loading | `discovery.py` |

---

## Features

### Dynamic State Variables

Configure custom state variables via YAML:

```yaml
state_variables:
  agent_vars:
    economic_strength:
      type: float
      min: 0
      default: 0.0
    tech_level:
      type: int
      min: 1
      max: 10
      default: 1

  global_vars:
    interest_rate:
      type: float
      default: 0.05
```

The framework dynamically generates Pydantic models from these definitions.

### Checkpointing

Automatic state persistence with schema validation:

```yaml
simulation:
  checkpoint_interval: 10  # Save every 10 turns
```

Output structure:
```
output/{RunID}/
├── checkpoints/
│   ├── turn_10.json
│   ├── turn_20.json
│   ├── last.json   # Latest state
│   └── final.json  # Final state
└── result.json     # Complete results
```

### LLM Integration

Built-in support for LLM-based agents:

```python
from llm_sim.infrastructure.patterns import LLMAgent

class MyLLMAgent(LLMAgent):
    async def decide_action_async(self, state: SimulationState) -> Action:
        prompt = self._build_prompt(state)
        response = await self.llm_client.generate_async(prompt)
        return self._parse_action(response)
```

Includes:
- Async LLM calls
- Reasoning chain capture
- Timeout handling
- Retry logic

---

## Documentation

- **[Platform Architecture](docs/PLATFORM_ARCHITECTURE.md)** - Control plane design (dashboard, MCP server)
- **[Architecture Overview](docs/ARCHITECTURE.md)** - Framework internals
- **[Configuration Guide](docs/CONFIGURATION.md)** - YAML configuration reference
- **[LLM Setup](docs/LLM_SETUP.md)** - Using LLMs with the framework
- **[Real-Time Simulation](docs/REALTIME_SIMULATION.md)** - Event-driven simulation design
- **[Compute Budget Simulation](docs/COMPUTE_BUDGET_SIMULATION.md)** - Turn-based with resource constraints
- **[API Reference](docs/API.md)** - Extending the framework

---

## Example Implementations

- **[llm-sim-economic](../llm-sim-economic)** - Economic simulations (reference implementation)

Create your own domain repo following this structure:

```
your-simulation/
├── src/your_sim/
│   ├── agents/      # Your agents
│   ├── engines/     # Your engines
│   └── validators/  # Your validators
├── scenarios/       # YAML configs
├── main.py          # CLI entry point
└── pyproject.toml   # Depends on llm-sim
```

---

## Development

### Running Tests

```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# Contract tests
pytest tests/contract

# Full test suite with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### Type Checking

```bash
mypy src/
```

### Code Formatting

```bash
black src/ tests/
ruff check src/ tests/
```

---

## Framework Components

### Base Classes (`infrastructure/base/`)

```python
class BaseAgent(ABC):
    @abstractmethod
    def decide_action(self, state: SimulationState) -> Action:
        """Decide action based on current state."""
        pass

class BaseEngine(ABC):
    @abstractmethod
    def initialize_state(self) -> SimulationState:
        """Create initial state."""
        pass

    @abstractmethod
    def run_turn(self, actions: List[Action]) -> SimulationState:
        """Execute one turn."""
        pass

class BaseValidator(ABC):
    @abstractmethod
    def validate_actions(
        self,
        actions: List[Action],
        state: SimulationState
    ) -> List[Action]:
        """Validate and filter actions."""
        pass
```

### Component Discovery

The framework automatically discovers your implementations:

```python
from llm_sim.discovery import ComponentDiscovery

discovery = ComponentDiscovery(base_path)
AgentClass = discovery.load_agent("my_agent")
EngineClass = discovery.load_engine("my_engine")
ValidatorClass = discovery.load_validator("my_validator")
```

Naming convention:
- `my_agent` → looks for `MyAgent` class (CamelCase)
- File: `agents/my_agent.py` or `agents.py` with `MyAgent` class

---

## Requirements

- **Python**: 3.12+
- **Core deps**: pydantic ≥2.0, PyYAML ≥6.0, structlog ≥24.0
- **LLM deps** (optional): ollama ≥0.1.0, httpx ≥0.25.0, tenacity ≥8.0

---

## Contributing

This is a framework library - concrete implementations belong in separate repos.

For framework improvements:
1. Maintain backward compatibility
2. Update tests
3. Document API changes
4. Follow existing patterns

---

## Roadmap

See [PLATFORM_ARCHITECTURE.md](docs/PLATFORM_ARCHITECTURE.md) for planned features:

- **Control server** - Multi-simulation orchestration
- **Dashboard** - Real-time monitoring UI
- **MCP integration** - LLM control interface
- **Real-time mode** - Event-driven simulations (optional)
- **Compute budgets** - Resource-constrained reasoning (optional)

---

## License

Part of the llm-sim project.

---

## Related Projects

- **[llm-sim-economic](../llm-sim-economic)** - Economic simulation implementations
- **llm-sim-server** (planned) - Control plane for managing multiple simulations

---

**This is a pure framework library.** To run simulations, use or create a domain implementation repository like `llm-sim-economic`.
