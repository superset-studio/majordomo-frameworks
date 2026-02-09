# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
# Install dependencies (includes dev extras)
uv sync --all-extras

# Linting
uv run ruff check src/majordomo_frameworks

# Fix linting issues
uv run ruff check --fix src/majordomo_frameworks

# Quick smoke test
uv run python -c "from majordomo_frameworks import build_headers, Provider, check_environment"
```

## Architecture

Framework adapters that route LLM requests through Majordomo Gateway for centralized logging and cost tracking. Supports Agno and Pydantic AI frameworks.

### Core Components

- **`core.py`**: Shared utilities used by all adapters. `Provider` literal type (`"openai" | "anthropic" | "gemini"`), `build_headers()` for constructing `X-Majordomo-*` tracking headers, `check_environment()` for validating required env vars, `get_gateway_url()` / `get_majordomo_key()` helpers.

- **`agno.py`**: Agno framework adapter (requires `[agno]` extra). Factory functions (`create_model`, `create_openai_model`, `create_anthropic_model`, `create_gemini_model`) that return Agno `OpenAIChat` or `OpenAILike` models configured to route through the gateway. All providers use OpenAI-compatible API via the gateway.

- **`pydantic_ai.py`**: Pydantic AI framework adapter (requires `[pydantic-ai]` extra). Factory functions (`create_model`, `create_openai_model`, `create_anthropic_model`, `create_gemini_model`) return models configured with gateway `base_url`. Header functions (`build_extra_headers`, `build_extra_headers_gemini`) return dicts for use in `AnthropicModelSettings` or `OpenAIChatModelSettings` `extra_headers` field. This pattern allows full use of Pydantic AI model settings (thinking, caching, etc.).

- **`__init__.py`**: Re-exports core utilities (`Provider`, `build_headers`, `check_environment`, `get_gateway_url`, `get_majordomo_key`, `PROVIDER_DEFAULTS`).

### Key Patterns

- Zero dependencies in core — framework-specific deps are optional extras (`[agno]`, `[pydantic-ai]`)
- Agno adapter bakes headers into the model at creation time (simpler API)
- Pydantic AI adapter separates model creation from headers — models get `base_url`, headers go in model settings `extra_headers` (idiomatic Pydantic AI pattern, supports full model settings like thinking/caching)
- Provider routing: OpenAI goes directly; Anthropic and Gemini use `X-Majordomo-Provider` header to tell the gateway which upstream to use
- `PROVIDER_DEFAULTS` maps each provider to a sensible default model ID
- `check_environment()` validates required env vars before making requests

### Environment Variables

- `MAJORDOMO_GATEWAY_URL` — Gateway URL (default: `http://localhost:7680`)
- `MAJORDOMO_API_KEY` — Majordomo API key (required)
- `OPENAI_API_KEY` — OpenAI API key (when using OpenAI provider)
- `ANTHROPIC_API_KEY` — Anthropic API key (when using Anthropic provider)
- `GEMINI_API_KEY` — Gemini API key (when using Gemini provider)

### Examples

- `examples/agno-support-agent/` — Multi-turn conversations with per-user cost tracking using Agno
- `examples/pydantic-ai-research/` — Multi-step research workflow with structured outputs using Pydantic AI

Each example has its own `pyproject.toml` and `README.md`. Run with `uv sync && uv run python -m src.main`.
