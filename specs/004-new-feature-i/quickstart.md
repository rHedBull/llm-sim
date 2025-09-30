# Quickstart: LLM-Based Reasoning Integration

**Feature**: 004-new-feature-i
**Purpose**: Validate that LLM-based reasoning is working end-to-end in the simulation
**Estimated Time**: 10 minutes

---

## Prerequisites

1. **Ollama installed and running**:
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/version
   # Expected: {"version":"..."}
   ```

2. **Gemma:3 model pulled**:
   ```bash
   ollama pull gemma:3
   # Wait for download to complete
   ```

3. **Dependencies installed**:
   ```bash
   uv pip install -e ".[dev]"
   # Should install ollama, httpx, tenacity, pytest-asyncio
   ```

4. **Environment variables** (optional):
   ```bash
   export OLLAMA_HOST="http://localhost:11434"  # Default
   export LOG_LEVEL="DEBUG"  # To see reasoning chains
   ```

---

## Quick Validation Steps

### Step 1: Verify LLM Client Works

```bash
# Run unit test for LLM client basic functionality
pytest tests/unit/test_llm_client.py::test_llm_client_successful_call -v

# Expected output:
# ✓ test_llm_client_successful_call PASSED
```

**Success Criteria**:
- Test passes without errors
- If fails: Check Ollama is running and gemma:3 is available

---

### Step 2: Verify Agent LLM Integration

```bash
# Run contract test for Agent LLM reasoning
pytest tests/contract/test_agent_llm_integration.py::test_agent_generates_policy -v

# Expected output:
# ✓ test_agent_generates_policy PASSED
```

**Success Criteria**:
- Agent successfully calls LLM
- PolicyDecision contains action string and reasoning
- Action object has policy_decision field populated

**Expected behavior**:
- Agent receives state with economic indicators
- LLM generates a specific policy action (e.g., "Lower interest rates by 0.5%")
- Action includes step-by-step reasoning
- Confidence score is between 0.0 and 1.0

---

### Step 3: Verify Validator LLM Integration

```bash
# Run contract test for Validator LLM reasoning
pytest tests/contract/test_validator_llm_integration.py::test_validator_accepts_economic_action -v

# Expected output:
# ✓ test_validator_accepts_economic_action PASSED
```

**Success Criteria**:
- Validator successfully calls LLM
- Economic action is marked as validated
- Validation result contains reasoning
- Non-economic action would be rejected (separate test)

**Expected behavior**:
- Validator receives action: "Lower interest rates by 0.5%"
- LLM determines it's within economic domain
- ValidationResult has is_valid=True
- Reasoning explains why it's economic policy

---

### Step 4: Verify Engine LLM Integration

```bash
# Run contract test for Engine LLM reasoning
pytest tests/contract/test_engine_llm_integration.py::test_engine_computes_state_update -v

# Expected output:
# ✓ test_engine_computes_state_update PASSED
```

**Success Criteria**:
- Engine successfully calls LLM
- StateUpdateDecision contains new interest rate
- New rate is different from original rate
- Reasoning explains the calculation

**Expected behavior**:
- Engine receives validated action
- LLM computes new interest rate (e.g., 2.5% -> 2.0%)
- StateUpdateDecision includes step-by-step reasoning
- New SimulationState reflects the change

---

### Step 5: End-to-End Reasoning Flow

```bash
# Run integration test for full simulation turn with LLM
pytest tests/integration/test_llm_reasoning_flow.py::test_full_turn_with_llm -v -s

