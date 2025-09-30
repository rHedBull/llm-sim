# Research: LLM-Based Reasoning Implementation

**Feature**: 004-new-feature-i
**Date**: 2025-09-30
**Status**: Complete

This document consolidates technical research findings for integrating LLM-based reasoning into Agent, Validator, and Engine components.

---

## 1. Ollama Python Client Best Practices

**Decision**: Use official `ollama` Python library with AsyncClient, enable streaming, configure 60-120s timeouts

**Rationale**:
- Official library provides full REST API coverage with backward compatibility
- AsyncClient enables concurrent agent processing without blocking
- Streaming reduces timeout issues by providing incremental responses
- httpx-based client allows flexible timeout configuration

**Alternatives Considered**:
- **LangChain's ChatOllama wrapper**: Rejected - unnecessary abstraction layer
- **Direct REST API calls**: Rejected - missing error handling and retry logic
- **Synchronous Client**: Rejected - blocks concurrent agent processing

**Key Implementation Notes**:
```python
from ollama import AsyncClient

client = AsyncClient(
    host='http://localhost:11434',
    timeout=60.0  # seconds, sufficient for local inference
)

response = await client.chat(
    model='gemma:3',
    messages=[{'role': 'user', 'content': prompt}],
    stream=True
)
```

---

## 2. LLM Retry Patterns

**Decision**: Exponential backoff with jitter, retry only on 5xx/429 errors, maximum 1 retry (per spec FR-014), use tenacity library

**Rationale**:
- Exponential backoff with jitter prevents thundering herd problem
- Only transient failures (5xx, 429, timeouts) should trigger retries
- Jitter spreads retry timing across agents
- Single retry constraint (spec FR-014) limits blast radius

**Alternatives Considered**:
- **Immediate retry without backoff**: Rejected - can overwhelm Ollama server
- **Infinite retries**: Rejected - violates spec requirement
- **Manual retry implementation**: Rejected - error-prone

**Key Implementation Notes**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

@retry(
    stop=stop_after_attempt(2),  # Initial + 1 retry
    wait=wait_exponential_jitter(initial=1, max=5),
    retry=retry_if_exception_type((ollama.ResponseError, httpx.TimeoutException)),
    reraise=True
)
async def call_llm_with_retry(client, prompt):
    return await client.chat(model='gemma:3', messages=messages)
```

**Error Classification**:
- **Retry**: 5xx errors, 429 rate limits, network timeouts
- **Don't retry**: 4xx client errors, 404 model not found, invalid JSON in request

---

## 3. Structured Output from LLMs

**Decision**: Use Ollama's native structured outputs with Pydantic schemas, add prompt instruction "return as JSON", implement post-validation, fallback to regex extraction

**Rationale**:
- Ollama supports JSON schema constraints via GBNF grammars
- Pydantic models generate JSON schemas automatically and provide validation
- Gemma models trained for JSON schema compliance
- Post-validation catches incomplete responses

**Alternatives Considered**:
- **Function calling**: Rejected - not universally supported
- **JSON Mode without schema**: Rejected - doesn't guarantee schema adherence
- **Manual regex parsing**: Kept as fallback only
- **Instructor library**: Rejected - unnecessary wrapper

**Key Implementation Notes**:
```python
from pydantic import BaseModel

class PolicyDecision(BaseModel):
    action: str
    reasoning: str
    confidence: float

response = await client.chat(
    model='gemma:3',
    messages=messages,
    format=PolicyDecision.model_json_schema()
)

# Always post-validate
result = PolicyDecision.model_validate_json(response['message']['content'])
```

**Validation Strategy**: Always validate with Pydantic after generation, even with schema constraints. Regex fallback for cases where LLM adds conversational text around JSON.

---

## 4. Testing LLM-Integrated Systems

**Decision**: Use pytest with pytest-mock for unit tests, mock at AsyncClient level, contract tests with fixed response fixtures, integration tests with real Ollama optional

**Rationale**:
- Mocking at AsyncClient level provides stable interface
- Contract tests validate integration points without LLM dependency
- Fixed response fixtures document expected LLM behavior
- Separation: unit tests mock LLM, integration tests use real Ollama

**Alternatives Considered**:
- **LangChain's FakeListLLM**: Rejected - adds dependency
- **vcrpy for recording**: Rejected - non-deterministic outputs
- **Real LLM in CI**: Rejected - slow and flaky (valuable for smoke tests only)

**Key Implementation Notes**:
```python
# Unit test: Mock retry logic
@pytest.mark.asyncio
async def test_retry_logic_on_timeout(mocker):
    mock_client = AsyncMock()
    mock_client.chat.side_effect = [
        ollama.ResponseError('Timeout'),
        {'message': {'content': '{"action": "test", "reasoning": "test"}'}}
    ]

    result = await call_llm_with_retry(mock_client, "test prompt")
    assert mock_client.chat.call_count == 2

# Contract test: Fixed fixtures
@pytest.fixture
def sample_policy_response():
    return {
        'message': {
            'content': '{"action": "Lower interest rates by 0.5%", "reasoning": "Combat deflation", "confidence": 0.85}'
        }
    }
