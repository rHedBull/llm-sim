# Migration Guide: Infrastructure Reorganization

This guide helps you migrate from the old flat structure to the new infrastructure-based organization.

## What Changed?

The codebase was reorganized to separate **infrastructure** (framework code) from **implementations** (domain-specific code):

### Old Structure (Before)
```
src/llm_sim/
├── agents/
│   ├── base.py              # BaseAgent
│   ├── llm_agent.py         # LLMAgent pattern
│   ├── nation.py            # NationAgent implementation
│   └── econ_llm_agent.py    # EconLLMAgent implementation
├── engines/
│   ├── base.py              # BaseEngine
│   ├── llm_engine.py        # LLMEngine pattern
│   ├── economic.py          # EconomicEngine implementation
│   └── econ_llm_engine.py   # EconLLMEngine implementation
└── validators/
    ├── base.py              # BaseValidator
    ├── llm_validator.py     # LLMValidator pattern
    ├── always_valid.py      # AlwaysValidValidator implementation
    └── econ_llm_validator.py # EconLLMValidator implementation
```

### New Structure (After)
```
src/llm_sim/
├── infrastructure/          # Framework code (stable)
│   ├── base/               # Abstract base classes
│   │   ├── agent.py        # BaseAgent
│   │   ├── engine.py       # BaseEngine
│   │   └── validator.py    # BaseValidator
│   └── patterns/           # LLM integration patterns
│       ├── llm_agent.py    # LLMAgent
│       ├── llm_engine.py   # LLMEngine
│       └── llm_validator.py # LLMValidator
│
└── implementations/        # Domain implementations (extensible)
    ├── agents/
    │   ├── nation.py
    │   └── econ_llm_agent.py
    ├── engines/
    │   ├── economic.py
    │   └── econ_llm_engine.py
    └── validators/
        ├── always_valid.py
        └── econ_llm_validator.py
```

## Benefits

1. **Clear separation**: Framework vs. domain code
2. **Better discoverability**: All implementations in one place
3. **Easier extension**: Add new implementations without modifying framework
4. **Reduced coupling**: Infrastructure is independent of specific domains
5. **Discovery-based loading**: Automatic component loading by filename

## Import Path Changes

### Base Classes

| Old Import | New Import |
|------------|------------|
| `from llm_sim.agents.base import BaseAgent` | `from llm_sim.infrastructure.base.agent import BaseAgent` |
| `from llm_sim.engines.base import BaseEngine` | `from llm_sim.infrastructure.base.engine import BaseEngine` |
| `from llm_sim.validators.base import BaseValidator` | `from llm_sim.infrastructure.base.validator import BaseValidator` |

**Convenience imports** (shorter):
```python
from llm_sim.infrastructure import BaseAgent, BaseEngine, BaseValidator
```

### LLM Patterns

| Old Import | New Import |
|------------|------------|
| `from llm_sim.agents.llm_agent import LLMAgent` | `from llm_sim.infrastructure.patterns.llm_agent import LLMAgent` |
| `from llm_sim.engines.llm_engine import LLMEngine` | `from llm_sim.infrastructure.patterns.llm_engine import LLMEngine` |
| `from llm_sim.validators.llm_validator import LLMValidator` | `from llm_sim.infrastructure.patterns.llm_validator import LLMValidator` |

**Convenience imports**:
```python
from llm_sim.infrastructure import LLMAgent, LLMEngine, LLMValidator
```

### Concrete Implementations

| Old Import | New Import |
|------------|------------|
| `from llm_sim.agents.nation import NationAgent` | `from llm_sim.implementations.agents.nation import NationAgent` |
| `from llm_sim.agents.econ_llm_agent import EconLLMAgent` | `from llm_sim.implementations.agents.econ_llm_agent import EconLLMAgent` |
| `from llm_sim.engines.economic import EconomicEngine` | `from llm_sim.implementations.engines.economic import EconomicEngine` |
| `from llm_sim.engines.econ_llm_engine import EconLLMEngine` | `from llm_sim.implementations.engines.econ_llm_engine import EconLLMEngine` |
| `from llm_sim.validators.always_valid import AlwaysValidValidator` | `from llm_sim.implementations.validators.always_valid import AlwaysValidValidator` |
| `from llm_sim.validators.econ_llm_validator import EconLLMValidator` | `from llm_sim.implementations.validators.econ_llm_validator import EconLLMValidator` |

