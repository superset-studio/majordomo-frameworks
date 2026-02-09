"""Customer support agent with conversation memory.

This agent demonstrates:
- Multi-turn conversations with in-memory history
- Per-user cost tracking via X-Majordomo-User-Id
- Gateway integration with Agno
"""

from agno.agent import Agent

from majordomo_frameworks import Provider
from majordomo_frameworks.agno import create_model

FEATURE_NAME = "support-agent"


def create_support_agent(
    provider: Provider,
    model_id: str | None = None,
    *,
    user_id: str,
    session_id: str,
) -> Agent:
    """Create a customer support agent.

    The agent:
    - Maintains conversation history in memory
    - Routes all LLM costs to the user via gateway metadata

    Args:
        provider: LLM provider ("openai", "anthropic", or "gemini")
        model_id: Specific model ID (uses provider default if not specified)
        user_id: Unique user identifier for cost tracking
        session_id: Session identifier for tracking
    """
    model = create_model(
        provider,
        model_id,
        feature=FEATURE_NAME,
        user_id=user_id,
        session_id=session_id,
    )

    return Agent(
        model=model,
        session_id=session_id,
        user_id=user_id,
        description="You are a helpful customer support agent.",
        instructions=[
            "Help customers with their questions and issues.",
            "Be friendly, professional, and concise.",
            "Reference earlier parts of the conversation when relevant.",
            "If you can't help, offer to escalate to a human agent.",
        ],
        markdown=True,
    )


class SupportSession:
    """Manages a customer support session."""

    def __init__(
        self,
        provider: Provider = "openai",
        model_id: str | None = None,
        *,
        user_id: str,
        session_id: str | None = None,
    ):
        """Initialize a support session.

        Args:
            provider: LLM provider to use
            model_id: Specific model ID (optional)
            user_id: Unique user identifier
            session_id: Session ID (defaults to user_id if not provided)
        """
        self.provider = provider
        self.model_id = model_id
        self.user_id = user_id
        self.session_id = session_id or f"{user_id}-session"

        self.agent = create_support_agent(
            provider=provider,
            model_id=model_id,
            user_id=user_id,
            session_id=self.session_id,
        )

    def chat(self, message: str) -> str:
        """Send a message and get a response.

        Args:
            message: The user's message

        Returns:
            The agent's response
        """
        response = self.agent.run(message)
        return response.content
