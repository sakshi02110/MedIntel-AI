"""
LLM Service for MedIntel AI.

Wraps the Groq API (Llama 3.3 70B) with:
- Exponential-backoff retries via tenacity
- JSON-mode support
- Streaming support (optional)
- Clear error logging
"""

import os
import time
from typing import Dict, Iterator, List, Optional, Any

from dotenv import load_dotenv
from groq import (
    Groq,
    APIConnectionError,
    APIStatusError,
    RateLimitError,
)
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError,
)

from src.utils.logger import get_logger

load_dotenv()

logger = get_logger("medintel.llm_service")

# ── Constants ──────────────────────────────────────────────────────────────────
DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_MAX_TOKENS = 4_096
DEFAULT_TEMPERATURE = 0.1      # Low temperature → deterministic medical facts
MAX_RETRIES = 3


# ── Retry decorator ────────────────────────────────────────────────────────────
def _make_retry_decorator():
    """Build a tenacity retry decorator for transient Groq API errors."""
    return retry(
        reraise=True,
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=16),
        retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
        before_sleep=before_sleep_log(logger, 20),  # 20 = logging.INFO
    )


_retry = _make_retry_decorator()


class LLMService:
    """
    High-level wrapper around the Groq chat-completions API.

    Example::

        llm = LLMService()
        result = llm.simple_prompt(
            system_prompt="You are a medical analyst.",
            user_prompt="Summarize this CBC report: ...",
        )
    """

    def __init__(self, model: str = DEFAULT_MODEL):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY not set. "
                "Please add it to your .env file."
            )
        self.model = model
        self._client = Groq(api_key=api_key)
        logger.info(f"LLMService ready (model={model})")

    # ── Public API ─────────────────────────────────────────────────────────────

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        json_mode: bool = False,
    ) -> Optional[str]:
        """
        Send a chat completion request.

        Args:
            messages:    OpenAI-style message list ``[{"role": ..., "content": ...}]``.
            max_tokens:  Token limit for the response.
            temperature: Sampling temperature (0 = deterministic).
            json_mode:   If True, instruct Groq to return a JSON object.

        Returns:
            Response content string, or ``None`` if all retries fail.
        """
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            return self._chat_with_retry(kwargs)
        except RetryError as exc:
            logger.error(f"All {MAX_RETRIES} retry attempts exhausted: {exc}")
            return None
        except APIStatusError as exc:
            logger.error(f"Groq API status error {exc.status_code}: {exc.message}")
            return None
        except Exception as exc:
            logger.error(f"Unexpected LLM error: {exc}", exc_info=True)
            return None

    def simple_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs,
    ) -> Optional[str]:
        """
        Convenience wrapper: one system message + one user message.

        All ``**kwargs`` are forwarded to :meth:`chat`.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.chat(messages, **kwargs)

    # ── Private ────────────────────────────────────────────────────────────────

    @_retry
    def _chat_with_retry(self, kwargs: Dict[str, Any]) -> str:
        """Execute the API call; tenacity handles retries on transient errors."""
        logger.debug(
            f"LLM request: model={self.model}, "
            f"messages={len(kwargs['messages'])}, "
            f"json_mode={kwargs.get('response_format') is not None}"
        )
        start = time.perf_counter()
        response = self._client.chat.completions.create(**kwargs)
        elapsed = time.perf_counter() - start

        content = response.choices[0].message.content or ""
        usage = response.usage
        logger.info(
            f"LLM ← {usage.completion_tokens} tokens "
            f"({usage.prompt_tokens} prompt) in {elapsed:.2f}s"
        )
        return content