## Migration Steps

### Step 1: Update Your Imports

**Before:**
```python
# old_simulation.py
from llm_sim.agents.nation import NationAgent
from llm_sim.engines.economic import EconomicEngine
from llm_sim.validators.always_valid import AlwaysValidValidator
```

**After:**
```python
# new_simulation.py
from llm_sim.implementations.agents.nation import NationAgent
from llm_sim.implementations.engines.economic import EconomicEngine
from llm_sim.implementations.validators.always_valid import AlwaysValidValidator
```

### Step 2: Update Custom Implementations

If you created custom agents/engines/validators:

**Before:**
```python
# my_custom_agent.py (in your project)
from llm_sim.agents.base import BaseAgent
from llm_sim.agents.llm_agent import LLMAgent

class MyAgent(LLMAgent):
    pass
```

**After:**
```python
# my_custom_agent.py (in your project)
from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.infrastructure.patterns.llm_agent import LLMAgent

class MyAgent(LLMAgent):
    pass
```

### Step 3: Test Your Changes

Run your test suite to verify everything works:

```bash
pytest tests/
```

## YAML Configs (No Changes Required!)

**Good news**: YAML configuration files don't need any changes! The discovery mechanism handles loading by filename.

```yaml
# This still works unchanged:
agents:
  - name: "Nation_A"
    type: "nation"  # ← Discovery finds implementations/agents/nation.py
    initial_economic_strength: 1000.0

engine:
  type: "economic"  # ← Discovery finds implementations/engines/economic.py
  interest_rate: 0.05

validator:
  type: "always_valid"  # ← Discovery finds implementations/validators/always_valid.py
```

The orchestrator uses `ComponentDiscovery` to automatically load implementations based on the `type` field, so your YAML configs remain backward compatible.

## Example Migration

### Before: Manual Imports

```python
# Old orchestrator-style code
from llm_sim.agents.nation import NationAgent
from llm_sim.engines.economic import EconomicEngine
from llm_sim.validators.always_valid import AlwaysValidValidator
from llm_sim.models.config import SimulationConfig

config = SimulationConfig(...)

# Manually instantiate
agents = [NationAgent(name="Nation_A")]
engine = EconomicEngine(config=config)
validator = AlwaysValidValidator()

# Run simulation manually
state = engine.initialize_state()
for turn in range(config.simulation.max_turns):
    actions = [agent.decide_action(state) for agent in agents]
    validated = validator.validate_actions(actions, state)
    state = engine.run_turn(validated)
```

### After: Discovery-Based Loading

```python
# New orchestrator-style code (recommended)
from llm_sim.orchestrator import SimulationOrchestrator

# Use YAML config with discovery
orchestrator = SimulationOrchestrator.from_yaml("config.yaml")
result = orchestrator.run()

# Or programmatic with discovery
from llm_sim.discovery import ComponentDiscovery
from pathlib import Path

discovery = ComponentDiscovery(Path("src/llm_sim"))

# Load by filename
NationAgent = discovery.load_agent("nation")
EconomicEngine = discovery.load_engine("economic")
AlwaysValidValidator = discovery.load_validator("always_valid")

# Instantiate as before
agents = [NationAgent(name="Nation_A")]
engine = EconomicEngine(config=config)
validator = AlwaysValidValidator()
```

## Finding and Replacing Imports

### Automated Search and Replace

Use your IDE or command line to update imports:

#### Find old base class imports:
```bash
grep -r "from llm_sim.agents.base import" .
grep -r "from llm_sim.engines.base import" .
grep -r "from llm_sim.validators.base import" .
```

#### Find old pattern imports:
```bash
grep -r "from llm_sim.agents.llm_agent import" .
grep -r "from llm_sim.engines.llm_engine import" .
grep -r "from llm_sim.validators.llm_validator import" .
```