```

**Test Organization**:
- Unit tests: `tests/unit/test_llm_client.py` (retry logic, error handling)
- Contract tests: `tests/contract/test_llm_contracts.py` (interface validation)
- Integration tests: `tests/integration/test_llm_reasoning.py` (real Ollama, optional)

---

## 5. Prompt Engineering for Reasoning

**Decision**: Use Chain-of-Thought (CoT) prompting with explicit "think step-by-step" instruction, provide domain-specific guidelines in system message, log full reasoning chains at DEBUG level

**Rationale**:
- CoT prompting improves LLM reasoning on complex tasks
- "Think step-by-step" triggers explicit reasoning in instruction-tuned models
- System messages establish domain boundaries without hardcoding types
- Logged reasoning chains enable debugging and auditability (spec FR-017)

**Alternatives Considered**:
- **Zero-shot without CoT**: Rejected - less explainable outputs
- **ReAct pattern**: Rejected - overkill for current scope
- **Self-consistency**: Rejected - increases latency 3-5x

**Key Prompt Templates**:

```python
# Agent prompt (economic policy generation)
AGENT_SYSTEM_PROMPT = """You are an economic policy advisor for a nation.
Analyze the current economic state and propose ONE specific policy action.
Think step-by-step about the economic situation and reasoning behind your recommendation.

Return your response as JSON with this structure:
{
  "action": "specific policy action string",
  "reasoning": "step-by-step explanation of why this action is appropriate",
  "confidence": 0.0-1.0
}"""

AGENT_USER_PROMPT = """Current economic state:
- GDP Growth: {gdp_growth}%
- Inflation: {inflation}%
- Unemployment: {unemployment}%
- Interest Rate: {interest_rate}%

Think step-by-step:
1. What is the most pressing economic issue?
2. What policy action would address this issue?
3. What are the expected effects?

Propose ONE specific economic policy action."""

# Validator prompt (domain validation)
VALIDATOR_SYSTEM_PROMPT = """You are a policy domain validator.
Determine if a proposed action falls within the ECONOMIC policy domain.

Economic domain includes: interest rates, fiscal policy, trade policy, taxation, monetary policy, economic sanctions.
NON-economic domains: military actions, social policy, foreign diplomacy (unless economically focused).

Use permissive validation: accept if the action has ANY significant economic impact, even if it touches other domains.

Return JSON:
{
  "is_valid": true/false,
  "reasoning": "step-by-step explanation of domain determination",
  "confidence": 0.0-1.0
}"""

# Engine prompt (state update reasoning)
ENGINE_SYSTEM_PROMPT = """You are an economic simulation engine.
Given a validated policy action, determine the new interest rate based on economic theory.

Consider:
- Current economic indicators
- Policy action effects
- Monetary policy principles

Return JSON:
{
  "new_interest_rate": float,
  "reasoning": "step-by-step explanation of how you calculated the new rate",
  "confidence": 0.0-1.0
}"""
```

**Prompt Structure**: System message (role + domain) + User message (data + step-by-step trigger + request)

---

## Configuration Management

**Additions to models/config.py**:
```python
class LLMConfig(BaseModel):
    model: str = "gemma:3"
    host: str = "http://localhost:11434"
    timeout: float = 60.0
    max_retries: int = 1  # Per spec FR-014
    temperature: float = 0.7
    stream: bool = True
```

---

## Logging Strategy

**Structured logging for reasoning chains**:
```python
import structlog
logger = structlog.get_logger()

logger.debug(
    "llm_reasoning_chain",
    component="agent",
    agent_id=agent.id,
    prompt=prompt,
    response=response,
    reasoning=parsed_result.reasoning,
    duration_ms=duration
)
```

**Log Levels**:
- DEBUG: Full reasoning chains (spec FR-017)
- INFO: Agent skipped due to validation failure (spec FR-008)
- ERROR: Prominent LLM failure messages (spec FR-015)

---

## Performance Monitoring

**Targets** (from spec):
- LLM response time: <5s per call
- Simulation step: <30s for 10 agents

**Metrics to track**:
- LLM latency per component (Agent/Validator/Engine)
- Retry rates (detect Ollama server issues)
- Validation rejection rates

---

## Dependencies to Add

**New dependencies** (add to pyproject.toml):
```toml
[project.dependencies]
ollama = ">=0.1.0"
httpx = ">=0.25.0"  # Required by ollama client
tenacity = ">=8.0"  # Retry logic

[project.optional-dependencies]
dev = [
    # ... existing dev dependencies
    "pytest-asyncio>=0.23.0",
    "pytest-mock>=3.12.0",
]
```

---

## Implementation Checklist

From this research, the implementation will require:

- [x] Ollama Python client integration (AsyncClient with streaming)
- [x] Retry logic with exponential backoff + jitter (tenacity)
- [x] Structured output validation (Pydantic schemas + post-validation)
- [x] CoT prompt templates for Agent/Validator/Engine
- [x] Debug-level reasoning chain logging (structlog)
- [x] LLM config section in models/config.py
- [x] Mock-based unit tests + contract tests with fixtures
- [x] Error handling: retry once, abort with prominent log

All research findings align with spec requirements (FR-001 through FR-019) and maintain existing architecture.