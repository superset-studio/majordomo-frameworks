"""Agno framework adapter for Majordomo Gateway.

Factory functions to create Agno models that route requests through
Majordomo Gateway for centralized logging and cost tracking.

All providers use OpenAILike since we're routing through the gateway,
which presents an OpenAI-compatible API for all providers.
"""

import os

from agno.models.openai import OpenAIChat
from agno.models.openai.like import OpenAILike

from majordomo_frameworks import (
    PROVIDER_DEFAULTS,
    Provider,
    build_headers,
    get_gateway_url,
)

AgnoModel = OpenAIChat | OpenAILike


def create_openai_model(
    model_id: str = "gpt-4o",
    *,
    feature: str | None = None,
    step: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> OpenAIChat:
    """Create an OpenAI model routed through the gateway."""
    headers = build_headers(
        feature=feature, step=step, user_id=user_id, session_id=session_id
    )
    if extra_headers:
        headers.update(extra_headers)
    return OpenAIChat(
        id=model_id,
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=f"{get_gateway_url()}/v1",
        extra_headers=headers,
    )


def create_anthropic_model(
    model_id: str = "claude-sonnet-4-20250514",
    *,
    feature: str | None = None,
    step: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> OpenAILike:
    """Create an Anthropic model routed through the gateway.

    Uses OpenAILike since we're going through the gateway's OpenAI-compatible API.
    The gateway translates OpenAI format to Anthropic format and back.
    """
    headers = build_headers(
        provider_header="anthropic-openai",
        feature=feature,
        step=step,
        user_id=user_id,
        session_id=session_id,
    )
    if extra_headers:
        headers.update(extra_headers)
    return OpenAILike(
        id=model_id,
        api_key=os.environ["ANTHROPIC_API_KEY"],
        base_url=f"{get_gateway_url()}/v1",
        extra_headers=headers,
    )


def create_gemini_model(
    model_id: str = "gemini-2.0-flash",
    *,
    feature: str | None = None,
    step: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> OpenAILike:
    """Create a Gemini model routed through the gateway.

    Uses OpenAILike via Gemini's OpenAI-compatible endpoint.
    The X-Majordomo-Provider header tells the gateway to route to Gemini.
    """
    headers = build_headers(
        provider_header="gemini-openai",
        feature=feature,
        step=step,
        user_id=user_id,
        session_id=session_id,
    )
    if extra_headers:
        headers.update(extra_headers)
    return OpenAILike(
        id=model_id,
        api_key=os.environ["GEMINI_API_KEY"],
        base_url=f"{get_gateway_url()}/v1",
        extra_headers=headers,
    )


def create_model(
    provider: Provider,
    model_id: str | None = None,
    *,
    feature: str | None = None,
    step: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> AgnoModel:
    """Create a model for the specified provider, routed through the gateway.

    Args:
        provider: The LLM provider ("openai", "anthropic", or "gemini")
        model_id: Model ID (uses sensible defaults if not specified)
        feature: Feature name for cost attribution
        step: Workflow step for granular tracking
        user_id: User ID for per-user cost tracking
        session_id: Session ID for conversation tracking
        extra_headers: Additional headers to include in requests

    Returns:
        An Agno model configured to route through Majordomo Gateway
    """
    id_ = model_id or PROVIDER_DEFAULTS[provider]
    kwargs = dict(
        feature=feature,
        step=step,
        user_id=user_id,
        session_id=session_id,
        extra_headers=extra_headers,
    )

    match provider:
        case "openai":
            return create_openai_model(id_, **kwargs)
        case "anthropic":
            return create_anthropic_model(id_, **kwargs)
        case "gemini":
            return create_gemini_model(id_, **kwargs)
