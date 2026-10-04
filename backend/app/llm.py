import os
import logging
import time
from typing import Any, List, Optional, Union, Dict
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger(__name__)


def text_of(content: Any) -> str:
    """Gemini/OpenAI may return a list of parts or strings; normalise to str."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for part in content:
            if isinstance(part, str):
                out.append(part)
            elif isinstance(part, dict):
                out.append(part.get("text", "") or part.get("content", ""))
            elif hasattr(part, "text"):
                out.append(part.text)
            else:
                out.append(str(part))
        return "".join(out)
    if hasattr(content, "text"):
        return content.text
    return str(content)


def invoke_with_retry(callable_fn, *args, max_retries: int = 1, delay: float = 1.0, **kwargs):
    """Invoke LLM with a retry-once policy on transient errors."""
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            return callable_fn(*args, **kwargs)
        except Exception as e:
            last_err = e
            logger.warning(
                f"LLM invocation failed (attempt {attempt + 1}/{max_retries + 1}): {type(e).__name__}: {e}"
            )
            if attempt < max_retries:
                time.sleep(delay)
    raise last_err


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
):
    """Factory creating the appropriate Chat model based on provider."""
    provider = (provider or settings.llm_provider).lower().strip()
    model_name = model or settings.llm_model

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = settings.google_api_key or os.environ.get("GOOGLE_API_KEY")
        if not api_key or not api_key.strip():
            logger.warning("No GOOGLE_API_KEY configured. Using FakeLLM offline fallback.")
            return FakeLLM(default_response="Google API key not configured. Please set GOOGLE_API_KEY in .env.")
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=api_key,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key or not api_key.strip():
            logger.warning("No OPENAI_API_KEY configured. Using FakeLLM offline fallback.")
            return FakeLLM(default_response="OpenAI API key not configured. Please set OPENAI_API_KEY in .env.")
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Expected 'gemini' or 'openai'.")


class FakeResponse:
    """Mock LLM response for offline testing."""
    def __init__(self, content: str):
        self.content = content

    def __repr__(self):
        return f"FakeResponse(content={self.content!r})"


class FakeLLM:
    """Scriptable Fake LLM for unit tests without external API dependencies."""
    def __init__(self, responses: Optional[List[str]] = None, default_response: str = '{"ops": []}'):
        self.responses: List[str] = list(responses) if responses else []
        self.default_response: str = default_response
        self.call_history: List[Any] = []

    def set_responses(self, responses: List[str]):
        self.responses = list(responses)

    def invoke(self, prompt: Any, *args, **kwargs) -> FakeResponse:
        self.call_history.append(prompt)
        if self.responses:
            return FakeResponse(self.responses.pop(0))
        return FakeResponse(self.default_response)
