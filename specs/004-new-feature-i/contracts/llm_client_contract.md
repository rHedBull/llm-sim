# LLM Client Contract

**Component**: `llm_sim.utils.llm_client.LLMClient`
**Purpose**: Provides unified interface for LLM interactions with retry logic and error handling

---

## Interface

### `async def call_with_retry(prompt: str, response_model: Type[BaseModel]) -> BaseModel`

**Description**: Calls LLM with automatic retry on transient failures, returns structured response.

**Input Parameters**:
- `prompt` (str): Full prompt to send to LLM (system + user messages constructed by caller)
- `response_model` (Type[BaseModel]): Pydantic model class for response validation

**Output**:
- Returns: Instance of `response_model` with validated LLM response
- Raises: `LLMFailureException` if LLM fails after retry (per spec FR-016)

**Behavior Guarantees**:
1. **Retry exactly once** on transient failures (5xx, 429, timeout) - spec FR-014
2. **No retry** on permanent failures (4xx except 429, invalid JSON)
3. **Exponential backoff with jitter** between attempts (1-5 seconds)
4. **Log prominent ERROR** if both attempts fail - spec FR-015
5. **Timeout**: 60 seconds per call (configurable via LLMConfig)
6. **Response validation**: Always validates against response_model schema
7. **Fallback parsing**: Attempts regex extraction if LLM adds wrapper text around JSON

**Error Conditions**:
- `LLMFailureException(reason="timeout", attempts=2)`: Both LLM calls timed out
- `LLMFailureException(reason="server_error", attempts=2, status_code=500)`: 5xx error persisted after retry
- `LLMFailureException(reason="invalid_response", attempts=2)`: LLM response doesn't match schema after retry
- `LLMFailureException(reason="connection_error", attempts=2)`: Cannot reach Ollama server

**Performance**:
- Target: <5s for successful first attempt
- Maximum: 120s total (60s timeout × 2 attempts, not counting backoff)

---

## Contract Tests

### Test 1: Successful First Attempt
```python
@pytest.mark.asyncio
async def test_llm_client_successful_first_attempt():
    """LLM returns valid response on first attempt"""
    # Given: LLM client with mocked successful response
    mock_response = {
        'message': {
            'content': '{"action": "Lower rates", "reasoning": "Combat deflation", "confidence": 0.85}'
        }
    }
    client = LLMClient(mock_ollama_client=mock_response)

    # When: Calling LLM with PolicyDecision model
    result = await client.call_with_retry(
        prompt="Generate policy",
        response_model=PolicyDecision
    )

    # Then: Returns validated PolicyDecision
    assert isinstance(result, PolicyDecision)
    assert result.action == "Lower rates"
    assert result.confidence == 0.85
    # And: No retry occurred
    assert mock_ollama_client.call_count == 1
```

### Test 2: Retry on Timeout, Then Success
```python
@pytest.mark.asyncio
async def test_llm_client_retry_on_timeout():
    """LLM times out on first attempt, succeeds on retry"""
    # Given: LLM client with timeout then success
    mock_client = AsyncMock()
    mock_client.chat.side_effect = [
        httpx.TimeoutException("Request timeout"),
        {'message': {'content': '{"action": "test", "reasoning": "test", "confidence": 0.5}'}}
    ]
    client = LLMClient(ollama_client=mock_client)

    # When: Calling LLM
    result = await client.call_with_retry(
        prompt="Generate policy",
        response_model=PolicyDecision
    )

    # Then: Returns valid response after retry
    assert isinstance(result, PolicyDecision)
    # And: Exactly 2 attempts made
    assert mock_client.chat.call_count == 2
    # And: Backoff delay occurred (check logs or timing)
```

### Test 3: Permanent Failure After Retry
```python
@pytest.mark.asyncio
async def test_llm_client_permanent_failure():
    """LLM fails on both attempts, raises exception"""
    # Given: LLM client with persistent 500 error
    mock_client = AsyncMock()
    mock_client.chat.side_effect = [
        ollama.ResponseError("Server error", status_code=500),
        ollama.ResponseError("Server error", status_code=500)
    ]
    client = LLMClient(ollama_client=mock_client)

    # When: Calling LLM
    with pytest.raises(LLMFailureException) as exc_info:
        await client.call_with_retry(
            prompt="Generate policy",
            response_model=PolicyDecision
        )

    # Then: Exception contains failure details
    assert exc_info.value.reason == "server_error"
    assert exc_info.value.attempts == 2
    assert exc_info.value.status_code == 500
    # And: Prominent error was logged
    # (assert log output contains "LLM_FAILURE")
```

