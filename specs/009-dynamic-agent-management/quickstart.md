# Quickstart: Dynamic Agent Management

**Feature**: 009-dynamic-agent-management
**Purpose**: Validate that dynamic agent lifecycle operations work end-to-end
**Estimated Time**: 5 minutes

## Prerequisites

- Feature implementation complete
- Tests passing (`uv run pytest tests/`)
- Example simulation config available

## Quick Validation Steps

### 1. External Add/Remove Operations

**Objective**: Verify orchestrator can add and remove agents at runtime

```bash
# Create test script
cat > test_dynamic_agents.py << 'EOF'
from llm_sim.orchestrator import SimulationOrchestrator
from llm_sim.infrastructure.base.agent import Agent
from pathlib import Path

# Load simulation with initial agents
orchestrator = SimulationOrchestrator.from_yaml("configs/example.yaml")
print(f"Initial agents: {list(orchestrator.state.agents.keys())}")

# Add a new agent
new_agent = orchestrator.discovery.load_agent("implementations/agents/simple_agent.py")
initial_state = {"resource": 100}
resolved_name = orchestrator.add_agent("researcher", new_agent, initial_state)
print(f"Added agent: {resolved_name}")
print(f"Agents after add: {list(orchestrator.state.agents.keys())}")

# Add another with same name (tests collision resolution)
resolved_name_2 = orchestrator.add_agent("researcher", new_agent, initial_state)
print(f"Added agent with collision: {resolved_name_2}")  # Should be "researcher_1"

# Remove an agent
success = orchestrator.remove_agent("agent1")
print(f"Removed agent1: {success}")
print(f"Agents after remove: {list(orchestrator.state.agents.keys())}")
EOF

# Run test
uv run python test_dynamic_agents.py
```

**Expected Output**:
```
Initial agents: ['agent1', 'agent2', 'agent3']
Added agent: researcher
Agents after add: ['agent1', 'agent2', 'agent3', 'researcher']
Added agent with collision: researcher_1
Removed agent1: True
Agents after remove: ['agent2', 'agent3', 'researcher', 'researcher_1']
```

---

### 2. Pause/Resume Operations

**Objective**: Verify pause and resume functionality

```bash
cat > test_pause_resume.py << 'EOF'
from llm_sim.orchestrator import SimulationOrchestrator

orchestrator = SimulationOrchestrator.from_yaml("configs/example.yaml")
print(f"Initial agents: {list(orchestrator.state.agents.keys())}")
print(f"Paused agents: {orchestrator.state.paused_agents}")

# Pause an agent indefinitely
success = orchestrator.pause_agent("agent1")
print(f"Paused agent1: {success}")
print(f"Paused agents: {orchestrator.state.paused_agents}")

# Pause with auto-resume
success = orchestrator.pause_agent("agent2", auto_resume_turns=2)
print(f"Paused agent2 with auto-resume=2: {success}")
print(f"Auto-resume config: {orchestrator.state.auto_resume}")

# Run simulation for 3 turns to trigger auto-resume
for turn in range(1, 4):
    orchestrator.run_turn()
    print(f"Turn {turn} - Paused: {orchestrator.state.paused_agents}")

# Manual resume
success = orchestrator.resume_agent("agent1")
print(f"Resumed agent1: {success}")
print(f"Final paused agents: {orchestrator.state.paused_agents}")
EOF

uv run python test_pause_resume.py
```

**Expected Output**:
```
Initial agents: ['agent1', 'agent2', 'agent3']
Paused agents: set()
Paused agent1: True
Paused agents: {'agent1'}
Paused agent2 with auto-resume=2: True
Auto-resume config: {'agent2': 2}
Turn 1 - Paused: {'agent1', 'agent2'}
Turn 2 - Paused: {'agent1'}          # agent2 auto-resumed
Turn 3 - Paused: {'agent1'}
Resumed agent1: True
Final paused agents: set()
```