#### Find old implementation imports:
```bash
grep -r "from llm_sim.agents.nation import" .
grep -r "from llm_sim.engines.economic import" .
grep -r "from llm_sim.validators.always_valid import" .
```

### Regex Replacements (Be Careful!)

For find-and-replace in your editor:

**Base classes:**
- Find: `from llm_sim\.(agents|engines|validators)\.base import (Base\w+)`
- Replace: `from llm_sim.infrastructure.base.$1 import $2`

**Patterns:**
- Find: `from llm_sim\.(agents|engines|validators)\.llm_\1 import (LLM\w+)`
- Replace: `from llm_sim.infrastructure.patterns.llm_$1 import $2`

**Implementations:**
- Find: `from llm_sim\.(agents|engines|validators)\.(\w+) import`
- Replace: `from llm_sim.implementations.$1.$2 import`

## Troubleshooting

### Import Error: Module Not Found

**Error:**
```python
ModuleNotFoundError: No module named 'llm_sim.agents.nation'
```

**Solution:** Update import to new path:
```python
from llm_sim.implementations.agents.nation import NationAgent
```

### Discovery Error: Class Not Found

**Error:**
```python
AttributeError: Module does not contain class 'MyAgent'
```

**Solution:** Ensure your class name matches the filename:
- File: `my_agent.py` → Class: `MyAgent`
- File: `economic_engine.py` → Class: `EconomicEngine`

### Discovery Error: Wrong Inheritance

**Error:**
```python
TypeError: MyAgent does not inherit from BaseAgent
```

**Solution:** Ensure your class inherits from the correct base:
```python
from llm_sim.infrastructure.base.agent import BaseAgent

class MyAgent(BaseAgent):  # ← Must inherit from BaseAgent
    pass
```

### Tests Failing After Migration

**Symptoms:** Tests that worked before now fail with import errors

**Solution:** Update test imports:
```python
# tests/test_my_agent.py
# Before:
from llm_sim.agents.nation import NationAgent

# After:
from llm_sim.implementations.agents.nation import NationAgent
```

## Backward Compatibility

### What Still Works

✅ **YAML configs**: No changes needed, discovery handles loading
✅ **Orchestrator API**: `SimulationOrchestrator.from_yaml()` unchanged
✅ **Action/State models**: No changes to data structures
✅ **LLM client**: Same configuration format

### What Changed (Breaking)

❌ **Direct imports**: Old import paths removed, must update
❌ **Manual instantiation**: Need to use discovery or new import paths
❌ **`agents/`, `engines/`, `validators/` modules**: Now empty (deprecated)

## Need Help?

- See [Creating Implementations](patterns/creating_implementations.md) for how to use the new structure
- See [Base Classes Reference](patterns/base_classes.md) for interface documentation
- See [LLM Pattern Documentation](patterns/llm_pattern.md) for LLM integration

## New Features Available After Migration

### Partial Observability (v0.2.0+)

After migrating to the new structure, you can use the partial observability feature:

```yaml
observability:
  enabled: true
  variable_visibility:
    external: [economic_strength, position]
    internal: [secret_reserves, strategy]
  matrix:
    - [Agent1, Agent2, external, 0.2]
    - [Agent1, Agent3, unaware, null]
  default:
    level: external
    noise: 0.1
```

**Benefits:**
- Realistic information asymmetry between agents
- Configurable noise levels for observations
- Three observability levels: unaware, external, insider
- Backward compatible (disabled by default)

