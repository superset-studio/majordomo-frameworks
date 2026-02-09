# majordomo-frameworks

Framework adapters for routing LLM requests through [Majordomo Gateway](https://github.com/superset-studio/majordomo-oss/tree/main/majordomo-gateway) with centralized logging and cost tracking.

## Installation

```bash
# Core package (no framework dependencies)
pip install majordomo-frameworks

# With Agno support
pip install majordomo-frameworks[agno]

# With Pydantic AI support
pip install majordomo-frameworks[pydantic-ai]
```

## Quick Start

### Shared utilities (zero dependencies)

```python
from majordomo_frameworks import build_headers, check_environment, Provider

# Check required env vars are set
missing = check_environment("openai")

# Build gateway headers
headers = build_headers(feature="my-feature", step="inference", user_id="alice")
```

### Agno

```python
from majordomo_frameworks.agno import create_model

model = create_model("openai", feature="support-agent", user_id="alice")
```

### Pydantic AI

```python
from majordomo_frameworks.pydantic_ai import create_model, build_extra_headers
from pydantic_ai.settings import AnthropicModelSettings

# Create model routed through the gateway
model = create_model("anthropic")

# Build headers for model settings
headers = build_extra_headers(feature="research-agent", step="synthesis")

# Use with Pydantic AI model settings
settings = AnthropicModelSettings(
    extra_headers=headers,
    # ... other settings like anthropic_thinking, etc.
)
```

## Supported Providers

| Provider | Agno | Pydantic AI |
|----------|------|-------------|
| OpenAI | `OpenAIChat` | `OpenAIModel` |
| Anthropic | `OpenAILike` | `AnthropicModel` |
| Gemini | `OpenAILike` | `OpenAIModel` |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MAJORDOMO_GATEWAY_URL` | No | Gateway URL (default: `http://localhost:7680`) |
| `MAJORDOMO_API_KEY` | Yes | Your Majordomo API key |
| `OPENAI_API_KEY` | Per provider | OpenAI API key |
| `ANTHROPIC_API_KEY` | Per provider | Anthropic API key |
| `GEMINI_API_KEY` | Per provider | Gemini API key |

## Documentation

- [**Pydantic AI Guide**](docs/pydantic-ai-guide.md) - Complete guide with migration instructions, advanced usage, and examples

## Examples

- [Agno Support Agent](examples/agno-support-agent/) - Multi-turn conversations with per-user cost tracking
- [Pydantic AI Research Agent](examples/pydantic-ai-research/) - Multi-step research workflow with structured outputs

## License

MIT