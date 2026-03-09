# Agno + Majordomo Gateway

This example demonstrates using [Agno](https://docs.agno.com/) with Majordomo Gateway for multi-step support workflows with structured outputs and per-step cost tracking.

## Features

- **Multi-step workflow**: Classify intent → generate response → summarize session
- **Structured outputs**: `IntentClassification` and `TicketSummary` via Pydantic models
- **Per-step cost tracking**: Each step (classify, respond, summarize) is tracked separately
- **Multi-provider support**: OpenAI, Anthropic, and Gemini
- **Per-user cost tracking**: Costs attributed via `X-Majordomo-User-Id`

## Project Structure

```
main.py                # CLI entry point (Click)
src/
├── models.py          # Pydantic models (IntentClassification, TicketSummary)
└── support_agent.py   # Multi-step support agent with SupportSession
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
uv run python main.py --user alice --interactive
```

This starts a multi-turn session where each message is classified, a response is generated, and when you quit the full session is summarized into a structured ticket.

### Single message

```bash
uv run python main.py --user alice "Hi, I need help with billing"
```

### Different providers

```bash
uv run python main.py --provider anthropic --user alice --interactive
uv run python main.py --provider gemini --user bob --interactive
```

## How It Works

### Three-Step Workflow

Each customer message goes through:

1. **Classify** (`step=classify`): Determines category (billing/technical/account/general) and urgency (low/medium/high) using structured output
2. **Respond** (`step=respond`): Generates a support response informed by the classification
3. **Summarize** (`step=summarize`): At session end, produces a `TicketSummary` with title, priority, description, and suggested actions

### Gateway Integration

Each step creates a separate model with its own `X-Majordomo-Step` header:

```python
from majordomo_frameworks.agno import create_model

model = create_model(
    "openai",
    feature="support-agent",
    step="classify",
    user_id="alice",
    session_id="alice-session",
    extra_headers={"X-Majordomo-Example-Framework": "agno"},
)
```

This enables per-step cost analysis in your gateway logs.

## Viewing Logs

Query per-step costs:

```sql
SELECT
    raw_metadata->>'Step' as step,
    COUNT(*) as requests,
    SUM(total_cost) as total_cost
FROM llm_requests
WHERE raw_metadata->>'Feature' = 'support-agent'
GROUP BY 1
ORDER BY step;
```
