"""Shared utilities for routing LLM requests through Majordomo Gateway."""

import os
from typing import Literal

Provider = Literal["openai", "anthropic", "gemini"]

PROVIDER_DEFAULTS: dict[str, str] = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-20250514",
    "gemini": "gemini-2.0-flash",
}


def get_gateway_url() -> str:
    """Get the Majordomo Gateway URL from environment."""
    return os.environ.get("MAJORDOMO_GATEWAY_URL", "http://localhost:7680")


def get_majordomo_key() -> str:
    """Get the Majordomo API key from environment."""
    key = os.environ.get("MAJORDOMO_API_KEY")
    if not key:
        raise ValueError("MAJORDOMO_API_KEY environment variable is required")
    return key


def build_headers(
    *,
    provider_header: str | None = None,
    feature: str | None = None,
    step: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, str]:
    """Build Majordomo headers for request tracking.

    Args:
        provider_header: X-Majordomo-Provider value (for routing)
        feature: Feature name for cost attribution
        step: Workflow step for granular tracking
        user_id: User ID for per-user cost tracking
        session_id: Session ID for conversation tracking
    """
    headers = {"X-Majordomo-Key": get_majordomo_key()}

    if provider_header:
        headers["X-Majordomo-Provider"] = provider_header
    if feature:
        headers["X-Majordomo-Feature"] = feature
    if step:
        headers["X-Majordomo-Step"] = step
    if user_id:
        headers["X-Majordomo-User-Id"] = user_id
    if session_id:
        headers["X-Majordomo-Session-Id"] = session_id

    return headers


def check_environment(provider: Provider) -> list[str]:
    """Check that required environment variables are set for a provider.

    Args:
        provider: The LLM provider to check

    Returns:
        List of missing environment variable names (empty if all set)
    """
    required = ["MAJORDOMO_API_KEY"]

    match provider:
        case "openai":
            required.append("OPENAI_API_KEY")
        case "anthropic":
            required.append("ANTHROPIC_API_KEY")
        case "gemini":
            required.append("GEMINI_API_KEY")

    return [var for var in required if not os.environ.get(var)]
