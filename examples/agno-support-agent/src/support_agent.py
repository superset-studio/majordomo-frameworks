"""Multi-step customer support agent with structured outputs.

This agent demonstrates:
- Multi-step workflows: classify → respond → summarize
- Structured outputs via Pydantic models (IntentClassification, TicketSummary)
- Per-step cost tracking via X-Majordomo-Step
- Per-user cost tracking via X-Majordomo-User-Id
- Custom metadata via extra_headers (X-Majordomo-Example-Framework)
"""

from agno.agent import Agent

from majordomo_frameworks import Provider
from majordomo_frameworks.agno import create_model
from src.models import IntentClassification, TicketSummary

FEATURE_NAME = "support-agent"
EXTRA_HEADERS = {"X-Majordomo-Example-Framework": "agno"}


def _create_classifier_agent(
    provider: Provider,
    model_id: str | None,
    *,
    user_id: str,
    session_id: str,
) -> Agent:
    """Create an agent that classifies customer intent."""
    model = create_model(
        provider,
        model_id,
        feature=FEATURE_NAME,
        step="classify",
        user_id=user_id,
        session_id=session_id,
        extra_headers=EXTRA_HEADERS,
    )
    return Agent(
        model=model,
        output_schema=IntentClassification,
        use_json_mode=True,
        description="You classify customer support messages.",
        instructions=[
            "Classify the customer's message into a category and urgency level.",
            "Categories: billing, technical, account, general.",
            "Urgency: low (general inquiry), medium (issue affecting usage),"
            " high (service down or security concern).",
            "Provide a one-sentence summary of the customer's intent.",
        ],
    )


def _create_support_agent(
    provider: Provider,
    model_id: str | None,
    *,
    user_id: str,
    session_id: str,
) -> Agent:
    """Create a support agent that responds to customer messages."""
    model = create_model(
        provider,
        model_id,
        feature=FEATURE_NAME,
        step="respond",
        user_id=user_id,
        session_id=session_id,
        extra_headers=EXTRA_HEADERS,
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


def _create_summary_agent(
    provider: Provider,
    model_id: str | None,
    *,
    user_id: str,
    session_id: str,
) -> Agent:
    """Create an agent that summarizes a support session into a ticket."""
    model = create_model(
        provider,
        model_id,
        feature=FEATURE_NAME,
        step="summarize",
        user_id=user_id,
        session_id=session_id,
        extra_headers=EXTRA_HEADERS,
    )
    return Agent(
        model=model,
        output_schema=TicketSummary,
        use_json_mode=True,
        description="You summarize customer support sessions into structured tickets.",
        instructions=[
            "Review the full conversation and create a support ticket summary.",
            "Set priority based on urgency and impact: low, medium, high, or critical.",
            "Include concrete suggested actions for the support team.",
            "The description should capture both the issue and any resolution provided.",
        ],
    )


class SupportSession:
    """Orchestrates a multi-step customer support session.

    Each interaction:
    1. Classifies the customer's intent (structured output)
    2. Generates a support response (informed by classification)

    At session end:
    3. Summarizes the full conversation into a structured ticket
    """

    def __init__(
        self,
        provider: Provider = "openai",
        model_id: str | None = None,
        *,
        user_id: str,
        session_id: str | None = None,
    ):
        self.user_id = user_id
        self.session_id = session_id or f"{user_id}-session"
        self.history: list[dict[str, str]] = []

        self.classifier = _create_classifier_agent(
            provider, model_id, user_id=user_id, session_id=self.session_id
        )
        self.support = _create_support_agent(
            provider, model_id, user_id=user_id, session_id=self.session_id
        )
        self.summarizer = _create_summary_agent(
            provider, model_id, user_id=user_id, session_id=self.session_id
        )

    def classify(self, message: str) -> IntentClassification:
        """Classify a customer message."""
        response = self.classifier.run(message)
        return response.content

    def respond(self, message: str, classification: IntentClassification) -> str:
        """Generate a support response informed by the classification.

        The classification context is prepended to the message so the support
        agent can tailor its response appropriately.
        """
        context = (
            f"[Internal context — category: {classification.category}, "
            f"urgency: {classification.urgency}, "
            f"intent: {classification.summary}]\n\n"
            f"Customer message: {message}"
        )
        response = self.support.run(context)
        content = response.content
        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": content})
        return content

    def chat(self, message: str) -> tuple[IntentClassification, str]:
        """Process a customer message: classify then respond.

        Returns:
            Tuple of (classification, response text)
        """
        classification = self.classify(message)
        response = self.respond(message, classification)
        return classification, response

    def summarize(self) -> TicketSummary:
        """Summarize the full session into a structured ticket."""
        conversation = "\n".join(
            f"{turn['role'].upper()}: {turn['content']}" for turn in self.history
        )
        response = self.summarizer.run(
            f"Summarize this support conversation:\n\n{conversation}"
        )
        return response.content
