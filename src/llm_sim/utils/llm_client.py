"""LLM client with retry logic for simulation components."""

import json
import re
import time
from typing import Type, TypeVar, Optional

import httpx
import structlog
from pydantic import BaseModel, ValidationError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
)

try:
    import ollama
except ImportError:
    ollama = None

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)


class LLMFailureException(Exception):
    """Exception raised when LLM fails after retry."""

    def __init__(
        self, reason: str, attempts: int, status_code: Optional[int] = None
    ):
        """Initialize LLM failure exception.

        Args:
            reason: Reason for failure (e.g., "timeout", "server_error")
            attempts: Number of attempts made
            status_code: HTTP status code if applicable
        """
        self.reason = reason
        self.attempts = attempts
        self.status_code = status_code
        super().__init__(
            f"LLM failed after {attempts} attempts: {reason}"
            + (f" (status={status_code})" if status_code else "")
        )


class ClientError(Exception):
    """Non-retryable client error (4xx)."""
    pass


class LLMClient:
    """Client for LLM interactions with automatic retry logic."""

    def __init__(self, config, ollama_client=None):
        """Initialize LLM client.

        Args:
            config: LLMConfig instance with model, host, timeout, etc.
            ollama_client: Optional pre-configured ollama.AsyncClient (for testing)
        """
        self.config = config
        if ollama_client is not None:
            self.client = ollama_client
        elif ollama:
            self.client = ollama.AsyncClient(
                host=config.host, timeout=httpx.Timeout(config.timeout)
            )
        else:
            raise ImportError("ollama library not installed")

        self.attempt_count = 0

    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON from text that may have conversational wrapper.

        Args:
            text: Text that may contain JSON

        Returns:
            Extracted JSON string

        Raises:
            ValueError: If no JSON found in text
        """
        # Try to find JSON object in text using regex
        json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        raise ValueError("No JSON object found in response")

    async def call_with_retry(
        self, prompt: str, response_model: Type[T]
    ) -> T:
        """Call LLM with automatic retry on transient failures.

        Args:
            prompt: Full prompt to send to LLM
            response_model: Pydantic model class for response validation

        Returns:
            Validated instance of response_model

        Raises:
            LLMFailureException: If LLM fails after retry
        """
        self.attempt_count = 0

        def _should_retry(retry_state):
            """Determine if exception should trigger retry."""
            if retry_state.outcome and retry_state.outcome.failed:
                exception = retry_state.outcome.exception()
                if isinstance(exception, ClientError):
                    return False  # Never retry 4xx errors
                # Retry all other exceptions
                return True
            return False

        @retry(
            stop=stop_after_attempt(self.config.max_retries + 1),
            wait=wait_exponential_jitter(initial=1, max=5),
            retry=_should_retry,
            reraise=True,
        )
        async def _call_with_retry_inner():
            self.attempt_count += 1
            start_time = time.time()

            try:
                # Call Ollama
                response = await self.client.chat(
                    model=self.config.model,
                    messages=[{"role": "user", "content": prompt}],
                    format=response_model.model_json_schema(),
                    stream=False,
                )

                duration_ms = int((time.time() - start_time) * 1000)

                # Extract response content
                content = response["message"]["content"]

                # Try direct parsing
                try:
                    result = response_model.model_validate_json(content)
                    logger.debug(
                        "llm_call_success",
                        attempts=self.attempt_count,
                        duration_ms=duration_ms,
                    )
                    return result
                except (ValidationError, json.JSONDecodeError):
                    # Try fallback extraction
                    try:
                        json_str = self._extract_json_from_text(content)
                        result = response_model.model_validate_json(json_str)
                        logger.debug(
                            "llm_call_success_with_extraction",
                            attempts=self.attempt_count,
                            duration_ms=duration_ms,
                        )
                        return result
                    except (ValueError, ValidationError, json.JSONDecodeError) as e:
                        raise LLMFailureException(
                            reason="invalid_response",
                            attempts=self.attempt_count,
                        ) from e

            except httpx.TimeoutException as e:
                logger.warning(
                    "llm_timeout",
                    attempt=self.attempt_count,
                    error=str(e),
                )
                if self.attempt_count >= self.config.max_retries + 1:
                    raise LLMFailureException(
                        reason="timeout", attempts=self.attempt_count
                    ) from e
                raise  # Retry

            except httpx.ConnectError as e:
                logger.warning(
                    "llm_connection_error",
                    attempt=self.attempt_count,
                    error=str(e),
                )
                if self.attempt_count >= self.config.max_retries + 1:
                    raise LLMFailureException(
                        reason="connection_error",
                        attempts=self.attempt_count,
                    ) from e
                raise  # Retry

            except Exception as e:
                error_str = str(e).lower()
                # Check if it's a 4xx client error (don't retry)
                if "404" in error_str or "400" in error_str:
                    raise ClientError(f"Client error: {e}") from e

                # 5xx or other errors (retry)
                logger.warning(
                    "llm_error",
                    attempt=self.attempt_count,
                    error=str(e),
                )
                if self.attempt_count >= self.config.max_retries + 1:
                    raise LLMFailureException(
                        reason="server_error",
                        attempts=self.attempt_count,
                        status_code=500,
                    ) from e
                raise  # Retry

        try:
            return await _call_with_retry_inner()
        except ClientError as e:
            # 4xx errors - don't retry, convert to LLMFailureException
            exc = LLMFailureException(
                reason="client_error",
                attempts=self.attempt_count,
                status_code=404,
            )
            logger.error(
                "LLM_FAILURE",
                reason=exc.reason,
                attempts=exc.attempts,
                status_code=exc.status_code,
            )
            raise exc from e
        except LLMFailureException as e:
            # Already wrapped - log prominent ERROR message
            logger.error(
                "LLM_FAILURE",
                reason=e.reason,
                attempts=e.attempts,
                status_code=e.status_code,
            )
            raise
        except Exception as e:
            # Wrap unexpected exceptions
            exc = LLMFailureException(
                reason="unknown_error",
                attempts=self.attempt_count,
            )
            logger.error(
                "LLM_FAILURE",
                reason=exc.reason,
                attempts=exc.attempts,
            )
            raise exc from e
