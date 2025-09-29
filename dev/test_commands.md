# Test Commands Reference

## Quick Test Commands

### Run all tests with summary
```bash
uv run pytest --tb=no -q
```

### Check specific test categories

#### Ollama Integration (8 tests)
```bash
uv run pytest tests/integration/test_ollama_smoke.py -v
```

#### Real LLM Integration (8 tests)
```bash
uv run pytest tests/integration/test_real_llm_integration.py -v
```

#### E2E Workflows (9 tests)
```bash
uv run pytest tests/e2e/test_complete_workflow.py -v
```

#### Agent State Interaction (6 tests)
```bash
uv run pytest tests/integration/agents/test_agent_state_interaction.py -v
```

#### Real E2E Simulation (10 tests)
```bash
uv run pytest tests/integration/test_real_e2e_simulation.py -v
```

## Progress Tracking

### Get failure summary
```bash
uv run pytest --tb=no -q 2>/dev/null | grep "failed" | tail -1
```

### Get detailed failure list
```bash
uv run pytest --tb=no -q 2>/dev/null | grep "FAILED"
```

### Count failures by category
```bash
uv run pytest --tb=no -q 2>/dev/null | grep "FAILED" | cut -d':' -f1-3 | cut -d'/' -f2- | sort | uniq -c | sort -nr
```

## After Each Fix

### Test specific fix
```bash
# Example for testing OllamaInterface changes
uv run pytest tests/integration/test_ollama_smoke.py::TestOllamaSmoke::test_ollama_connection -xvs
```

### Verify no regression
```bash
# Run core component tests to ensure nothing broke
uv run pytest tests/integration/test_validator_integration.py tests/integration/test_agent_registry_integration.py tests/integration/test_game_engine_integration.py tests/integration/test_state_manager_integration.py -v
```

## Debugging

### Run with detailed output
```bash
uv run pytest [test_file] -xvs --tb=short
```

### Run with pdb on failure
```bash
uv run pytest [test_file] -x --pdb
```