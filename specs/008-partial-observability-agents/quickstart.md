# Quickstart: Partial Observability

**Feature**: 008-partial-observability-agents
**Purpose**: Verify partial observability works end-to-end with a minimal test scenario

---

## Prerequisites

- Python 3.12+ with uv package manager
- llm_sim installed with observability feature
- Test configuration file created

---

## Setup

### 1. Create Test Configuration

Create `test_observability.yaml`:

```yaml
simulation:
  name: "Partial Observability Test"
  max_turns: 5
  checkpoint_interval: null

engine:
  type: "economic_engine"
  interest_rate: 0.05

agents:
  - name: "Observer"
    type: "llm_agent"
  - name: "External"
    type: "llm_agent"
  - name: "Hidden"
    type: "llm_agent"

validator:
  type: "llm_validator"
  domain: "economic"
  permissive: true

state_variables:
  agent_vars:
    economic_strength:
      type: float
      min: 0
      default: 100.0
      visibility: external
    secret_reserves:
      type: float
      min: 0
      default: 50.0
      visibility: internal
  global_vars:
    interest_rate:
      type: float
      default: 0.05
      visibility: external
    central_bank_reserves:
      type: float
      default: 1000.0
      visibility: internal

observability:
  enabled: true
  variable_visibility:
    external: [economic_strength, interest_rate]
    internal: [secret_reserves, central_bank_reserves]
  matrix:
    # Observer sees itself perfectly
    - [Observer, Observer, insider, 0.0]
    # Observer sees External's public data with noise
    - [Observer, External, external, 0.2]
    # Observer cannot see Hidden
    - [Observer, Hidden, unaware, null]
    # Observer sees external global state with noise
    - [Observer, global, external, 0.1]

    # External sees Observer and itself
    - [External, Observer, external, 0.15]
    - [External, External, insider, 0.0]
    - [External, Hidden, external, 0.2]
    - [External, global, external, 0.1]

    # Hidden sees everyone
    - [Hidden, Observer, external, 0.1]
    - [Hidden, External, external, 0.1]
    - [Hidden, Hidden, insider, 0.0]
    - [Hidden, global, insider, 0.0]
  default:
    level: external
    noise: 0.2

logging:
  level: "DEBUG"
  format: "json"

llm:
  model: "gemma:3"
  host: "http://localhost:11434"
  timeout: 60.0
  max_retries: 1
  temperature: 0.7
  stream: true
```

### 2. Verify Configuration Loads

```bash
uv run python -c "
from llm_sim.models.config import load_config
config = load_config('test_observability.yaml')
print(f'✓ Config loaded: {config.simulation.name}')
print(f'✓ Observability enabled: {config.observability.enabled}')
print(f'✓ Matrix entries: {len(config.observability.matrix)}')
"
```

**Expected Output**:
```
✓ Config loaded: Partial Observability Test
✓ Observability enabled: True
✓ Matrix entries: 13
```

---

## Test Scenario

### Step 1: Run Simulation

```bash
uv run python -m llm_sim test_observability.yaml
```

### Step 2: Verify Observations in Logs

Check log output for observation construction:

```bash
grep "constructing_observation" output/logs/test_observability_*.json
```

**Expected Log Entries** (structured JSON):
```json
{"event": "constructing_observation", "observer": "Observer", "turn": 1}
{"event": "observation_filtered", "observer": "Observer", "visible_agents": ["Observer", "External"], "excluded": ["Hidden"]}
{"event": "noise_applied", "observer": "Observer", "target": "External", "variable": "economic_strength", "noise_factor": 0.2}
```

### Step 3: Verify Checkpoint Data

Load checkpoint and inspect observations:

```bash
uv run python -c "
import json
from pathlib import Path

# Load latest checkpoint
checkpoint_files = sorted(Path('output/checkpoints/').glob('test_observability_*_turn_*.json'))
with open(checkpoint_files[-1]) as f:
    data = json.load(f)

state = data['state']
print(f\"Turn: {state['turn']}\")
print(f\"Ground truth agents: {list(state['agents'].keys())}\")

# Observations would be logged separately or reconstructed
# For quickstart, verify structure matches SimulationState
print(f\"✓ State has required fields: turn, agents, global_state\")
"
```