### Test 4: Invalid Response Format
```python
@pytest.mark.asyncio
async def test_llm_client_invalid_response_format():
    """LLM returns non-JSON response, triggers retry, then fails"""
    # Given: LLM returns invalid format twice
    mock_client = AsyncMock()
    mock_client.chat.side_effect = [
        {'message': {'content': 'I cannot help with that'}},
        {'message': {'content': 'Invalid response again'}}
    ]
    client = LLMClient(ollama_client=mock_client)

    # When: Calling LLM
    with pytest.raises(LLMFailureException) as exc_info:
        await client.call_with_retry(
            prompt="Generate policy",
            response_model=PolicyDecision
        )

    # Then: Exception indicates invalid response
    assert exc_info.value.reason == "invalid_response"
    assert exc_info.value.attempts == 2
```

### Test 5: Fallback JSON Extraction
```python
@pytest.mark.asyncio
async def test_llm_client_fallback_json_extraction():
    """LLM wraps JSON in conversational text, client extracts it"""
    # Given: LLM returns JSON wrapped in text
    mock_response = {
        'message': {
            'content': 'Here is my response:\n{"action": "test", "reasoning": "test", "confidence": 0.5}\nI hope this helps!'
        }
    }
    client = LLMClient(mock_ollama_client=mock_response)

    # When: Calling LLM
    result = await client.call_with_retry(
        prompt="Generate policy",
        response_model=PolicyDecision
    )

    # Then: Successfully extracts and validates JSON
    assert isinstance(result, PolicyDecision)
    assert result.action == "test"
```

### Test 6: No Retry on 4xx Client Error
```python
@pytest.mark.asyncio
async def test_llm_client_no_retry_on_client_error():
    """LLM returns 4xx error (e.g., 404 model not found), no retry"""
    # Given: LLM returns 404 (model not found)
    mock_client = AsyncMock()
    mock_client.chat.side_effect = ollama.ResponseError("Model not found", status_code=404)
    client = LLMClient(ollama_client=mock_client)

    # When: Calling LLM
    with pytest.raises(LLMFailureException) as exc_info:
        await client.call_with_retry(
            prompt="Generate policy",
            response_model=PolicyDecision
        )

    # Then: Exception raised after single attempt (no retry on 4xx)
    assert exc_info.value.attempts == 1
    assert mock_client.chat.call_count == 1
```

---

## Integration Points

**Used by**:
- `llm_sim.agents.base.Agent` → for policy decision generation
- `llm_sim.validators.llm_validator.LLMValidator` → for domain validation
- `llm_sim.engines.base.Engine` → for state update reasoning

**Dependencies**:
- `ollama.AsyncClient` (external library)
- `httpx` (for timeout handling)
- `tenacity` (for retry logic)
- `pydantic` (for response validation)

**Configuration**: Reads from `LLMConfig` in `SimulationConfig`

---

## Example Usage

```python
from llm_sim.utils.llm_client import LLMClient
from llm_sim.models.llm_models import PolicyDecision

# Initialize client with config
client = LLMClient(config=simulation_config.llm)

# Construct prompt
prompt = f"""You are an economic advisor.
Current GDP: {state.gdp}%
Current Inflation: {state.inflation}%

Propose one policy action.
"""

# Call LLM with retry
try:
    decision = await client.call_with_retry(
        prompt=prompt,
        response_model=PolicyDecision
    )
    print(f"Action: {decision.action}")
    print(f"Reasoning: {decision.reasoning}")
except LLMFailureException as e:
    logger.error("LLM_FAILURE", component="agent", error=str(e))
    raise  # Abort simulation step
```

---

## Version: 1.0.0
**Status**: Draft
**Last Updated**: 2025-09-30