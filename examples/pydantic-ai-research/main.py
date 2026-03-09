"""CLI entry point for running the research agent example.

Usage:
    uv run python main.py "Your research topic"
    uv run python main.py --provider anthropic "Your research topic"
    uv run python main.py --provider gemini "Your research topic"
"""

import asyncio
import os
import sys

import click
from dotenv import load_dotenv
from src.research_agent import ResearchAgent

from majordomo_frameworks import check_environment


def check_extra_environment() -> list[str]:
    """Check for additional environment variables beyond provider requirements."""
    missing = []
    if not os.environ.get("TAVILY_API_KEY"):
        missing.append("TAVILY_API_KEY")
    return missing


def print_report(report) -> None:
    """Pretty-print a research report."""
    click.echo("\n" + "=" * 70)
    click.echo("RESEARCH REPORT")
    click.echo("=" * 70)
    click.echo(f"\n{report.title}")
    click.echo("-" * 70)
    click.echo(f"\n{report.summary}")
    click.echo("\nKey Findings:")
    for i, finding in enumerate(report.key_findings, 1):
        click.echo(f"  {i}. {finding}")
    click.echo(f"\nSources consulted: {report.sources_used}")
    click.echo(f"Confidence: {report.confidence}")
    click.echo("=" * 70)


@click.command()
@click.argument("topic")
@click.option(
    "--provider",
    type=click.Choice(["openai", "anthropic", "gemini"]),
    default="openai",
    help="LLM provider to use.",
)
@click.option(
    "--model",
    type=str,
    default=None,
    help="Specific model name (uses provider default if not specified).",
)
def main(topic: str, provider: str, model: str | None) -> None:
    """Research agent powered by Majordomo Gateway.

    Generates search queries, executes web searches, and synthesizes a
    research report for the given TOPIC.
    """
    load_dotenv()

    # Check environment
    missing = check_environment(provider) + check_extra_environment()
    if missing:
        click.echo(f"Error: Missing environment variables: {', '.join(missing)}", err=True)
        click.echo("\nSet them in your environment or create a .env file:", err=True)
        click.echo("  cp ../.env.example .env", err=True)
        sys.exit(1)

    # Run research
    click.echo(f"\nUsing provider: {provider}")
    if model:
        click.echo(f"Using model: {model}")
    click.echo(f"Researching: {topic}")
    click.echo("-" * 70)

    asyncio.run(run_research(topic, provider, model))


async def run_research(topic: str, provider: str, model: str | None) -> None:
    """Execute the research workflow."""
    agent = ResearchAgent(provider=provider, model_name=model)

    click.echo("\n[Step 1] Generating search queries...", nl=False)
    queries = await agent.generate_queries(topic)
    click.echo(f"\n  Generated {len(queries.queries)} queries")

    click.echo("[Step 2] Executing web searches...", nl=False)
    search_results = agent.execute_searches(queries.queries)
    click.echo(f"\n  Found {len(search_results)} results")

    click.echo("[Step 3] Synthesizing research report...", nl=False)
    report = await agent.synthesize(topic, search_results)
    print_report(report)

    # Show how to query logs
    click.echo("\nView your gateway logs:")
    click.echo('  psql -d majordomo -c "SELECT model, raw_metadata->>\'Step\' as step, total_cost')
    click.echo("    FROM llm_requests")
    click.echo("    WHERE raw_metadata->>'Feature' = 'research-agent'")
    click.echo('    ORDER BY created_at DESC LIMIT 10;"')


if __name__ == "__main__":
    main()