# Expected output:
# ✓ test_full_turn_with_llm PASSED
# (With -s flag, you'll see DEBUG logs with reasoning chains)
```

**Success Criteria**:
- Full turn completes: Agent → Validator → Engine
- All three components use LLM reasoning
- New state includes all reasoning chains
- Simulation progresses to turn 2

**Expected behavior**:
1. Agent observes state (GDP=2.5%, Inflation=3.0%, Unemployment=5.0%, Rate=2.5%)
2. Agent LLM generates policy: "Lower interest rates by 0.5%"
3. Validator LLM validates: is_valid=True (economic domain)
4. Engine LLM computes: new_interest_rate=2.0%
5. State updated with reasoning chains attached

**Expected DEBUG logs** (with LOG_LEVEL=DEBUG):
```
llm_reasoning_chain component=agent agent_id=TestNation reasoning="High unemployment indicates weak demand..."
llm_reasoning_chain component=validator reasoning="Action targets interest rates, core economic policy..."
llm_reasoning_chain component=engine reasoning="Lowering rates by 0.5% from 2.5% results in 2.0%..."
```

---

### Step 6: Error Handling Validation

```bash
# Test LLM failure and retry behavior
pytest tests/integration/test_llm_error_handling.py::test_llm_retry_and_abort -v

# Expected output:
# ✓ test_llm_retry_and_abort PASSED
```

**Success Criteria**:
- LLM failure triggers exactly one retry
- After second failure, LLMFailureException is raised
- Prominent ERROR log message appears
- Simulation step aborts (does not proceed to next turn)

**Expected behavior**:
1. First LLM call fails (timeout)
2. Retry occurs after 1-5 second backoff
3. Second LLM call fails
4. ERROR log: "LLM_FAILURE: Component=agent Agent=TestNation Error=timeout"
5. Exception propagates to orchestrator
6. Simulation turn aborts

---

### Step 7: Validation Rejection Flow

```bash
# Test validator rejection and engine skip behavior
pytest tests/integration/test_validation_rejection.py::test_rejected_action_skipped -v

# Expected output:
# ✓ test_rejected_action_skipped PASSED
```

**Success Criteria**:
- Validator marks action as validated=False
- Engine logs INFO message about skipping agent
- State is unchanged (except turn increment)
- Simulation continues (does not abort)

**Expected behavior**:
1. Agent proposes: "Deploy military forces to border"
2. Validator LLM determines: is_valid=False (not economic domain)
3. Action marked as validated=False
4. Engine skips action
5. INFO log: "SKIPPED Agent [TestNation] due to unvalidated Action"
6. Interest rate unchanged in new state

---

## Full Simulation Test

Run a complete 3-turn simulation with LLM reasoning:

```bash
# Run full simulation with LLM (requires Ollama running)
pytest tests/e2e/test_llm_simulation.py::test_multi_turn_llm_simulation -v -s

# Expected output:
# ✓ test_multi_turn_llm_simulation PASSED
# Duration: ~30-60 seconds (3 turns × 2 agents × 3 LLM calls per agent)
```

**Success Criteria**:
- Simulation completes 3 turns
- Each turn has reasoning chains from all agents
- Interest rate changes over time based on LLM decisions
- Final state includes complete reasoning history
- No LLM failures or timeouts

**Expected behavior**:
- Turn 1: Agent A proposes policy, validated, applied
- Turn 1: Agent B proposes policy, validated, applied
- Turn 2: Both agents observe updated state, propose new policies
- Turn 3: Simulation continues based on previous outcomes
- Final output: 3 states in history, each with reasoning chains

---

## Debugging Tips

### If tests fail with "Connection refused":
```bash
# Start Ollama if not running
ollama serve &

# Verify it's accessible
curl http://localhost:11434/api/version
```

### If tests timeout:
```bash
# Check Ollama resource usage
ollama ps

# If model not loaded, pull it
ollama pull gemma:3

# Test model directly
ollama run gemma:3 "What is 2+2?"
```

### If tests fail with "Model not found":
```bash
# Verify model is available
ollama list | grep gemma

# Pull model if missing
ollama pull gemma:3
```

### To see full LLM prompts and responses:
```bash
# Run tests with DEBUG logging
LOG_LEVEL=DEBUG pytest tests/integration/test_llm_reasoning_flow.py -v -s