See [Simulation Guide](SIMULATION_GUIDE.md#partial-observability) for complete documentation.

### Dynamic Agent Management (v0.3.0+)

**BREAKING CHANGE:** Agent storage has changed from `List[Agent]` to `Dict[str, Agent]`.

#### What Changed

**Before (v0.2.x):**
```python
# SimulationState.agents was a list
state.agents: List[Agent]

# Accessing agents by index
agent = state.agents[0]

# Iterating over agents
for agent in state.agents:
    process(agent)
```

**After (v0.3.0+):**
```python
# SimulationState.agents is now a dict keyed by agent name
state.agents: Dict[str, Agent]

# Accessing agents by name
agent = state.agents["Agent1"]

# Iterating over agents
for agent in state.agents.values():
    process(agent)

# Getting agent names
for name in state.agents.keys():
    print(name)
```

#### Migration Steps

**1. Update Agent Iteration:**

```python
# Old pattern
for agent in state.agents:
    print(agent.name)

# New pattern
for agent in state.agents.values():
    print(agent.name)
```

**2. Update Agent Access:**

```python
# Old pattern - by index
first_agent = state.agents[0]

# New pattern - by name
first_agent = state.agents["Agent1"]
# Or get first agent from dict
first_agent = next(iter(state.agents.values()))
```

**3. Update Agent Count:**

```python
# Old pattern
num_agents = len(state.agents)

# New pattern (same)
num_agents = len(state.agents)
```

**4. Update Agent Lookups:**

```python
# Old pattern - find by name
agent = next(a for a in state.agents if a.name == "Agent1")

# New pattern - direct lookup
agent = state.agents.get("Agent1")  # Returns None if not found
# Or
agent = state.agents["Agent1"]  # Raises KeyError if not found
```

#### Find and Replace

Search for these patterns in your codebase:

```bash
# Find agent iteration patterns
grep -r "for .* in .*\.agents:" .
grep -r "for .* in state\.agents" .

# Find agent index access
grep -r "\.agents\[" .

# Find list operations
grep -r "\.agents\.append" .
grep -r "\.agents\.remove" .
```

**Common replacements:**

| Old Code | New Code |
|----------|----------|
| `for agent in state.agents:` | `for agent in state.agents.values():` |
| `state.agents[i]` | `state.agents[name]` |
| `state.agents.append(agent)` | `state.agents[agent.name] = agent` |
| `state.agents.remove(agent)` | `del state.agents[agent.name]` |
| `[a for a in state.agents if ...]` | `[a for a in state.agents.values() if ...]` |

#### Benefits of Dict-Based Storage

- **O(1) agent lookups** by name (was O(n) list search)
- **Name-based access** more intuitive than index
- **Supports dynamic agents** - add/remove by name
- **No index invalidation** when agents removed
- **Built-in uniqueness** enforcement by name

#### Backward Compatibility

**Not backward compatible** - you must update your code. No legacy support provided for list-based access.

#### Dynamic Agent Management Features

With dict-based storage, you can now:

```python
# Add agents at runtime
orchestrator.add_agent("NewAgent", initial_state={"wealth": 100})

# Remove agents by name
orchestrator.remove_agent("OldAgent")

# Pause/resume agents
orchestrator.pause_agent("Agent1", auto_resume_turns=5)
orchestrator.resume_agent("Agent1")

# Agent-initiated lifecycle changes
from llm_sim.models.lifecycle import LifecycleAction, LifecycleOperation

# In agent.decide_action():
return LifecycleAction(
    operation=LifecycleOperation.ADD_AGENT,
    initiating_agent=self.name,
    target_agent_name="Offspring",
    initial_state={"parent": self.name}
)
```

See [Dynamic Agent Management](SIMULATION_GUIDE.md#dynamic-agent-management) for complete documentation.

---

## Summary

| What | Old | New |
|------|-----|-----|
| **Base classes** | `llm_sim.agents.base` | `llm_sim.infrastructure.base.agent` |
| **LLM patterns** | `llm_sim.agents.llm_agent` | `llm_sim.infrastructure.patterns.llm_agent` |
| **Implementations** | `llm_sim.agents.nation` | `llm_sim.implementations.agents.nation` |
| **YAML configs** | ✅ No change | ✅ No change |
| **Discovery loading** | ❌ Not available | ✅ Automatic |
| **Observability** | ❌ Not available | ✅ Optional feature |
| **Agent storage** | `List[Agent]` | `Dict[str, Agent]` (v0.3.0+) |
| **Dynamic agents** | ❌ Not available | ✅ Add/remove/pause at runtime (v0.3.0+) |

**Migration effort**:
- v0.1.x → v0.2.0: Low - mostly import path updates, YAML configs unchanged
- v0.2.x → v0.3.0: Medium - agent storage breaking change, update iteration patterns
