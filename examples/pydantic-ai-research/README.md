# Pydantic AI + Majordomo Gateway

This example demonstrates using [Pydantic AI](https://ai.pydantic.dev/) with Majordomo Gateway for centralized LLM request logging and cost tracking across multiple providers.

## Features

- **Multi-provider support**: OpenAI, Anthropic, and Gemini through a unified interface
- **Tool calling**: Web search via Tavily API with requests logged through the gateway
- **Structured outputs**: Pydantic models for type-safe responses
- **Cost attribution**: Track costs by feature and workflow step

## Project Structure

```
main.py                 # CLI entry point (Click)
src/
├── models.py           # Pydantic models for structured outputs
├── tools.py            # Web search tool (Tavily integration)
└── research_agent.py   # Research agent with multi-step workflow
```

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Majordomo Gateway running ([setup guide](https://github.com/superset-studio/majordomo-gateway/blob/main/docs/getting-started.md))
- API keys for your chosen provider(s)

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Create a `.env` file with your API keys:
   ```bash
   cp ../.env.example .env
   ```

   Required variables:
   ```
   MAJORDOMO_GATEWAY_URL=http://localhost:7680
   MAJORDOMO_API_KEY=mdm_sk_...

   # Add keys for providers you want to use
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   GEMINI_API_KEY=...

   # Optional: for real web search (falls back to mock if not set)
   TAVILY_API_KEY=tvly-...
   ```

## Usage

Run the research agent with your preferred provider:

```bash
# OpenAI (default)
uv run python main.py "Impact of AI on software development"

# Anthropic
uv run python main.py --provider anthropic "Impact of AI on software development"

# Gemini
uv run python main.py --provider gemini "Impact of AI on software development"

# Specify a model
uv run python main.py --provider openai --model gpt-4o-mini "Your topic"
```

## How It Works

### Gateway Integration

Models are configured to route through the gateway, with headers passed via model settings:

```python
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
from majordomo_frameworks.pydantic_ai import create_model, build_extra_headers

# Create model routed through the gateway
model = create_model("openai")

# Build headers for model settings
headers = build_extra_headers(feature="research-agent", step="synthesis")
settings = ModelSettings(extra_headers=headers)

# Use headers when running the agent
agent = Agent(model=model, ...)
result = await agent.run("prompt", model_settings=settings)
```

This pattern lets you use all Pydantic AI model settings (thinking, caching, etc.) alongside Majordomo headers.

### Workflow Steps

The research agent runs a two-step workflow:

1. **Query Generation** - LLM generates search queries for the topic
2. **Synthesis** - LLM analyzes search results and produces a report

Each step is tagged with `X-Majordomo-Step` for granular cost tracking.

## Viewing Logs

After running, query the gateway database:

```sql
-- Costs by workflow step
SELECT
    model,
    raw_metadata->>'Step' as step,
    input_tokens,
    output_tokens,
    total_cost
FROM llm_requests
WHERE raw_metadata->>'Feature' = 'research-agent'
ORDER BY created_at DESC;

-- Compare providers
SELECT
    provider,
    COUNT(*) as requests,
    SUM(total_cost) as total_cost
FROM llm_requests
WHERE raw_metadata->>'Feature' = 'research-agent'
GROUP BY provider;
```
