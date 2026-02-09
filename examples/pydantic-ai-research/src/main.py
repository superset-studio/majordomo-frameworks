"""CLI entry point for running the research agent example.

Usage:
    uv run python -m src.main --provider openai "Your research topic"
    uv run python -m src.main --provider anthropic "Your research topic"
    uv run python -m src.main --provider gemini "Your research topic"
"""

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

from majordomo_frameworks import check_environment
from src.research_agent import ResearchAgent


def check_extra_environment() -> list[str]:
    """Check for additional environment variables beyond provider requirements."""
    missing = []
    if not os.environ.get("TAVILY_API_KEY"):
        missing.append("TAVILY_API_KEY")
    return missing


def print_report(report) -> None:
    """Pretty-print a research report."""
    print("\n" + "=" * 70)
    print("RESEARCH REPORT")
    print("=" * 70)
    print(f"\n{report.title}")
    print("-" * 70)
    print(f"\n{report.summary}")
    print("\nKey Findings:")
    for i, finding in enumerate(report.key_findings, 1):
        print(f"  {i}. {finding}")
    print(f"\nSources consulted: {report.sources_used}")
    print(f"Confidence: {report.confidence}")
    print("=" * 70)


async def main() -> int:
    """Run the research agent."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Research agent powered by Majordomo Gateway"
    )
    parser.add_argument(
        "topic",
        help="The topic to research",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "anthropic", "gemini"],
        default="openai",
        help="LLM provider to use (default: openai)",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Specific model name (uses provider default if not specified)",
    )
    args = parser.parse_args()

    # Check environment
    missing = check_environment(args.provider) + check_extra_environment()
    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        print("\nSet them in your environment or create a .env file:")
        print("  cp ../.env.example .env")
        return 1

    # Run research
    print(f"\nUsing provider: {args.provider}")
    if args.model:
        print(f"Using model: {args.model}")
    print(f"Researching: {args.topic}")
    print("-" * 70)

    agent = ResearchAgent(provider=args.provider, model_name=args.model)

    print("\n[Step 1] Generating search queries...", flush=True)
    queries = await agent.generate_queries(args.topic)
    print(f"  Generated {len(queries.queries)} queries")

    print("[Step 2] Executing web searches...", flush=True)
    search_results = agent.execute_searches(queries.queries)
    print(f"  Found {len(search_results)} results")

    print("[Step 3] Synthesizing research report...", flush=True)
    report = await agent.synthesize(args.topic, search_results)
    print_report(report)

    # Show how to query logs
    print("\nView your gateway logs:")
    print("  psql -d majordomo -c \"SELECT model, raw_metadata->>'Step' as step, total_cost")
    print("    FROM llm_requests")
    print("    WHERE raw_metadata->>'Feature' = 'research-agent'")
    print("    ORDER BY created_at DESC LIMIT 10;\"")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