---

### 3. Agent-Initiated Lifecycle Actions

**Objective**: Verify agents can request lifecycle changes

**Create test agent** (`test_spawn_agent.py`):
```python
from llm_sim.infrastructure.base.agent import Agent
from llm_sim.models.action import Action
from llm_sim.models.lifecycle import LifecycleAction, LifecycleOperation
from typing import Any, Dict, List

class SpawningAgent(Agent):
    def decide_actions(
        self,
        observation: Dict[str, Any],
        agent_state: Dict[str, Any]
    ) -> List[Action]:
        # On turn 3, spawn a new agent
        if observation.get("turn") == 3:
            return [
                LifecycleAction(
                    operation=LifecycleOperation.ADD_AGENT,
                    initiating_agent=self.name,
                    target_agent_name="offspring",
                    initial_state={"parent": self.name}
                )
            ]
        return []
```

**Run simulation**:
```bash
cat > test_agent_spawn.py << 'EOF'
from llm_sim.orchestrator import SimulationOrchestrator
from test_spawn_agent import SpawningAgent

# Create orchestrator with spawning agent
orchestrator = SimulationOrchestrator.from_yaml("configs/minimal.yaml")
orchestrator.add_agent("spawner", SpawningAgent("spawner"), {})

print(f"Turn 1 - Agents: {list(orchestrator.state.agents.keys())}")
orchestrator.run_turn()

print(f"Turn 2 - Agents: {list(orchestrator.state.agents.keys())}")
orchestrator.run_turn()

print(f"Turn 3 - Agents: {list(orchestrator.state.agents.keys())}")
orchestrator.run_turn()  # spawner requests offspring

print(f"Turn 4 - Agents: {list(orchestrator.state.agents.keys())}")  # offspring should exist
EOF

uv run python test_agent_spawn.py
```

**Expected Output**:
```
Turn 1 - Agents: ['spawner']
Turn 2 - Agents: ['spawner']
Turn 3 - Agents: ['spawner']
Turn 4 - Agents: ['spawner', 'offspring']  # offspring added after turn 3
```

---

### 4. Constraint Validation

**Objective**: Verify max agent limit and validation logging

```bash
cat > test_constraints.py << 'EOF'
from llm_sim.orchestrator import SimulationOrchestrator
from llm_sim.infrastructure.base.agent import Agent

orchestrator = SimulationOrchestrator.from_yaml("configs/minimal.yaml")

# Add agents up to limit
dummy_agent = orchestrator.discovery.load_agent("implementations/agents/simple_agent.py")
for i in range(25):
    name = orchestrator.add_agent(f"agent{i}", dummy_agent, {})
    print(f"Added: {name}, Total: {len(orchestrator.state.agents)}")

# Try to add 26th agent (should fail validation)
print("\n--- Attempting to add 26th agent ---")
name = orchestrator.add_agent("overflow", dummy_agent, {})
print(f"Result: {name}, Total: {len(orchestrator.state.agents)}")
# Check logs for: "lifecycle_validation_failed" warning
EOF

uv run python test_constraints.py 2>&1 | grep -A 2 "overflow"
```

**Expected Output**:
```
--- Attempting to add 26th agent ---
[WARNING] lifecycle_validation_failed operation=add_agent agent_name=overflow reason="Maximum agent count (25) reached"
Result: overflow, Total: 25  # Agent NOT added, count unchanged
```

---

### 5. Checkpoint Persistence

**Objective**: Verify dict-based agent storage persists correctly

