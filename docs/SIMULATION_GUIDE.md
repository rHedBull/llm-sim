# Simulation Creation Guide

**A comprehensive guide to creating and configuring simulations with the llm-sim framework.**

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration Structure](#configuration-structure)
3. [State Variables](#state-variables)
4. [Partial Observability](#partial-observability)
5. [Agent Configuration](#agent-configuration)
6. [Engine Configuration](#engine-configuration)
7. [Validator Configuration](#validator-configuration)
8. [LLM Integration](#llm-integration)
9. [Checkpointing](#checkpointing)
10. [Complete Examples](#complete-examples)

---

## Overview

Simulations in llm-sim are configured using YAML files that define:

- **State variables** - What data agents track
- **Agents** - Who makes decisions
- **Engine** - How the world evolves
- **Validator** - What actions are valid
- **Observability** - What information agents can see
- **LLM settings** - How agents reason
- **Simulation parameters** - Runtime configuration

---

## Configuration Structure

A complete configuration file has this structure:

```yaml
simulation:
  name: "My Simulation"
  max_turns: 100
  checkpoint_interval: 10

state_variables:
  agent_vars:
    # Agent-specific variables
  global_vars:
    # Shared global state

agents:
  - name: Agent1
    type: my_agent

engine:
  type: my_engine

validator:
  type: my_validator

observability:
  enabled: true
  # Partial observability configuration

llm:
  model: "llama3.2"
  host: "http://localhost:11434"

logging:
  level: "INFO"
  format: "json"
```

---

## State Variables

Define custom state variables that agents track. The framework generates Pydantic models from these definitions.

### Agent Variables

Variables that each agent tracks individually:

```yaml
state_variables:
  agent_vars:
    economic_strength:
      type: float
      min: 0
      default: 100.0
      description: "Agent's economic power"

    tech_level:
      type: int
      min: 1
      max: 10
      default: 1
      description: "Technology advancement level"

    alliance:
      type: str
      default: "neutral"
      description: "Current alliance membership"

    is_active:
      type: bool
      default: true
      description: "Whether agent is participating"
```

### Global Variables

Variables shared across all agents:

```yaml
state_variables:
  global_vars:
    interest_rate:
      type: float
      min: 0.0
      max: 1.0
      default: 0.05
      description: "Global interest rate"

    turn:
      type: int
      default: 0
      description: "Current simulation turn"

    total_wealth:
      type: float
      default: 0.0
      description: "Sum of all agent wealth"
```

### Variable Types

Supported types:

| Type | Example | Constraints |
|------|---------|-------------|
| `float` | `economic_strength: 100.0` | `min`, `max` |
| `int` | `tech_level: 5` | `min`, `max` |
| `str` | `alliance: "NATO"` | - |
| `bool` | `is_active: true` | - |

### Variable Constraints

Optional validation constraints:

```yaml
economic_strength:
  type: float
  min: 0          # Minimum value (inclusive)
  max: 1000       # Maximum value (inclusive)
  default: 100.0  # Initial value
```

---

## Partial Observability

Control what information each agent can see. This enables realistic simulations where agents have incomplete or noisy information.

### Basic Setup

```yaml
observability:
  enabled: true

  variable_visibility:
    external: [economic_strength, position]
    internal: [secret_reserves, strategy]

  matrix:
    - [Agent1, Agent2, external, 0.2]
    - [Agent1, Agent3, unaware, null]
    - [Agent1, global, external, 0.1]

  default:
    level: external
    noise: 0.1
```

### Observability Levels

Three levels control what agents can see:

| Level | Meaning | Use Case |
|-------|---------|----------|
| `unaware` | Target is completely invisible | Unknown agents, hidden actors |
| `external` | Only public variables visible | Competitors, public information |
| `insider` | All variables visible | Allies, own state, trusted sources |

### Variable Visibility

Classify variables as external (public) or internal (private):

```yaml
variable_visibility:
  external:
    - economic_strength  # Public information
    - position
    - tech_level

  internal:
    - secret_reserves    # Private information
    - hidden_strategy
    - internal_plans
```

**Rules:**
- Variables in `external` list are visible to `external` and `insider` observers
- Variables in `internal` list are only visible to `insider` observers
- Variables not listed default to `external` (backward compatible)
- No variable can be in both lists (validation error)

### Observability Matrix

Define observer-target relationships:

```yaml
matrix:
  # Format: [observer, target, level, noise]

  # Agent observes self perfectly
  - [Agent1, Agent1, insider, 0.0]

  # Agent observes competitor with noise
  - [Agent1, Agent2, external, 0.2]

  # Agent unaware of hidden actor
  - [Agent1, Agent3, unaware, null]

  # Agent observes global state
  - [Agent1, global, external, 0.1]
```

**Matrix Entry Format:**
- `observer`: Agent ID making the observation
- `target`: Agent ID or "global" being observed
- `level`: `unaware`, `external`, or `insider`
- `noise`: Float ≥ 0.0 (noise factor) or `null` for unaware

### Noise Model

Deterministic multiplicative noise is applied to numeric variables:

```yaml
# 0.2 noise means ±20% variation
- [Agent1, Agent2, external, 0.2]
```

**Noise Properties:**
- **Deterministic**: Same seed → same noise value (reproducible)
- **Multiplicative**: `noisy_value = true_value * (1.0 + random[-noise, +noise])`
- **Bounded**: Noise factor controls max deviation
- **Seeded**: Based on `(turn, observer_id, variable_name)`

**Example:**
```python
# True value: economic_strength = 1000.0
# Noise factor: 0.2 (±20%)
# Possible noisy value: 850.0 (15% below)
# Range: [800.0, 1200.0]
```

**Special Cases:**
- `noise: 0.0` - No noise, perfect information
- `noise: null` - For unaware level (not used)
- Integer values are noised then rounded

### Default Observability

Fallback for undefined observer-target pairs:

```yaml
default:
  level: external      # Default observability level
  noise: 0.1          # Default noise factor
```

**When used:**
- Observer-target pair not in matrix
- Allows sparse matrix configuration
- Common pattern: default to limited visibility

### Asymmetric Visibility

Agents can have different views of each other:

```yaml
matrix:
  # Agent1 sees Agent2
  - [Agent1, Agent2, external, 0.2]

  # Agent2 cannot see Agent1 (not in matrix)
  # Falls back to default (or unaware if default.level = unaware)
```

### Global State Observability

Global state is treated like any agent:

```yaml
matrix:
  # Full access to global state
  - [Agent1, global, insider, 0.0]

  # Limited access with noise
  - [Agent2, global, external, 0.15]

  # No access to global state
  - [Agent3, global, unaware, null]
```

### Backward Compatibility

Full observability (legacy behavior):

```yaml
# Option 1: Disable observability
observability:
  enabled: false

# Option 2: Omit observability section entirely
# (observability is optional)
```

When disabled or omitted, agents receive complete ground truth state.

### Complete Observability Example

```yaml
observability:
  enabled: true

  # Classify variables
  variable_visibility:
    external:
      - economic_strength
      - position
      - public_policy
    internal:
      - secret_reserves
      - hidden_strategy
      - intelligence_budget

  # Define observer-target relationships
  matrix:
    # Agent1 (insider to self, external to others)
    - [Agent1, Agent1, insider, 0.0]
    - [Agent1, Agent2, external, 0.2]
    - [Agent1, Agent3, external, 0.2]
    - [Agent1, global, external, 0.1]

    # Agent2 (similar setup)
    - [Agent2, Agent2, insider, 0.0]
    - [Agent2, Agent1, external, 0.15]
    - [Agent2, Agent3, unaware, null]  # Doesn't know Agent3 exists
    - [Agent2, global, external, 0.1]

    # Agent3 (spy with insider access to Agent1)
    - [Agent3, Agent3, insider, 0.0]
    - [Agent3, Agent1, insider, 0.05]  # Infiltrated Agent1
    - [Agent3, Agent2, external, 0.2]
    - [Agent3, global, insider, 0.0]   # Full global knowledge

  # Default for undefined pairs
  default:
    level: unaware  # Hidden by default
    noise: 0.0
```

### Observability Use Cases

**1. Economic Competition**
```yaml
# Companies see competitors' public data with noise
- [CompanyA, CompanyB, external, 0.15]
```

**2. Intelligence Networks**
```yaml
# Spy has insider access to target
- [Spy, Target, insider, 0.05]
```

**3. Fog of War**
```yaml
# Military units aware of nearby units, unaware of distant ones
- [Unit1, Unit2, external, 0.3]  # Nearby
- [Unit1, Unit3, unaware, null]  # Distant
```

**4. Information Asymmetry**
```yaml
# Central bank has perfect global view
- [CentralBank, global, insider, 0.0]
# Commercial banks have noisy view
- [Bank1, global, external, 0.1]
```

**5. Trust Networks**
```yaml
# Allied agents share insider information
- [Ally1, Ally2, insider, 0.0]
# Neutral agents see public data
- [Neutral1, Ally1, external, 0.2]
```

---

## Agent Configuration

Define agents that make decisions:

```yaml
agents:
  - name: Agent1
    type: my_agent
    config:
      # Agent-specific parameters
      risk_tolerance: 0.7
      strategy: "aggressive"

  - name: Agent2
    type: my_agent
    config:
      risk_tolerance: 0.3
      strategy: "defensive"
```

### LLM Agents

For agents using LLM reasoning:

```yaml
agents:
  - name: Agent1
    type: llm_agent
    config:
      system_prompt: |
        You are a strategic decision maker.
        Maximize economic strength while maintaining stability.

      temperature: 0.7
      max_tokens: 500
```

---

## Engine Configuration

Define how the simulation world evolves:

```yaml
engine:
  type: economic_engine
  config:
    interest_rate: 0.05
    inflation_rate: 0.02
    growth_rate: 0.03
```

Common engine types:
- `economic_engine` - Economic simulations
- `game_engine` - Game-theoretic scenarios
- `custom_engine` - Your custom implementation

---

## Validator Configuration

Define action validation rules:

```yaml
validator:
  type: llm_validator
  config:
    domain: "economic"
    permissive: false
    max_retries: 3
```

**Permissive mode:**
- `true` - Allow invalid actions (log warnings)
- `false` - Reject invalid actions (strict validation)

---

## LLM Integration

Configure LLM settings for reasoning agents:

```yaml
llm:
  model: "llama3.2"
  host: "http://localhost:11434"
  timeout: 60.0
  max_retries: 3
  temperature: 0.7
  stream: true
```

### Supported LLM Providers

**Ollama (default):**
```yaml
llm:
  model: "llama3.2"
  host: "http://localhost:11434"
```

**OpenAI-compatible:**
```yaml
llm:
  model: "gpt-4"
  host: "https://api.openai.com/v1"
  api_key: "${OPENAI_API_KEY}"
```

### Model Selection

| Model | Use Case | Performance |
|-------|----------|-------------|
| `llama3.2` | Fast reasoning, local | Good for testing |
| `llama3.3:70b` | High quality reasoning | Slower, better decisions |
| `gpt-4` | Production quality | Best reasoning, requires API |
| `claude-3-opus` | Long context, nuanced | Expensive, high quality |

---

## Checkpointing

Configure state persistence:

```yaml
simulation:
  checkpoint_interval: 10  # Save every 10 turns
```

### Output Structure

```
output/{run_id}/
├── checkpoints/
│   ├── turn_10.json
│   ├── turn_20.json
│   ├── last.json    # Latest state
│   └── final.json   # Final state
├── logs/
│   └── simulation.log
└── result.json      # Complete results
```

### Checkpoint Contents

Each checkpoint includes:
- Current turn number
- All agent states
- Global state
- Reasoning chains (for LLM agents)
- Metadata (timestamp, schema hash)

### Loading Checkpoints

```python
from llm_sim.persistence import CheckpointManager

manager = CheckpointManager(output_dir="output/run_20231101_123456")
state = manager.load_checkpoint("last")
```

---

## Complete Examples

### Example 1: Simple Economic Simulation

```yaml
simulation:
  name: "Simple Economy"
  max_turns: 50
  checkpoint_interval: 10

state_variables:
  agent_vars:
    wealth:
      type: float
      min: 0
      default: 1000.0

  global_vars:
    interest_rate:
      type: float
      default: 0.05

agents:
  - name: Trader1
    type: llm_agent
  - name: Trader2
    type: llm_agent

engine:
  type: economic_engine

validator:
  type: llm_validator
  config:
    permissive: false

llm:
  model: "llama3.2"
  host: "http://localhost:11434"

logging:
  level: "INFO"
```

### Example 2: Partial Observability Scenario

```yaml
simulation:
  name: "Intelligence Game"
  max_turns: 100
  checkpoint_interval: 20

state_variables:
  agent_vars:
    economic_strength:
      type: float
      min: 0
      default: 1000.0

    military_power:
      type: float
      min: 0
      default: 100.0

    secret_operations:
      type: int
      default: 0

    intelligence_level:
      type: int
      min: 0
      max: 10
      default: 5

  global_vars:
    global_tension:
      type: float
      min: 0.0
      max: 1.0
      default: 0.3

agents:
  - name: Nation1
    type: llm_agent

  - name: Nation2
    type: llm_agent

  - name: Spy
    type: llm_agent

engine:
  type: geopolitical_engine

validator:
  type: llm_validator

observability:
  enabled: true

  variable_visibility:
    external:
      - economic_strength
      - military_power

    internal:
      - secret_operations
      - intelligence_level

  matrix:
    # Nation1 sees self and public info of Nation2
    - [Nation1, Nation1, insider, 0.0]
    - [Nation1, Nation2, external, 0.2]
    - [Nation1, Spy, unaware, null]
    - [Nation1, global, external, 0.1]

    # Nation2 similar
    - [Nation2, Nation2, insider, 0.0]
    - [Nation2, Nation1, external, 0.2]
    - [Nation2, Spy, unaware, null]
    - [Nation2, global, external, 0.1]

    # Spy has insider access to Nation1
    - [Spy, Spy, insider, 0.0]
    - [Spy, Nation1, insider, 0.05]
    - [Spy, Nation2, external, 0.15]
    - [Spy, global, insider, 0.0]

  default:
    level: unaware
    noise: 0.0

llm:
  model: "llama3.3:70b"
  host: "http://localhost:11434"
  temperature: 0.8

logging:
  level: "DEBUG"
  format: "json"
```

### Example 3: Market Competition

```yaml
simulation:
  name: "Market Competition"
  max_turns: 200
  checkpoint_interval: 25

state_variables:
  agent_vars:
    market_share:
      type: float
      min: 0.0
      max: 1.0
      default: 0.1

    product_quality:
      type: float
      min: 0.0
      max: 10.0
      default: 5.0

    rd_investment:
      type: float
      min: 0.0
      default: 100.0

    pricing_strategy:
      type: str
      default: "moderate"

    # Private information
    cost_structure:
      type: float
      default: 50.0

    secret_innovation:
      type: int
      default: 0

  global_vars:
    market_demand:
      type: float
      default: 1000.0

    average_price:
      type: float
      default: 100.0

agents:
  - name: Company1
    type: llm_agent
    config:
      strategy: "cost_leader"

  - name: Company2
    type: llm_agent
    config:
      strategy: "differentiator"

  - name: Company3
    type: llm_agent
    config:
      strategy: "innovator"

engine:
  type: market_engine
  config:
    elasticity: 1.5
    innovation_rate: 0.1

validator:
  type: market_validator
  config:
    permissive: false

observability:
  enabled: true

  variable_visibility:
    external:
      - market_share
      - product_quality
      - pricing_strategy

    internal:
      - rd_investment
      - cost_structure
      - secret_innovation

  matrix:
    # Each company sees competitors' public data with noise
    - [Company1, Company1, insider, 0.0]
    - [Company1, Company2, external, 0.15]
    - [Company1, Company3, external, 0.15]
    - [Company1, global, external, 0.05]

    - [Company2, Company2, insider, 0.0]
    - [Company2, Company1, external, 0.15]
    - [Company2, Company3, external, 0.15]
    - [Company2, global, external, 0.05]

    - [Company3, Company3, insider, 0.0]
    - [Company3, Company1, external, 0.15]
    - [Company3, Company2, external, 0.15]
    - [Company3, global, external, 0.05]

  default:
    level: external
    noise: 0.2

llm:
  model: "gpt-4"
  host: "https://api.openai.com/v1"
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.7

logging:
  level: "INFO"
  format: "json"
```

---

## Configuration Validation

The framework validates configurations on load:

### Common Validation Errors

**1. Unknown variable in observability:**
```yaml
variable_visibility:
  external: [unknown_var]  # ERROR: not in state_variables
```

**2. Variable in both external and internal:**
```yaml
variable_visibility:
  external: [wealth]
  internal: [wealth]  # ERROR: cannot be both
```

**3. Unknown agent in matrix:**
```yaml
matrix:
  - [UnknownAgent, Agent1, external, 0.1]  # ERROR: agent not defined
```

**4. Negative noise:**
```yaml
matrix:
  - [Agent1, Agent2, external, -0.1]  # ERROR: noise must be >= 0
```

**5. Invalid observability level:**
```yaml
matrix:
  - [Agent1, Agent2, public, 0.1]  # ERROR: must be unaware/external/insider
```

---

## Best Practices

### 1. Start Simple

Begin with basic configuration, add observability later:

```yaml
# Phase 1: Basic simulation
agents:
  - name: Agent1
    type: my_agent

# Phase 2: Add observability
observability:
  enabled: true
  # ...
```

### 2. Use Meaningful Noise Levels

| Noise | Interpretation | Use Case |
|-------|----------------|----------|
| 0.0 | Perfect information | Insider, own state |
| 0.05 | High quality intel | Spy networks, allies |
| 0.1-0.2 | Public information | Market data, news |
| 0.3+ | Low quality intel | Rumors, distant observations |

### 3. Leverage Defaults

Use sparse matrix + default for cleaner config:

```yaml
matrix:
  # Only specify special relationships
  - [Agent1, Agent1, insider, 0.0]
  - [Spy, Target, insider, 0.05]

default:
  level: external  # Everyone else gets external view
  noise: 0.2
```

### 4. Test Incrementally

1. Test with `enabled: false` (full observability)
2. Enable observability with low noise
3. Gradually increase noise and restrictions
4. Verify agent behavior changes appropriately

### 5. Document Your Schema

Add descriptions to variables:

```yaml
state_variables:
  agent_vars:
    economic_strength:
      type: float
      default: 1000.0
      description: "Agent's total economic power in GDP units"
```

### 6. Use Structured Logging

Enable DEBUG logging to see observations:

```yaml
logging:
  level: "DEBUG"
  format: "json"
```

Look for events:
- `observation_construction` - When observations are built
- `observation_filtered.agents_filtered` - Which agents are visible
- `noise_applied` - Noise application details

---

## Troubleshooting

### Agents See Everything Despite Observability

**Problem:** Observability enabled but agents still see full state

**Solutions:**
1. Check `observability.enabled: true`
2. Verify matrix entries exist for observer-target pairs
3. Check default level isn't `insider`
4. Review logs for `observation_filtered` events

### Noise Not Applied

**Problem:** Observed values identical to ground truth

**Solutions:**
1. Verify `noise > 0.0` in matrix entries
2. Check variable is numeric (noise only applies to int/float)
3. For integers, noise may round to same value (expected)

### Matrix Too Complex

**Problem:** Too many matrix entries to maintain

**Solutions:**
1. Use `default` for common cases
2. Group agents by role with same observability patterns
3. Consider if full asymmetry is needed

### Variables Missing in Observations

**Problem:** Expected variables not in observation

**Solutions:**
1. Check variable is in `external` list for external observers
2. Verify observability level is correct
3. For `unaware`, entire agent is excluded (expected)

---

## Next Steps

- **[API Reference](API.md)** - Extending the framework
- **[LLM Setup](LLM_SETUP.md)** - Configuring LLM providers
- **[Platform Architecture](PLATFORM_ARCHITECTURE.md)** - Multi-simulation orchestration
- **[Example Implementation](https://github.com/your-org/llm-sim-economic)** - Complete reference

---

**Need help?** Check existing configurations in the `scenarios/` directory of example implementations.
