# Agno + Majordomo Gateway

This example demonstrates using [Agno](https://docs.agno.com/) with Majordomo Gateway for multi-turn conversations with per-user cost tracking.

## Features

- **Multi-turn conversations**: Agent remembers context within a session
- **Multi-provider support**: OpenAI, Anthropic, and Gemini
- **Per-user cost tracking**: Costs attributed via `X-Majordomo-User-Id`

## Project Structure

```
src/
├── support_agent.py    # Support agent with conversation memory
└── main.py             # CLI entry point
```

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- Majordomo Gateway running ([setup guide](https://github.com/superset-studio/majordomo-gateway/blob/main/docs/getting-started.md))
- API keys for your chosen provider(s)

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Create a `.env` file:
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
   ```

## Usage

### Interactive mode (recommended)

```bash
uv run python -m src.main --user alice --interactive
```

This starts a multi-turn conversation where the agent remembers previous messages.

### Single message

```bash
uv run python -m src.main --user alice "Hi, I need help with billing"
```

### Different providers

```bash
uv run python -m src.main --provider anthropic --user alice --interactive
uv run python -m src.main --provider gemini --user bob --interactive
```

## How It Works

### Gateway Integration

Models are configured with user metadata for cost attribution:

```python
from majordomo_frameworks.agno import create_model

model = create_model(
    "openai",
    feature="support-agent",
    user_id="alice",
    session_id="alice-session",
)
```

This adds headers to every request:
- `X-Majordomo-Key`: Your gateway API key
- `X-Majordomo-Feature`: Feature name for cost grouping
- `X-Majordomo-User-Id`: User identifier for per-user tracking
- `X-Majordomo-Session-Id`: Session identifier

### Conversation Memory

The agent maintains conversation history in memory using Agno's `add_history_to_context=True`. Within an interactive session, the agent remembers previous messages.

## Viewing Logs

Query per-user costs:

```sql
SELECT
    raw_metadata->>'User-Id' as user_id,
    COUNT(*) as requests,
    SUM(total_cost) as total_cost
FROM llm_requests
WHERE raw_metadata->>'Feature' = 'support-agent'
GROUP BY 1
ORDER BY total_cost DESC;
```