```bash
cat > test_checkpoint.py << 'EOF'
from llm_sim.orchestrator import SimulationOrchestrator
import json

orchestrator = SimulationOrchestrator.from_yaml("configs/example.yaml")

# Modify agent population
orchestrator.pause_agent("agent1", auto_resume_turns=5)
new_agent = orchestrator.discovery.load_agent("implementations/agents/simple_agent.py")
orchestrator.add_agent("dynamic", new_agent, {"value": 42})

# Run turn to trigger checkpoint
orchestrator.run_turn()

# Load checkpoint file
checkpoint_path = orchestrator.checkpoint_manager.checkpoint_dir / "turn_001.json"
with open(checkpoint_path) as f:
    checkpoint = json.load(f)

print("Agents in checkpoint:", list(checkpoint["state"]["agents"].keys()))
print("Paused agents:", checkpoint["state"]["paused_agents"])
print("Auto-resume:", checkpoint["state"]["auto_resume"])
EOF

uv run python test_checkpoint.py
```

**Expected Output**:
```
Agents in checkpoint: ['agent1', 'agent2', 'agent3', 'dynamic']
Paused agents: ['agent1']
Auto-resume: {'agent1': 5}
```

---

## Acceptance Criteria Validation

| Scenario | Test Script | Status |
|----------|-------------|--------|
| Add agent at runtime | `test_dynamic_agents.py` | ✅ Validated |
| Remove agent at runtime | `test_dynamic_agents.py` | ✅ Validated |
| Pause agent | `test_pause_resume.py` | ✅ Validated |
| Resume agent | `test_pause_resume.py` | ✅ Validated |
| Auto-resume after N turns | `test_pause_resume.py` | ✅ Validated |
| Agent-initiated spawn | `test_agent_spawn.py` | ✅ Validated |
| Duplicate name collision | `test_dynamic_agents.py` | ✅ Validated |
| Max agent limit (25) | `test_constraints.py` | ✅ Validated |
| Dict-based checkpoint | `test_checkpoint.py` | ✅ Validated |

## Cleanup

```bash
rm test_*.py
```

## Troubleshooting

### Agents not added
- Check logs for `lifecycle_validation_failed` warnings
- Verify agent count < 25
- Ensure agent instance is valid

### Pause not working
- Verify agent exists in `state.agents`
- Check that agent not already paused

### Auto-resume not triggering
- Verify `auto_resume_turns` > 0
- Ensure simulation running turns (not paused)
- Check `state.auto_resume` dict contents

### Checkpoint errors
- Verify dict structure: `{"agents": {...}, "paused_agents": [...], "auto_resume": {...}}`
- Check that all `paused_agents` names exist in `agents` dict
- Ensure `auto_resume` keys subset of `paused_agents`

## Next Steps

After successful quickstart validation:

1. Run full test suite: `uv run pytest tests/ -v`
2. Check test coverage: `uv run pytest --cov=src/llm_sim --cov-report=term-missing`
3. Review logs for any unexpected warnings
4. Update project README with lifecycle management examples
5. Create example simulation config demonstrating dynamic agents

## Performance Validation (Optional)

```bash
cat > benchmark_lifecycle.py << 'EOF'
import time
from llm_sim.orchestrator import SimulationOrchestrator

orchestrator = SimulationOrchestrator.from_yaml("configs/example.yaml")
dummy_agent = orchestrator.discovery.load_agent("implementations/agents/simple_agent.py")

# Benchmark add operations
start = time.time()
for i in range(22):  # Add up to 25 total (assuming 3 initial)
    orchestrator.add_agent(f"bench{i}", dummy_agent, {})
elapsed = time.time() - start
print(f"Added 22 agents in {elapsed*1000:.2f}ms ({elapsed/22*1000:.2f}ms per agent)")

# Benchmark pause/resume
start = time.time()
for name in list(orchestrator.state.agents.keys())[:10]:
    orchestrator.pause_agent(name)
elapsed = time.time() - start
print(f"Paused 10 agents in {elapsed*1000:.2f}ms ({elapsed/10*1000:.2f}ms per agent)")
EOF

uv run python benchmark_lifecycle.py
rm benchmark_lifecycle.py
```

**Expected**: All operations < 1ms per agent for 25 agents.
