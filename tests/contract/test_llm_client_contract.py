"""
from llm_sim.models.state import GlobalState
Contract tests for LLMClient utility.

These tests validate the interface and behavior of the LLM client,
including retry logic, error handling, and response validation.

Status: THESE TESTS MUST FAIL - LLMClient not yet implemented
"""

import pytest
from unittest.mock import AsyncMock
import httpx

# These imports will fail until implementation is complete
try:
    from llm_sim.utils.llm_client import LLMClient, LLMFailureException
    from llm_sim.models.llm_models import PolicyDecision
    import ollama
except ImportError:
    pytest.skip("LLMClient not yet implemented", allow_module_level=True)


@pytest.mark.asyncio
async def test_llm_client_successful_first_attempt():
    """LLM returns valid response on first attempt"""
    # Given: LLM client with mocked successful response
    mock_client = AsyncMock()
    mock_client.chat.return_value = {
        'message': {
            'content': '{"action": "Lower rates", "reasoning": "Combat deflation", "confidence": 0.85}'
        }
    }

    config = type('Config', (), {
        'model': 'gemma:3',
        'host': 'http://localhost:11434',
        'timeout': 60.0,
        'max_retries': 1,
        'temperature': 0.7,
        'stream': True
    })()

    client = LLMClient(config=config, ollama_client=mock_client)

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
    assert mock_client.chat.call_count == 1


@pytest.mark.asyncio
async def test_llm_client_retry_on_timeout():
    """LLM times out on first attempt, succeeds on retry"""
    # Given: LLM client with timeout then success
    mock_client = AsyncMock()
    mock_client.chat.side_effect = [
        httpx.TimeoutException("Request timeout"),
        {'message': {'content': '{"action": "test", "reasoning": "test reasoning", "confidence": 0.5}'}}
    ]

    config = type('Config', (), {
        'model': 'gemma:3',
        'host': 'http://localhost:11434',
        'timeout': 60.0,
        'max_retries': 1,
        'temperature': 0.7,
        'stream': True
    })()

    client = LLMClient(config=config, ollama_client=mock_client)

    # When: Calling LLM
    result = await client.call_with_retry(
        prompt="Generate policy",
        response_model=PolicyDecision
    )

    # Then: Returns valid response after retry
    assert isinstance(result, PolicyDecision)
    # And: Exactly 2 attempts made
    assert mock_client.chat.call_count == 2


@pytest.mark.asyncio
async def test_llm_client_permanent_failure():
    """LLM fails on both attempts, raises exception"""
    # Given: LLM client with persistent 500 error
    mock_client = AsyncMock()
    mock_client.chat.side_effect = [
        Exception("Server error 500"),
        Exception("Server error 500")
    ]

    config = type('Config', (), {
        'model': 'gemma:3',
        'host': 'http://localhost:11434',
        'timeout': 60.0,
        'max_retries': 1,
        'temperature': 0.7,
        'stream': True
    })()

    client = LLMClient(config=config, ollama_client=mock_client)

    # When: Calling LLM
    with pytest.raises(LLMFailureException) as exc_info:
        await client.call_with_retry(
            prompt="Generate policy",
            response_model=PolicyDecision
        )

    # Then: Exception contains failure details
    assert exc_info.value.attempts == 2


@pytest.mark.asyncio
async def test_llm_client_invalid_response_format():
    """LLM returns non-JSON response, triggers retry, then fails"""
    # Given: LLM returns invalid format twice
    mock_client = AsyncMock()
    mock_client.chat.side_effect = [
        {'message': {'content': 'I cannot help with that'}},
        {'message': {'content': 'Invalid response again'}}
    ]

    config = type('Config', (), {
        'model': 'gemma:3',
        'host': 'http://localhost:11434',
        'timeout': 60.0,
        'max_retries': 1,
        'temperature': 0.7,
        'stream': True
    })()

    client = LLMClient(config=config, ollama_client=mock_client)

    # When: Calling LLM
    with pytest.raises(LLMFailureException) as exc_info:
        await client.call_with_retry(
            prompt="Generate policy",
            response_model=PolicyDecision
        )

    # Then: Exception indicates invalid response
    assert exc_info.value.attempts == 2


@pytest.mark.asyncio
async def test_llm_client_fallback_json_extraction():
    """LLM wraps JSON in conversational text, client extracts it"""
    # Given: LLM returns JSON wrapped in text
    mock_client = AsyncMock()
    mock_client.chat.return_value = {
        'message': {
            'content': 'Here is my response:\n{"action": "test", "reasoning": "test reasoning here", "confidence": 0.5}\nI hope this helps!'
        }
    }

    config = type('Config', (), {
        'model': 'gemma:3',
        'host': 'http://localhost:11434',
        'timeout': 60.0,
        'max_retries': 1,
        'temperature': 0.7,
        'stream': True
    })()

    client = LLMClient(config=config, ollama_client=mock_client)

    # When: Calling LLM
    result = await client.call_with_retry(
        prompt="Generate policy",
        response_model=PolicyDecision
    )

    # Then: Successfully extracts and validates JSON
    assert isinstance(result, PolicyDecision)
    assert result.action == "test"


@pytest.mark.asyncio
async def test_llm_client_no_retry_on_client_error():
    """LLM returns 4xx error (e.g., 404 model not found), no retry"""
    # Given: LLM returns 404 (model not found)
    mock_client = AsyncMock()
    mock_client.chat.side_effect = Exception("Model not found 404")

    config = type('Config', (), {
        'model': 'gemma:3',
        'host': 'http://localhost:11434',
        'timeout': 60.0,
        'max_retries': 1,
        'temperature': 0.7,
        'stream': True
    })()

    client = LLMClient(config=config, ollama_client=mock_client)

    # When: Calling LLM
    with pytest.raises(LLMFailureException) as exc_info:
        await client.call_with_retry(
            prompt="Generate policy",
            response_model=PolicyDecision
        )

    # Then: Exception raised after single attempt (no retry on 4xx)
    assert exc_info.value.attempts == 1
    assert mock_client.chat.call_count == 1