# Or check structured logs
tail -f logs/simulation_debug.log | grep llm_reasoning_chain
```

### If LLM returns invalid JSON:
- Check prompt templates in `llm_sim/prompts/`
- Verify Pydantic schemas match expected LLM output
- Test LLM directly with Ollama CLI to debug prompt
- Review fallback regex extraction in LLMClient

---

## Manual Verification (Optional)

Run a simulation with real LLM and inspect output:

```bash
# Create test config with LLM enabled
cat > config_llm_test.yaml << EOF
simulation:
  name: "LLM Reasoning Test"
  max_turns: 3

engine:
  type: economic

validator:
  type: llm_validator
  domain: economic
  permissive: true

llm:
  model: "gemma:3"
  host: "http://localhost:11434"
  timeout: 60.0
  max_retries: 1
  temperature: 0.7
  stream: true

agents:
  - name: "TestNation"
    type: nation
    initial_strength: 100.0

logging:
  level: DEBUG
  format: json
EOF

# Run simulation
python -m llm_sim config_llm_test.yaml

# Inspect output for reasoning chains
# Look for DEBUG logs with component=agent/validator/engine
```

**What to look for**:
1. Each turn shows agent policy decisions with reasoning
2. Validator logs show domain validation reasoning
3. Engine logs show interest rate calculation reasoning
4. Final state includes complete reasoning history
5. Interest rate changes over turns based on LLM decisions

---

## Success Checklist

- [ ] All unit tests pass (LLM client retry logic)
- [ ] All contract tests pass (Agent/Validator/Engine interfaces)
- [ ] All integration tests pass (full reasoning flow)
- [ ] Error handling tests pass (retry and abort)
- [ ] Validation rejection tests pass (skip logic)
- [ ] End-to-end simulation completes successfully
- [ ] DEBUG logs show reasoning chains for all components
- [ ] Interest rate changes based on LLM decisions
- [ ] No LLM failures or timeouts during test run

---

## Next Steps

After quickstart validation:

1. **Run full test suite**: `pytest tests/ -v --cov=src/llm_sim`
2. **Performance benchmark**: `pytest tests/performance/test_llm_latency.py`
3. **Review reasoning quality**: Manually inspect DEBUG logs for coherence
4. **Tune prompts**: Adjust prompt templates if reasoning is unclear
5. **Production config**: Update LLM timeout/retry settings for production

---

## Troubleshooting Common Issues

### Issue: "LLM returns non-JSON responses"
**Solution**:
- Check prompt includes "Return response as JSON"
- Verify `format=response_model.model_json_schema()` is used
- Enable fallback regex extraction in LLMClient

### Issue: "Validator rejects all actions"
**Solution**:
- Verify domain is set correctly in ValidatorConfig
- Check `permissive=True` is enabled (per spec FR-005a)
- Review validator prompt template for clarity
- Test validator prompt manually with Ollama CLI

### Issue: "Engine calculates unrealistic interest rates"
**Solution**:
- Add bounds checking in StateUpdateDecision validation
- Improve engine prompt with economic constraints
- Include current rate in prompt for context
- Add validation rules (e.g., -2% to +2% change max)

### Issue: "Tests are too slow"
**Solution**:
- Use mocked LLM for unit/contract tests (don't call real Ollama)
- Reserve integration tests with real LLM for critical paths
- Enable streaming to reduce perceived latency
- Increase Ollama server resources (RAM, GPU)

---

## Time Estimates

- **Unit tests** (mocked LLM): 5-10 seconds total
- **Contract tests** (mocked LLM): 10-20 seconds total
- **Integration tests** (real LLM): 30-60 seconds per test
- **End-to-end simulation** (3 turns, 2 agents): 60-120 seconds
- **Full test suite**: 3-5 minutes (with parallel execution)

---

**Version**: 1.0.0
**Status**: Draft
**Last Updated**: 2025-09-30