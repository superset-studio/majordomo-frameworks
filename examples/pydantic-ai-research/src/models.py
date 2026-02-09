"""Pydantic models for structured agent outputs."""

from pydantic import BaseModel, Field


class SearchQueries(BaseModel):
    """Generated search queries for a research topic."""

    queries: list[str] = Field(
        ...,
        description="List of 3-5 specific search queries to research the topic",
        min_length=3,
        max_length=5,
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation of why these queries will help research the topic",
    )


class ResearchReport(BaseModel):
    """Final synthesized research report."""

    title: str = Field(..., description="Title for the research report")
    summary: str = Field(
        ..., description="Executive summary of findings (2-3 sentences)"
    )
    key_findings: list[str] = Field(
        ...,
        description="List of 3-5 key findings from the research",
        min_length=3,
        max_length=5,
    )
    sources_used: int = Field(..., description="Number of sources consulted")
    confidence: str = Field(
        ..., description="Confidence level: high, medium, or low"
    )
