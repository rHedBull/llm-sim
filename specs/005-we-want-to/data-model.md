# Data Model: Simulation Infrastructure Reorganization

**Feature**: 005-we-want-to | **Date**: 2025-09-30

## Overview

This document defines the structural entities involved in separating abstract infrastructure from concrete implementations.

## Directory Structure Entity

### Infrastructure Directory
**Purpose**: Houses all abstract classes (both base interfaces and pattern implementations)

**Structure**:
```
infrastructure/
├── base/                 # Minimal abstract interfaces
│   ├── __init__.py
│   ├── agent.py         # BaseAgent class
│   ├── engine.py        # BaseEngine class
│   └── validator.py     # BaseValidator class
└── patterns/            # Pattern-providing abstract classes
    ├── __init__.py
    ├── llm_agent.py     # LLMAgent (extends BaseAgent)
    ├── llm_engine.py    # LLMEngine (extends BaseEngine)
    └── llm_validator.py # LLMValidator (extends BaseValidator)
```

**Constraints**:
- Files in `base/` must contain ONLY abstract base classes
- Files in `patterns/` must contain abstract classes that extend `base/` classes
- No concrete implementations allowed in `infrastructure/`

### Implementations Directory
**Purpose**: Houses all concrete domain-specific implementations

**Structure**:
```
implementations/
├── agents/
│   ├── __init__.py
│   ├── econ_llm_agent.py    # EconLLMAgent (extends LLMAgent)
│   └── nation.py            # NationAgent (extends BaseAgent)
├── engines/
│   ├── __init__.py
│   ├── econ_llm_engine.py   # EconLLMEngine (extends LLMEngine)
│   └── economic.py          # EconomicEngine (extends BaseEngine)
└── validators/
    ├── __init__.py
    ├── econ_llm_validator.py # EconLLMValidator (extends LLMValidator)
    └── always_valid.py       # AlwaysValidValidator (extends BaseValidator)
```

**Constraints**:
- Files must follow snake_case naming
- Class names must be PascalCase version of filename (e.g., `econ_llm_agent.py` → `EconLLMAgent`)
- Each file contains exactly one concrete implementation class
- Must extend an abstract class from `infrastructure/`

## Module Import Path Mapping

### Old → New Import Paths

| Component | Old Path | New Path |
|-----------|----------|----------|
| BaseAgent | `llm_sim.agents.base.BaseAgent` | `llm_sim.infrastructure.base.agent.BaseAgent` |
| BaseEngine | `llm_sim.engines.base.BaseEngine` | `llm_sim.infrastructure.base.engine.BaseEngine` |
| BaseValidator | `llm_sim.validators.base.BaseValidator` | `llm_sim.infrastructure.base.validator.BaseValidator` |
| LLMAgent | `llm_sim.agents.llm_agent.LLMAgent` | `llm_sim.infrastructure.patterns.llm_agent.LLMAgent` |
| LLMEngine | `llm_sim.engines.llm_engine.LLMEngine` | `llm_sim.infrastructure.patterns.llm_engine.LLMEngine` |
| LLMValidator | `llm_sim.validators.llm_validator.LLMValidator` | `llm_sim.infrastructure.patterns.llm_validator.LLMValidator` |
| EconLLMAgent | `llm_sim.agents.econ_llm_agent.EconLLMAgent` | `llm_sim.implementations.agents.econ_llm_agent.EconLLMAgent` |
| NationAgent | `llm_sim.agents.nation.NationAgent` | `llm_sim.implementations.agents.nation.NationAgent` |
| EconLLMEngine | `llm_sim.engines.econ_llm_engine.EconLLMEngine` | `llm_sim.implementations.engines.econ_llm_engine.EconLLMEngine` |
| EconLLMValidator | `llm_sim.validators.econ_llm_validator.EconLLMValidator` | `llm_sim.implementations.validators.econ_llm_validator.EconLLMValidator` |
| AlwaysValidValidator | `llm_sim.validators.always_valid.AlwaysValidValidator` | `llm_sim.implementations.validators.always_valid.AlwaysValidValidator` |

### Convenience Imports (Optional)

Top-level `__init__.py` files can provide convenience re-exports:

```python
# src/llm_sim/infrastructure/__init__.py
from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.infrastructure.base.engine import BaseEngine
from llm_sim.infrastructure.base.validator import BaseValidator
from llm_sim.infrastructure.patterns.llm_agent import LLMAgent
from llm_sim.infrastructure.patterns.llm_engine import LLMEngine
from llm_sim.infrastructure.patterns.llm_validator import LLMValidator

__all__ = [
    "BaseAgent", "BaseEngine", "BaseValidator",
    "LLMAgent", "LLMEngine", "LLMValidator"
]
```

## Discovery Mechanism Entity

### ComponentDiscovery Interface

**Purpose**: Dynamically load concrete implementations by filename reference

**Attributes**:
- `component_type`: str - One of "agents", "engines", "validators"
- `implementations_dir`: Path - Root implementations directory
- `_cache`: Dict[str, Type] - Loaded class cache

**Methods**:

```python
def discover(filename: str, base_class: Type) -> Type:
    """
    Load concrete implementation class from filename.

    Args:
        filename: Name of Python file (without .py), e.g., "econ_llm_agent"
        base_class: Expected base class (for validation)

    Returns:
        Loaded class that inherits from base_class

    Raises:
        FileNotFoundError: If filename.py doesn't exist
        TypeError: If loaded class doesn't inherit from base_class
        AttributeError: If expected class name not found in module
    """
```

