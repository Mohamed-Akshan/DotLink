import logging
from functools import lru_cache
from typing import Any
from core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=2)
def get_model(provider: str) -> Any:
    """Create each configured model once, and reuse it for later requests."""

    if provider == "openai" and settings.openai_api_key:

        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            timeout=15,
            max_retries=0,
        )

    if provider == "gemini" and settings.google_api_key:

        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            timeout=15,
            max_retries=0,
        )

    raise RuntimeError("Model provider is not configured")


def invoke_with_fallback(messages: list, tools: list | None = None, config: dict | None = None) -> Any:
    """Try the primary model, then the backup model only if needed."""

    providers = []

    if settings.openai_api_key:

        providers.append("openai")

    if settings.google_api_key:

        providers.append("gemini")

    for provider in providers:

        try:

            model = get_model(provider)

            if tools:

                model = model.bind_tools(tools)

            return model.invoke(messages, config=config)

        except Exception as error:

            logger.warning("Model %s unavailable: %s", provider, type(error).__name__)

    raise RuntimeError("No AI provider is available")


def message_text(content: Any) -> str:
    """Read plain text returned by either supported model provider."""

    if isinstance(content, str):

        return content

    parts = []

    if isinstance(content, list):

        for part in content:

            if isinstance(part, dict):

                parts.append(part.get("text", ""))

            elif isinstance(part, str):

                parts.append(part)

    return " ".join(parts)
