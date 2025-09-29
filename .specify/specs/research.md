# Research & Analysis: Simulation Loop Implementation

## Codebase Analysis

### Current Structure
```
llm_sim/
├── src/
│   └── llm_sim/  (empty module, greenfield implementation)
├── templates/   (likely for YAML configurations)
├── .specify/    (specification framework)
├── pyproject.toml (Python project configuration)
└── main.py      (entry point)
```

### Integration Points
1. **Module Structure**: `src/llm_sim/` is empty, allowing clean implementation
2. **Configuration**: `templates/` directory suggests YAML config storage
3. **Package Management**: Uses `uv` as specified in constitution
4. **Python Version**: `.python-version` file present (Python 3.x)

## Technology Choices

### Core Dependencies
1. **pydantic**: Data validation and settings management
   - Provides automatic validation
   - Type safety with minimal boilerplate
   - Serialization/deserialization support

2. **PyYAML**: Configuration file parsing
   - Human-readable configuration format
   - Widely adopted standard
   - Simple API

3. **structlog**: Structured logging
   - Better than basic logging module
   - Structured output for observability
   - Context preservation

### Standard Library
1. **abc**: Abstract Base Classes for interfaces
2. **pathlib**: Modern path handling
3. **typing**: Type hints for clarity
4. **dataclasses**: Simpler alternative where pydantic overhead not needed

## Architecture Decisions

### Component Organization
```
src/llm_sim/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── engine.py      # BaseEngine ABC and EconomicEngine impl
│   ├── agent.py       # BaseAgent ABC and NationAgent impl
│   ├── validator.py   # BaseValidator ABC and AlwaysValidValidator impl
│   └── logger.py      # Logging configuration
├── models/
│   ├── __init__.py
│   ├── state.py       # State pydantic model
│   ├── action.py      # Action pydantic model
│   └── config.py      # SimulationConfig model
└── simulation.py      # Main simulation loop orchestration
```

### Data Flow
1. YAML config → SimulationConfig (pydantic)
2. SimulationConfig → Engine initialization
3. Engine → State broadcast to Agents
4. Agents → Actions to Validator
5. Validator → Validated Actions to Engine
6. Engine → State update
7. Loop until termination conditions

## Implementation Patterns

### KISS Compliance
- Single-file components (< 200 lines each)
- Flat class hierarchy (Base → Concrete only)
- Synchronous execution (no async complexity)

### DRY Compliance
- Shared base classes for all extensible components
- Single source of truth for state in Engine
- Centralized configuration loading

### Testing Strategy
- Unit tests for each component in isolation
- Integration test for full simulation loop
- Property-based testing for state transitions
- Fixtures for common test data

## Dependencies to Add
```toml
[project.dependencies]
pydantic = "^2.5.0"
pyyaml = "^6.0"
structlog = "^24.1.0"
```

## Development Dependencies
```toml
[project.dev-dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
mypy = "^1.7.0"
black = "^23.12.0"
ruff = "^0.1.9"
```

## Configuration Example
```yaml
# simulation_config.yaml
simulation:
  name: "Economic Growth Simulation"
  max_turns: 100
  termination:
    min_value: 0
    max_value: 1000000

engine:
  type: "EconomicEngine"
  interest_rate: 0.05

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

## Next Steps
1. Create data models with pydantic
2. Define ABC interfaces
3. Implement concrete classes
4. Set up test framework
5. Create example configurations