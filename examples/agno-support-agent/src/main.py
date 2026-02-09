"""CLI entry point for the Agno support agent example.

This example demonstrates:
- Multi-turn conversations with in-memory history
- Cost tracking per user via X-Majordomo-User-Id
- Gateway integration with multiple providers

Usage:
    # Single message
    uv run python -m src.main --user alice "Hi, I need help with my account"

    # Interactive mode (recommended - shows multi-turn memory)
    uv run python -m src.main --user alice --interactive

    # Different providers
    uv run python -m src.main --provider anthropic --user bob --interactive
"""

import argparse
import sys

from dotenv import load_dotenv

from majordomo_frameworks import Provider, check_environment
from src.support_agent import SupportSession


def interactive_mode(session: SupportSession) -> None:
    """Run an interactive chat session."""
    print("\nInteractive support session (type 'quit' to exit)")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("\nGoodbye!")
            break

        response = session.chat(user_input)
        print(f"\nAgent: {response}")


def main() -> int:
    """Run the support agent."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Customer support agent powered by Majordomo Gateway"
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="Message to send (omit for --interactive)",
    )
    parser.add_argument(
        "--user",
        type=str,
        required=True,
        help="User ID for cost tracking",
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
        help="Specific model ID (uses provider default if not specified)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start an interactive chat session",
    )
    args = parser.parse_args()

    if not args.message and not args.interactive:
        parser.error("Provide a message or use --interactive")

    missing = check_environment(args.provider)
    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        print("\nSet them in your environment or create a .env file:")
        print("  cp ../.env.example .env")
        return 1

    print(f"Provider: {args.provider}")
    print(f"User: {args.user}")

    session = SupportSession(
        provider=args.provider,
        model_id=args.model,
        user_id=args.user,
    )

    if args.interactive:
        interactive_mode(session)
    else:
        print(f"\nYou: {args.message}")
        print("-" * 50)
        response = session.chat(args.message)
        print(f"\nAgent: {response}")

    # Show how to query logs
    print("\n" + "-" * 50)
    print("View per-user costs in your gateway logs:")
    print('  psql -d majordomo -c "SELECT')
    print("      raw_metadata->>'User-Id' as user_id,")
    print("      COUNT(*) as requests,")
    print("      SUM(total_cost) as total_cost")
    print("    FROM llm_requests")
    print("    WHERE raw_metadata->>'Feature' = 'support-agent'")
    print('    GROUP BY 1;"')

    return 0


if __name__ == "__main__":
    sys.exit(main())