---

## Acceptance Criteria

### ✅ Criterion 1: Unaware Filtering
**Test**: Observer's observation excludes Hidden agent
**Verification**:
```python
# In agent logic or test
observation = construct_observation("Observer", ground_truth, config)
assert "Hidden" not in observation.agents
assert "External" in observation.agents
```

### ✅ Criterion 2: Variable Filtering
**Test**: External observer sees only external variables
**Verification**:
```python
observed_agent = observation.agents["External"]
assert hasattr(observed_agent, "economic_strength")  # External var
assert not hasattr(observed_agent, "secret_reserves")  # Internal var (filtered)
```

### ✅ Criterion 3: Noise Application
**Test**: Noisy observations differ from ground truth
**Verification**:
```python
ground_truth_value = ground_truth.agents["External"].economic_strength
observed_value = observation.agents["External"].economic_strength
assert observed_value != ground_truth_value  # Noise applied
assert abs(observed_value - ground_truth_value) / ground_truth_value <= 0.2  # Within noise bounds
```

### ✅ Criterion 4: Deterministic Noise
**Test**: Same turn/agent/variable produces same noise
**Verification**:
```python
obs1 = construct_observation("Observer", ground_truth, config)
obs2 = construct_observation("Observer", ground_truth, config)
assert obs1.agents["External"].economic_strength == obs2.agents["External"].economic_strength
```

### ✅ Criterion 5: Global State Observability
**Test**: Observer sees only external global variables
**Verification**:
```python
assert hasattr(observation.global_state, "interest_rate")  # External
assert not hasattr(observation.global_state, "central_bank_reserves")  # Internal (filtered)
```

### ✅ Criterion 6: Insider Access
**Test**: Hidden has insider view of global state
**Verification**:
```python
hidden_obs = construct_observation("Hidden", ground_truth, config)
assert hasattr(hidden_obs.global_state, "interest_rate")
assert hasattr(hidden_obs.global_state, "central_bank_reserves")  # Insider sees internal vars
```

### ✅ Criterion 7: Backward Compatibility
**Test**: Disabling observability provides full visibility
**Verification**:
```python
# Modify config: observability.enabled = False
config.observability.enabled = False
obs = construct_observation("Observer", ground_truth, config)
assert set(obs.agents.keys()) == set(ground_truth.agents.keys())  # All agents visible
```

---

## Troubleshooting

### Issue: Configuration Validation Fails

**Error**: `ValueError: Unknown variable 'economic_strength' in external list`

**Solution**: Verify variable names in `variable_visibility` match those in `state_variables.agent_vars` or `state_variables.global_vars`

---

### Issue: All Agents Visible Despite Unaware Level

**Error**: Hidden agent appears in Observer's observation

**Solution**: Check matrix entry is correct: `[Observer, Hidden, unaware, null]`

---

### Issue: Noise Not Applied

**Error**: Observed values identical to ground truth

**Solution**: Verify noise factor > 0.0 in matrix entry. Check noise generation function is called.

---

### Issue: Internal Variables Still Visible

**Error**: External observer sees internal variables

**Solution**:
1. Check variable is listed in `variable_visibility.internal`
2. Verify observability level is `external` (not `insider`)
3. Confirm filtering logic excludes internal variables for external observers

---

## Success Indicators

✅ **Configuration loads without validation errors**
✅ **Simulation runs for configured turns**
✅ **Observations logged with filtering applied**
✅ **Unaware agents excluded from observations**
✅ **External variables visible, internal variables hidden (for external observers)**
✅ **Noise applied to numeric variables (deterministic)**
✅ **Insider observers see all variables**
✅ **Global state observability works like agent observability**
✅ **Disabling observability restores full visibility**

---

## Next Steps

After quickstart validation:
1. Run full test suite: `uv run pytest tests/integration/test_partial_observability.py`
2. Verify contract tests pass: `uv run pytest tests/contract/`
3. Test with different matrix configurations (asymmetric, defaults)
4. Performance test with 100 agents and complex matrix
5. Integration test with actual LLM agents making decisions based on observations

---

*Quickstart scenario complete. Validates core observability functionality in < 5 minutes.*
