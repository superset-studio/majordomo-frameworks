"""Pydantic AI framework adapter for Majordomo Gateway.

Factory functions to create Pydantic AI models that route requests through
Majordomo Gateway for centralized logging and cost tracking.

Usage:
    from majordomo_frameworks.pydantic_ai import create_model, build_extra_headers

    # Create a model routed through the gateway
    model = create_model("anthropic")

    # Build headers for use in model settings
    headers = build_extra_headers(feature="my-agent", step="synthesis")

    # Use with AnthropicModelSettings
    from pydantic_ai.settings import AnthropicModelSettings
    settings = AnthropicModelSettings(
        extra_headers=headers,
        anthropic_thinking={"type": "enabled", "budget_tokens": 32000},
    )

Supported providers:
- OpenAI: Uses AsyncOpenAI client with gateway base_url
- Anthropic: Uses AnthropicProvider with gateway base_url
- Gemini: Via OpenAI-compatible endpoint (requires X-Majordomo-Provider header)
"""

import os

from openai import AsyncOpenAI
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.openai import OpenAIProvider

from majordomo_frameworks import (
    PROVIDER_DEFAULTS,
    Provider,
    get_gateway_url,
    get_majordomo_key,
)


def build_extra_headers(
    *,
    feature: str | None = None,
    step: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build Majordomo headers for use in model settings extra_headers.

    Use these headers with AnthropicModelSettings or OpenAIChatModelSettings:

        from pydantic_ai.settings import AnthropicModelSettings

        headers = build_extra_headers(feature="my-agent", step="synthesis")
        settings = AnthropicModelSettings(
            extra_headers=headers,
            # ... other settings
        )

    Args:
        feature: Feature name for cost attribution
        step: Workflow step for granular tracking
        user_id: User ID for per-user cost tracking
        session_id: Session ID for conversation tracking
        extra_headers: Additional headers to include in the result

    Returns:
        Dict of X-Majordomo-* headers to pass as extra_headers
    """
    headers: dict[str, str] = {"X-Majordomo-Key": get_majordomo_key()}

    if feature:
        headers["X-Majordomo-Feature"] = feature
    if step:
        headers["X-Majordomo-Step"] = step
    if user_id:
        headers["X-Majordomo-User-Id"] = user_id
    if session_id:
        headers["X-Majordomo-Session-Id"] = session_id
    if extra_headers:
        headers.update(extra_headers)

    return headers


def build_extra_headers_gemini(
    *,
    feature: str | None = None,
    step: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build Majordomo headers for Gemini models (includes provider routing header).

    Gemini uses the OpenAI-compatible endpoint, so it needs an extra header
    to tell the gateway to route to Gemini.

    Args:
        feature: Feature name for cost attribution
        step: Workflow step for granular tracking
        user_id: User ID for per-user cost tracking
        session_id: Session ID for conversation tracking
        extra_headers: Additional headers to include in the result

    Returns:
        Dict of headers including X-Majordomo-Provider for Gemini routing
    """
    headers = build_extra_headers(
        feature=feature,
        step=step,
        user_id=user_id,
        session_id=session_id,
        extra_headers=extra_headers,
    )
    headers["X-Majordomo-Provider"] = "gemini-openai"
    return headers


def create_openai_model(model_name: str = "gpt-4o") -> OpenAIModel:
    """Create an OpenAI model routed through the gateway.

    The model is configured with the gateway base_url. Use build_extra_headers()
    to create headers for OpenAIChatModelSettings.

    Args:
        model_name: OpenAI model name (e.g., "gpt-4o", "gpt-4o-mini")

    Returns:
        OpenAIModel configured to route through Majordomo Gateway
    """
    client = AsyncOpenAI(
        base_url=f"{get_gateway_url()}/v1",
        api_key=os.environ["OPENAI_API_KEY"],
    )
    return OpenAIModel(model_name, provider=OpenAIProvider(openai_client=client))


def create_anthropic_model(model_name: str = "claude-sonnet-4-20250514") -> AnthropicModel:
    """Create an Anthropic model routed through the gateway.

    The model is configured with the gateway base_url. Use build_extra_headers()
    to create headers for AnthropicModelSettings.

    Args:
        model_name: Anthropic model name (e.g., "claude-sonnet-4-20250514")

    Returns:
        AnthropicModel configured to route through Majordomo Gateway
    """
    return AnthropicModel(
        model_name,
        provider=AnthropicProvider(
            base_url=get_gateway_url(),
            api_key=os.environ["ANTHROPIC_API_KEY"],
        ),
    )


def create_gemini_model(model_name: str = "gemini-2.0-flash") -> OpenAIModel:
    """Create a Gemini model routed through the gateway via OpenAI-compatible endpoint.

    The model is configured with the gateway base_url. Use build_extra_headers_gemini()
    to create headers for OpenAIChatModelSettings (includes the provider routing header).

    Args:
        model_name: Gemini model name (e.g., "gemini-2.0-flash", "gemini-2.5-pro")

    Returns:
        OpenAIModel configured to route through Majordomo Gateway to Gemini
    """
    client = AsyncOpenAI(
        base_url=f"{get_gateway_url()}/v1",
        api_key=os.environ["GEMINI_API_KEY"],
    )
    return OpenAIModel(model_name, provider=OpenAIProvider(openai_client=client))


def create_model(
    provider: Provider,
    model_name: str | None = None,
) -> OpenAIModel | AnthropicModel:
    """Create a model for the specified provider, routed through the gateway.

    The model is configured with the gateway base_url but no headers baked in.
    Use build_extra_headers() (or build_extra_headers_gemini() for Gemini) to
    create headers for your model settings.

    Example:
        model = create_model("anthropic")
        headers = build_extra_headers(feature="my-agent", step="synthesis")
        settings = AnthropicModelSettings(extra_headers=headers, ...)

    Args:
        provider: The LLM provider ("openai", "anthropic", or "gemini")
        model_name: Model name (uses sensible defaults if not specified)

    Returns:
        A Pydantic AI model configured to route through Majordomo Gateway
    """
    name = model_name or PROVIDER_DEFAULTS[provider]

    match provider:
        case "openai":
            return create_openai_model(name)
        case "anthropic":
            return create_anthropic_model(name)
        case "gemini":
            return create_gemini_model(name)
