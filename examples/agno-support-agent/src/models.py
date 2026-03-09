"""Pydantic models for structured agent outputs."""

from pydantic import BaseModel, Field


class IntentClassification(BaseModel):
    """Classification of a customer support message."""

    category: str = Field(
        ...,
        description="Support category: billing, technical, account, or general",
    )
    urgency: str = Field(
        ...,
        description="Urgency level: low, medium, or high",
    )
    summary: str = Field(
        ...,
        description="One-sentence summary of the customer's intent",
    )


class TicketSummary(BaseModel):
    """Structured summary of a support session for ticket creation."""

    title: str = Field(..., description="Short title for the support ticket")
    category: str = Field(
        ...,
        description="Support category: billing, technical, account, or general",
    )
    priority: str = Field(
        ...,
        description="Priority level: low, medium, high, or critical",
    )
    description: str = Field(
        ...,
        description="Detailed description of the issue and resolution",
    )
    suggested_actions: list[str] = Field(
        ...,
        description="List of suggested follow-up actions",
        min_length=1,
        max_length=5,
    )
