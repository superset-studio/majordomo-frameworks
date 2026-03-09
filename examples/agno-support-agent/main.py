"""CLI entry point for the Agno support agent example.

This example demonstrates:
- Multi-step workflows: classify → respond → summarize
- Structured outputs (IntentClassification, TicketSummary)
- Per-step and per-user cost tracking via Majordomo Gateway

Usage:
    uv run python main.py --user alice "Hi, I need help with my account"
    uv run python main.py --user alice --interactive
    uv run python main.py --provider anthropic --user bob --interactive
"""

import sys

import click
from dotenv import load_dotenv
from src.support_agent import SupportSession

from majordomo_frameworks import check_environment


def interactive_mode(session: SupportSession) -> None:
    """Run an interactive chat session."""
    click.echo("\nInteractive support session (type 'quit' to exit)")
    click.echo("-" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo("\n")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            break

        classification, response = session.chat(user_input)
        click.echo(
            f"  [{classification.category} | {classification.urgency}]"
            f" {classification.summary}"
        )
        click.echo(f"\nAgent: {response}")

    # Summarize the session into a structured ticket
    if session.history:
        click.echo("\n" + "=" * 50)
        click.echo("TICKET SUMMARY")
        click.echo("=" * 50)
        summary = session.summarize()
        click.echo(f"\nTitle: {summary.title}")
        click.echo(f"Category: {summary.category}")
        click.echo(f"Priority: {summary.priority}")
        click.echo(f"\n{summary.description}")
        click.echo("\nSuggested Actions:")
        for i, action in enumerate(summary.suggested_actions, 1):
            click.echo(f"  {i}. {action}")

    click.echo("\nGoodbye!")


@click.command()
@click.argument("message", required=False)
@click.option(
    "--user",
    required=True,
    help="User ID for cost tracking.",
)
@click.option(
    "--provider",
    type=click.Choice(["openai", "anthropic", "gemini"]),
    default="openai",
    help="LLM provider to use.",
)
@click.option(
    "--model",
    default=None,
    help="Specific model ID (uses provider default if not specified).",
)
@click.option(
    "--interactive",
    is_flag=True,
    help="Start an interactive chat session.",
)
def main(
    message: str | None,
    user: str,
    provider: str,
    model: str | None,
    interactive: bool,
) -> None:
    """Customer support agent powered by Majordomo Gateway.

    Classifies intent, generates responses, and summarizes sessions
    into structured tickets — all with per-step cost tracking.
    """
    load_dotenv()

    if not message and not interactive:
        click.echo("Error: Provide a message or use --interactive", err=True)
        sys.exit(1)

    missing = check_environment(provider)
    if missing:
        click.echo(f"Error: Missing environment variables: {', '.join(missing)}", err=True)
        click.echo("\nSet them in your environment or create a .env file:", err=True)
        click.echo("  cp ../.env.example .env", err=True)
        sys.exit(1)

    click.echo(f"Provider: {provider}")
    click.echo(f"User: {user}")

    session = SupportSession(
        provider=provider,
        model_id=model,
        user_id=user,
    )

    if interactive:
        interactive_mode(session)
    else:
        click.echo(f"\nYou: {message}")
        click.echo("-" * 50)
        classification, response = session.chat(message)
        click.echo(
            f"  [{classification.category} | {classification.urgency}]"
            f" {classification.summary}"
        )
        click.echo(f"\nAgent: {response}")

    # Show how to query logs
    click.echo("\n" + "-" * 50)
    click.echo("View per-step costs in your gateway logs:")
    click.echo('  psql -d majordomo -c "SELECT')
    click.echo("      raw_metadata->>'Step' as step,")
    click.echo("      COUNT(*) as requests,")
    click.echo("      SUM(total_cost) as total_cost")
    click.echo("    FROM llm_requests")
    click.echo("    WHERE raw_metadata->>'Feature' = 'support-agent'")
    click.echo('    GROUP BY 1;"')


if __name__ == "__main__":
    main()
