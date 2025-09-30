"""LLM Client for Ollama integration with retry logic.

This module provides a robust LLM client with:
- Automatic retry on transient failures
- Exponential backoff with jitter
- Structured output validation
- Fallback JSON extraction
"""

import re
import json
from typing import Type, TypeVar, Optional
from datetime import datetime

import structlog
import ollama
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
)
from pydantic import BaseModel, ValidationError

from llm_sim.models.config import LLMConfig

logger = structlog.get_logger()

T = TypeVar('T', bound=BaseModel)


class LLMFailureException(Exception):
    """Exception raised when LLM call fails after retries."""

    def __init__(self, reason: str, attempts: int, status_code: Optional[int] = None):
        self.reason = reason
        self.attempts = attempts
        self.status_code = status_code
        super().__init__(f"LLM failure after {attempts} attempts: {reason}")


def should_retry_exception(exception: Exception) -> bool:
    """Determine if an exception should trigger a retry.

    Retry on:
    - 5xx errors (server errors)
    - 429 (rate limiting)
    - Timeout exceptions

    Don't retry on:
    - 4xx errors (except 429) - client errors
    """
    if isinstance(exception, httpx.TimeoutException):
        return True

    if isinstance(exception, ollama.ResponseError):
        status_code = getattr(exception, 'status_code', None)
        if status_code is None:
            # If no status code, assume it's a network error and retry
            return True
        # Retry on 5xx and 429
        if status_code >= 500 or status_code == 429:
            return True
        # Don't retry on other 4xx errors
        return False

    # For other exceptions, don't retry by default
    return False


class LLMClient:
    """Client for calling LLM with retry logic and structured outputs."""

    def __init__(self, config: LLMConfig):
        """Initialize LLM client with configuration.

        Args:
            config: LLM configuration (model, host, timeout, retries, etc.)
        """
        self.config = config
        self.client = ollama.AsyncClient(
            host=config.host,
            timeout=config.timeout
        )
        self.logger = structlog.get_logger()

    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extract JSON from text that may contain surrounding content.

        Some LLMs wrap JSON in conversational text like:
        "Sure, here is the response: {...} Hope this helps!"

        Args:
            text: Raw text potentially containing JSON

        Returns:
            Extracted JSON string or None if not found
        """
        # Try to find JSON object with regex
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        if matches:
            # Return the first match (assume it's the main response)
            return matches[0]

        return None

    async def call_with_retry(
        self,
        prompt: str,
        response_model: Type[T],
        component: str = "unknown"
    ) -> T:
        """Call LLM with retry logic and structured output validation.

        Args:
            prompt: The prompt to send to the LLM
            response_model: Pydantic model class for response validation
            component: Component name for logging (agent/validator/engine)

        Returns:
            Validated Pydantic model instance

        Raises:
            LLMFailureException: If all retry attempts fail
        """
        # Create retry decorator dynamically to track attempts
        attempt_count = [0]  # Use list to modify in closure

        @retry(
            stop=stop_after_attempt(self.config.max_retries + 1),  # Initial + retries
            wait=wait_exponential_jitter(initial=1, max=5),
            retry=retry_if_exception_type((httpx.TimeoutException, ollama.ResponseError, ValueError)),
            reraise=True
        )
        async def _call_with_retry_inner():
            attempt_count[0] += 1
            start_time = datetime.now()

            try:
                # Call Ollama with structured output format
                response = await self.client.chat(
                    model=self.config.model,
                    messages=[{'role': 'user', 'content': prompt}],
                    format=response_model.model_json_schema(),
                    options={
                        'temperature': self.config.temperature,
                    },
                    stream=self.config.stream
                )

                # Extract content from response
                # Check if response is actually a generator/async iterator
                if hasattr(response, '__aiter__'):
                    # Streaming response: collect all chunks
                    content_parts = []
                    async for chunk in response:
                        if 'message' in chunk and 'content' in chunk['message']:
                            content_parts.append(chunk['message']['content'])
                    content = ''.join(content_parts)
                else:
                    # Non-streaming response or dict from mock
                    content = response['message']['content']

                # Try to parse directly
                try:
                    result = response_model.model_validate_json(content)
                except (ValidationError, json.JSONDecodeError) as parse_error:
                    # Fallback: try to extract JSON from text
                    self.logger.debug(
                        "llm_json_extraction_fallback",
                        component=component,
                        raw_content=content[:200]  # Log first 200 chars
                    )
                    extracted = self._extract_json_from_text(content)
                    if extracted:
                        try:
                            result = response_model.model_validate_json(extracted)
                        except (ValidationError, json.JSONDecodeError):
                            # Even extracted JSON is invalid, treat as retryable error
                            raise ValueError(f"Invalid JSON response format: {parse_error}")
                    else:
                        # No JSON found, treat as retryable error (LLM might have had issues)
                        raise ValueError(f"Invalid JSON response format: {parse_error}")

                # Log successful call
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                self.logger.debug(
                    "llm_call_success",
                    component=component,
                    duration_ms=duration_ms,
                    attempt=attempt_count[0],
                    model=self.config.model
                )

                return result

            except (httpx.TimeoutException, ollama.ResponseError, ValueError) as e:
                # Check if we should retry
                if isinstance(e, ValueError) or should_retry_exception(e):
                    # Log retry attempt
                    self.logger.warning(
                        "llm_call_retry",
                        component=component,
                        attempt=attempt_count[0],
                        error=str(e),
                        will_retry=(attempt_count[0] < self.config.max_retries + 1)
                    )
                    raise  # Will trigger retry
                else:
                    # Don't retry on client errors
                    status_code = getattr(e, 'status_code', None)
                    raise LLMFailureException(
                        reason=str(e),
                        attempts=attempt_count[0],
                        status_code=status_code
                    )

        try:
            return await _call_with_retry_inner()
        except Exception as e:
            # Final failure after all retries
            self.logger.error(
                "LLM_FAILURE",
                component=component,
                error=str(e),
                attempts=attempt_count[0],
                model=self.config.model
            )

            # Convert to LLMFailureException if not already
            if isinstance(e, LLMFailureException):
                raise
            else:
                raise LLMFailureException(
                    reason=str(e),
                    attempts=attempt_count[0]
                )