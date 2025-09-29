# Data Model Specification

## Core Models

### SimulationConfig
Pydantic model for YAML configuration parsing.

```python
class SimulationConfig(BaseModel):
    simulation: SimulationSettings
    engine: EngineConfig
    agents: List[AgentConfig]
    validator: ValidatorConfig
    logging: LoggingConfig

class SimulationSettings(BaseModel):
    name: str
    max_turns: int
    termination: TerminationConditions

class TerminationConditions(BaseModel):
    min_value: Optional[float] = None
    max_value: Optional[float] = None

class EngineConfig(BaseModel):
    type: str
    interest_rate: float

class AgentConfig(BaseModel):
    name: str
    type: str
    initial_economic_strength: float

class ValidatorConfig(BaseModel):
    type: str

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"
```

### State
Immutable state representation using Pydantic.

```python
class SimulationState(BaseModel):
    turn: int
    agents: Dict[str, AgentState]
    global_state: GlobalState

    class Config:
        frozen = True  # Immutable

class AgentState(BaseModel):
    name: str
    economic_strength: float

    class Config:
        frozen = True

class GlobalState(BaseModel):
    interest_rate: float
    total_economic_value: float

    class Config:
        frozen = True
```

### Action
Action representation with validation tracking.

```python
class Action(BaseModel):
    agent_name: str
    action_type: ActionType
    parameters: Dict[str, Any]
    validated: bool = False
    validation_timestamp: Optional[datetime] = None

    def mark_validated(self) -> "Action":
        return self.model_copy(
            update={
                "validated": True,
                "validation_timestamp": datetime.now()
            }
        )

class ActionType(str, Enum):
    GROW = "grow"
    MAINTAIN = "maintain"
    DECLINE = "decline"
```

## Data Flow

### 1. Configuration Loading
```
YAML File → PyYAML → SimulationConfig → Validation
```

### 2. State Initialization
```
SimulationConfig → Initial SimulationState → Engine Memory
```

### 3. Turn Processing
```
Current State → Agents → Actions → Validator → Validated Actions → Engine → New State
```

### 4. State Transitions
- States are immutable
- Each turn creates new state object
- Previous states can be retained for history

## Validation Rules

### Configuration Validation
- `max_turns` > 0
- `interest_rate` between -1.0 and 1.0
- All agent names unique
- Valid engine/validator/agent types

### State Validation
- `turn` >= 0
- `economic_strength` >= 0
- Consistent agent names across turns

### Action Validation
- `agent_name` exists in current state
- `action_type` is valid enum value
- Parameters match action type requirements

## Serialization

### YAML Support
All configs loadable from YAML:
```yaml
simulation:
  name: "Test Sim"
  max_turns: 100
```

### JSON Support
States serializable to JSON for logging:
```json
{
  "turn": 5,
  "agents": {
    "Nation_A": {
      "economic_strength": 1276.28
    }
  }
}
```

## Type Safety

### Runtime Validation
- Pydantic validates all data at runtime
- Type mismatches raise clear errors
- Optional fields have defaults

### Static Type Checking
- Full mypy compatibility
- Type hints on all public methods
- Generic types where appropriate

## Extensibility

### Custom Fields
Models support extension via inheritance:
```python
class ExtendedAgentState(AgentState):
    military_strength: float
    diplomatic_reputation: float
```

### Custom Validators
Pydantic validators for business logic:
```python
@field_validator('interest_rate')
def validate_interest_rate(cls, v):
    if not -1.0 <= v <= 1.0:
        raise ValueError('Interest rate must be between -100% and 100%')
    return v
```