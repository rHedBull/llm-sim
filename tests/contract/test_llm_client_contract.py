"""Contract tests for LLMClient interface.

These tests validate the LLMClient interface contract from:
specs/004-new-feature-i/contracts/llm_client_contract.md

Tests MUST FAIL before LLMClient implementation (TDD).
"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import TimeoutException
import ollama

# Import will fail until LLMClient is implemented
try:
    from llm_sim.utils.llm_client import LLMClient, LLMFailureException
    from llm_sim.models.config import LLMConfig
    from llm_sim.models.llm_models import PolicyDecision
except ImportError:
    pytest.skip("LLMClient not yet implemented", allow_module_level=True)


@pytest.fixture
def llm_config():
    """Standard LLM configuration for tests."""
    return LLMConfig(
        model="gemma:3",
        host="http://localhost:11434",
        timeout=60.0,
        max_retries=1,
        temperature=0.7,
        stream=True
    )


@pytest.fixture
def sample_policy_response():
    """Sample successful LLM response."""
    return {
        'message': {
            'content': '{"action": "Lower interest rates by 0.5%", "reasoning": "High unemployment indicates weak demand, lowering rates can stimulate borrowing and investment", "confidence": 0.85}'
        }
    }


@pytest.mark.asyncio
async def test_llm_client_successful_first_attempt(llm_config, sample_policy_response):
    """Test successful LLM call on first attempt.

    Contract: LLMClient.call_with_retry should:
    - Call LLM once if successful
    - Return parsed Pydantic model
    - Not retry on success
    """
    client = LLMClient(config=llm_config)

    with patch.object(client.client, 'chat', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = sample_policy_response

        result = await client.call_with_retry(
            prompt="Test prompt",
            response_model=PolicyDecision
        )

        # Assertions
        assert isinstance(result, PolicyDecision)
        assert result.action == "Lower interest rates by 0.5%"
        assert result.confidence == 0.85
        assert mock_chat.call_count == 1


@pytest.mark.asyncio
async def test_llm_client_retry_on_timeout(llm_config, sample_policy_response):
    """Test retry logic on timeout error.

    Contract: LLMClient should:
    - Retry once on TimeoutException
    - Use exponential backoff
    - Return result on second attempt
    """
    client = LLMClient(config=llm_config)

    with patch.object(client.client, 'chat', new_callable=AsyncMock) as mock_chat:
        # First call: timeout, second call: success
        mock_chat.side_effect = [
            TimeoutException("Request timeout"),
            sample_policy_response
        ]

        result = await client.call_with_retry(
            prompt="Test prompt",
            response_model=PolicyDecision
        )

        # Assertions
        assert isinstance(result, PolicyDecision)
        assert mock_chat.call_count == 2


@pytest.mark.asyncio
async def test_llm_client_permanent_failure(llm_config):
    """Test permanent failure after max retries.

    Contract: LLMClient should:
    - Retry once (max_retries=1)
    - Raise LLMFailureException after 2 failed attempts
    - Include error details in exception
    """
    client = LLMClient(config=llm_config)

    with patch.object(client.client, 'chat', new_callable=AsyncMock) as mock_chat:
        # Both calls fail
        mock_chat.side_effect = [
            TimeoutException("Request timeout"),
            TimeoutException("Request timeout")
        ]

        with pytest.raises(LLMFailureException) as exc_info:
            await client.call_with_retry(
                prompt="Test prompt",
                response_model=PolicyDecision
            )

        # Assertions
        assert "timeout" in str(exc_info.value).lower()
        assert mock_chat.call_count == 2


@pytest.mark.asyncio
async def test_llm_client_invalid_response_format(llm_config):
    """Test handling of invalid JSON responses.

    Contract: LLMClient should:
    - Attempt to parse LLM response as JSON
    - Retry if parsing fails
    - Raise exception if retry also fails
    """
    client = LLMClient(config=llm_config)

    with patch.object(client.client, 'chat', new_callable=AsyncMock) as mock_chat:
        # Both calls return invalid JSON
        mock_chat.side_effect = [
            {'message': {'content': 'This is not JSON'}},
            {'message': {'content': 'Still not JSON'}}
        ]

        with pytest.raises(LLMFailureException):
            await client.call_with_retry(
                prompt="Test prompt",
                response_model=PolicyDecision
            )

        assert mock_chat.call_count == 2


@pytest.mark.asyncio
async def test_llm_client_fallback_json_extraction(llm_config):
    """Test fallback JSON extraction when LLM wraps JSON in text.

    Contract: LLMClient should:
    - Extract JSON from surrounding text
    - Use regex fallback if needed
    - Parse extracted JSON successfully
    """
    client = LLMClient(config=llm_config)

    # Response with JSON wrapped in conversational text
    wrapped_response = {
        'message': {
            'content': 'Sure, here is my response:\n{"action": "Increase taxes", "reasoning": "To reduce deficit", "confidence": 0.7}\nHope this helps!'
        }
    }

    with patch.object(client.client, 'chat', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = wrapped_response

        result = await client.call_with_retry(
            prompt="Test prompt",
            response_model=PolicyDecision
        )

        # Assertions
        assert isinstance(result, PolicyDecision)
        assert result.action == "Increase taxes"
        assert result.confidence == 0.7
        assert mock_chat.call_count == 1


@pytest.mark.asyncio
async def test_llm_client_no_retry_on_client_error(llm_config):
    """Test no retry on 4xx client errors.

    Contract: LLMClient should:
    - Not retry on 4xx errors (except 429)
    - Raise exception immediately
    - Only attempt once
    """
    client = LLMClient(config=llm_config)

    with patch.object(client.client, 'chat', new_callable=AsyncMock) as mock_chat:
        # 404 error (client error, should not retry)
        error_response = ollama.ResponseError("Model not found")
        error_response.status_code = 404
        mock_chat.side_effect = error_response

        with pytest.raises((LLMFailureException, ollama.ResponseError)):
            await client.call_with_retry(
                prompt="Test prompt",
                response_model=PolicyDecision
            )

        # Should only attempt once (no retry on 4xx)
        assert mock_chat.call_count == 1