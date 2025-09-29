# Implementation Plan for Remaining 41 Test Failures

## Overview
We have 41 failing tests across 5 main categories. Most failures are due to missing method implementations or interface mismatches rather than bugs.

## Failure Analysis

### 1. Ollama Integration Issues (8 tests)
**Root Cause:** Tests expect actual Ollama connection, but we're using mocks
**Files:** `tests/integration/test_ollama_smoke.py`
**Errors:**
- `LLMConnectionError: Not connected to Ollama`
- Tests trying to connect to real Ollama service

### 2. Real LLM Integration Issues (8 tests)
**Root Cause:** Missing methods and serialization issues
**Files:** `tests/integration/test_real_llm_integration.py`
**Errors:**
- `TypeError: Object of type GlobalEvent is not JSON serializable`
- `AttributeError: 'OllamaInterface' object has no attribute 'generate'`
- `TypeError: Validator.__init__() got an unexpected keyword argument 'llm_client'`
- Abstract class instantiation issues

### 3. E2E Workflow Issues (9 tests)
**Root Cause:** Missing coordinator methods
**Files:** `tests/e2e/test_complete_workflow.py`
**Errors:**
- `AttributeError: 'SimulationCoordinator' object has no attribute 'run_single_turn'`
- Missing workflow orchestration methods

### 4. Agent State Interaction Issues (6 tests)
**Root Cause:** Missing memory and state persistence features
**Files:** `tests/integration/agents/test_agent_state_interaction.py`
**Errors:**
- Memory persistence not implemented
- State transition with outcomes not working
- Garbage collection not implemented

### 5. Real E2E Simulation Issues (10 tests)
**Root Cause:** Component initialization and integration issues
**Files:** `tests/integration/test_real_e2e_simulation.py`
**Errors:**
- Registry initialization problems
- Config structure mismatches
- Missing LLM client handling

## Implementation Priority Order

### Phase 1: Fix Critical Infrastructure (High Priority)
These fixes will unblock the most tests.

#### 1.1 Fix OllamaInterface Methods (Impacts: 16 tests)
**File:** `src/llm_sim/llm/ollama_client.py`
**Tasks:**
- [ ] Add `generate()` method that wraps `generate_text()`
- [ ] Fix JSON serialization for GlobalEvent objects
- [ ] Ensure proper mock interface compatibility
**Estimated Time:** 2 hours

#### 1.2 Add SimulationCoordinator Methods (Impacts: 9 tests)
**File:** `src/llm_sim/coordinator/simulation.py`
**Tasks:**
- [ ] Implement `run_single_turn()` method
- [ ] Add turn processing logic
- [ ] Implement checkpoint saving/loading
- [ ] Add parallel agent processing
**Estimated Time:** 3 hours

### Phase 2: Fix Integration Layer (Medium Priority)

#### 2.1 Fix Validator LLM Integration (Impacts: 3 tests)
**File:** `src/llm_sim/validation/validator.py`
**Tasks:**
- [ ] Add optional `llm_client` parameter to Validator.__init__
- [ ] Implement LLM-based validation reasoning
**Estimated Time:** 1 hour

#### 2.2 Fix LLMDrivenAgent Abstract Methods (Impacts: 2 tests)
**File:** `src/llm_sim/agents/llm_driven.py`
**Tasks:**
- [ ] Ensure all abstract methods have default implementations
- [ ] Fix instantiation issues
**Estimated Time:** 1 hour

### Phase 3: Implement Missing Features (Lower Priority)

#### 3.1 Agent Memory Persistence (Impacts: 6 tests)
**Files:** `src/llm_sim/agents/memory/`
**Tasks:**
- [ ] Implement memory persistence across turns
- [ ] Add memory garbage collection
- [ ] Implement state snapshots and restore
- [ ] Add audit trail generation
**Estimated Time:** 4 hours

#### 3.2 Fix Component Integration (Impacts: 10 tests)
**Files:** Various integration points
**Tasks:**
- [ ] Fix registry initialization flow
- [ ] Handle missing LLM clients gracefully
- [ ] Fix config structure validation
- [ ] Improve error messages
**Estimated Time:** 3 hours

## Implementation Steps

### Step 1: Quick Wins (1-2 hours)
1. Add `generate()` method to OllamaInterface
2. Fix GlobalEvent JSON serialization
3. Add `llm_client` parameter to Validator

### Step 2: Core Methods (3-4 hours)
1. Implement `run_single_turn()` in SimulationCoordinator
2. Add checkpoint saving/loading
3. Implement parallel agent processing

### Step 3: Integration Fixes (2-3 hours)
1. Fix LLMDrivenAgent abstract class
2. Update mock interfaces for compatibility
3. Fix component initialization flows

### Step 4: Advanced Features (4-5 hours)
1. Implement agent memory persistence
2. Add memory garbage collection
3. Implement audit trails
4. Fix remaining integration issues

## Expected Outcomes

After implementing this plan:
- **Quick Wins:** Will fix ~20 tests (Ollama and LLM integration)
- **Core Methods:** Will fix ~9 tests (E2E workflows)
- **Integration Fixes:** Will fix ~6 tests (agent interactions)
- **Advanced Features:** Will fix remaining ~6 tests

**Total Time Estimate:** 12-15 hours
**Expected Result:** All 41 remaining tests passing

## Testing Strategy

After each implementation step:
1. Run specific test suite for that component
2. Verify no regression in already-passing tests
3. Commit changes with clear messages
4. Update documentation as needed

## Success Metrics

- All 385 tests passing (excluding skipped/deselected)
- No regression in existing functionality
- Clear documentation for new features
- Maintainable and extensible code