```python
def validate_implementation(cls: Type, base_class: Type) -> bool:
    """
    Verify that a loaded class properly implements base class.

    Args:
        cls: Loaded class
        base_class: Expected base class

    Returns:
        True if cls inherits from base_class and implements required methods
    """
```

```python
def list_available(component_type: str) -> List[str]:
    """
    List all available implementations for a component type.

    Args:
        component_type: "agents", "engines", or "validators"

    Returns:
        List of available filenames (without .py extension)
    """
```

**Constraints**:
- Must cache loaded classes for performance
- Must validate inheritance at load time
- Must provide clear error messages for common mistakes
- Must handle missing files gracefully

## Configuration Schema Entity

### YAML Configuration Format

**No changes to user-facing configuration**. Existing format maintained:

```yaml
simulation:
  name: "Economic Simulation"
  max_turns: 100

agents:
  - name: "Nation1"
    type: "nation"              # Filename reference (nation.py)
    initial_economic_strength: 100
    strategy: "grow"

  - name: "Nation2"
    type: "econ_llm_agent"      # Filename reference (econ_llm_agent.py)
    initial_economic_strength: 100

engine:
  type: "econ_llm_engine"       # Filename reference (econ_llm_engine.py)
  interest_rate: 5.0

validator:
  type: "econ_llm_validator"    # Filename reference (econ_llm_validator.py)
```

**Key Points**:
- `type` field references filename (without `.py`)
- Discovery mechanism resolves filename to concrete class
- No change needed to existing configurations
- Backward compatibility maintained

## Abstract Class Interface Contracts

### BaseAgent Interface

```python
class BaseAgent(ABC):
    """Minimal interface for simulation agents."""

    name: str
    _current_state: Optional[SimulationState]

    @abstractmethod
    def decide_action(self, state: SimulationState) -> Action:
        """Decide action based on current state."""
        pass

    def receive_state(self, state: SimulationState) -> None:
        """Receive state update."""
        pass

    def get_current_state(self) -> Optional[SimulationState]:
        """Get current state."""
        pass
```

### BaseEngine Interface

```python
class BaseEngine(ABC):
    """Minimal interface for simulation engines."""

    config: SimulationConfig
    _state: Optional[SimulationState]
    _turn_counter: int

    @abstractmethod
    def initialize_state(self) -> SimulationState:
        """Create initial simulation state."""
        pass

    @abstractmethod
    def apply_actions(self, actions: List[Action]) -> SimulationState:
        """Apply validated actions."""
        pass

    @abstractmethod
    def apply_engine_rules(self, state: SimulationState) -> SimulationState:
        """Apply engine-specific rules."""
        pass

    @abstractmethod
    def check_termination(self, state: SimulationState) -> bool:
        """Check if simulation should terminate."""
        pass
```

### BaseValidator Interface

```python
class BaseValidator(ABC):
    """Minimal interface for action validators."""

    validation_count: int
    rejection_count: int

    @abstractmethod
    def validate_action(self, action: Action, state: SimulationState) -> bool:
        """Validate single action."""
        pass

    def validate_actions(self, actions: List[Action], state: SimulationState) -> List[Action]:
        """Validate all actions."""
        pass

    def get_stats(self) -> Dict[str, float]:
        """Get validation statistics."""
        pass
```

## Validation Rules

### File Organization Validation
- All abstract classes must be under `infrastructure/`
- All concrete classes must be under `implementations/`
- No cross-contamination allowed

### Naming Convention Validation
- Filename: `snake_case.py`
- Class name: `PascalCase` (derived from filename)
- Example: `econ_llm_agent.py` must contain `EconLLMAgent`

### Inheritance Validation
- Classes in `infrastructure/base/` must be abstract (use `ABC`, `@abstractmethod`)
- Classes in `infrastructure/patterns/` must extend `base/` classes
- Classes in `implementations/` must extend either `base/` or `patterns/` classes
- No concrete class can extend another concrete class

### Discovery Validation
- Referenced filename must exist in appropriate `implementations/` subdirectory
- Loaded class must inherit from expected base class
- Loaded class must implement all abstract methods

## Entity Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                      │
│  ┌──────────────┐                  ┌──────────────────┐    │
│  │  Base Layer  │                  │  Patterns Layer  │     │
│  │              │◄─────extends─────│                  │     │
│  │ BaseAgent    │                  │  LLMAgent        │     │
│  │ BaseEngine   │                  │  LLMEngine       │     │
│  │ BaseValidator│                  │  LLMValidator    │     │
│  └──────────────┘                  └──────────────────┘     │
└──────────────▲─────────────────────────────▲────────────────┘
               │                              │
               │                              │
               └──────extends────────────────┘
                              │
                              │
┌─────────────────────────────────────────────────────────────┐
│                  Implementations Layer                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Concrete Implementations                 │  │
│  │  EconLLMAgent    (extends LLMAgent)                  │  │
│  │  NationAgent     (extends BaseAgent)                 │  │
│  │  EconLLMEngine   (extends LLMEngine)                 │  │
│  │  EconLLMValidator (extends LLMValidator)             │  │
│  │  AlwaysValidValidator (extends BaseValidator)        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Migration Checklist

- [ ] Create `infrastructure/base/` directory structure
- [ ] Create `infrastructure/patterns/` directory structure
- [ ] Create `implementations/{agents,engines,validators}/` directories
- [ ] Move abstract base classes to `infrastructure/base/`
- [ ] Move LLM pattern classes to `infrastructure/patterns/`
- [ ] Move concrete implementations to `implementations/`
- [ ] Update all import statements in moved files
- [ ] Update all test imports
- [ ] Implement discovery mechanism
- [ ] Update orchestrator to use discovery
- [ ] Verify YAML configs still work
- [ ] Run full test suite
