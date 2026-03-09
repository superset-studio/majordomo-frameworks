"""Research agent that uses web search to gather and synthesize information.

This agent demonstrates:
- Tool calling (web search) through Majordomo Gateway
- Multi-step workflows with separate logging per step
- Structured output with Pydantic models
- Using build_extra_headers with model settings
"""

from dataclasses import dataclass, field

from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings

from majordomo_frameworks import Provider
from majordomo_frameworks.pydantic_ai import (
    build_extra_headers,
    build_extra_headers_gemini,
    create_model,
)
from src.models import ResearchReport, SearchQueries
from src.tools import SearchResult, web_search

FEATURE_NAME = "research-agent"


@dataclass
class ResearchContext:
    """Context passed through the research workflow."""

    topic: str
    search_results: list[SearchResult] = field(default_factory=list)


def get_model_settings(provider: Provider, step: str) -> ModelSettings:
    """Build model settings with Majordomo headers for the given step.

    Args:
        provider: The LLM provider
        step: Workflow step name for tracking

    Returns:
        ModelSettings with extra_headers configured
    """
    example_headers = {"X-Majordomo-Example-Framework": "pydantic-ai"}
    if provider == "gemini":
        headers = build_extra_headers_gemini(
            feature=FEATURE_NAME, step=step, extra_headers=example_headers
        )
    else:
        headers = build_extra_headers(
            feature=FEATURE_NAME, step=step, extra_headers=example_headers
        )

    return ModelSettings(extra_headers=headers)


def create_query_agent(
    provider: Provider, model_name: str | None = None
) -> Agent[None, SearchQueries]:
    """Create an agent that generates search queries for a topic."""
    agent = Agent(
        model=create_model(provider, model_name),
        output_type=SearchQueries,
        system_prompt="""You are a research assistant. Given a topic, generate specific
        search queries that will help gather comprehensive information.

        Focus on:
            - Different aspects and angles of the topic
            - Recent developments and current state
            - Expert opinions and authoritative sources
            - Practical implications and real-world examples

        Generate queries that are specific enough to find relevant results,
        but broad enough to capture different perspectives.""",
    )
    return agent


def create_synthesis_agent(
    provider: Provider, model_name: str | None = None
) -> Agent[ResearchContext, ResearchReport]:
    """Create an agent that synthesizes search results into a report."""
    agent = Agent(
        model=create_model(provider, model_name),
        output_type=ResearchReport,
        deps_type=ResearchContext,
        system_prompt="""You are a research analyst. Synthesize the provided search results
        into a clear, well-structured research report.

        Guidelines:
            - Focus on facts and verifiable information
            - Note any conflicting information or limitations
            - Cite the number of sources you actually used
            - Be objective and balanced in your analysis
            - Set confidence based on source quality and consistency""",
    )

    @agent.system_prompt
    async def add_search_context(ctx: RunContext[ResearchContext]) -> str:
        """Inject search results into the system prompt."""
        if not ctx.deps.search_results:
            return "\n\nNo search results available. Base your report on your knowledge."

        results_text = "\n\n".join(
            f"### {r.title}\nURL: {r.url}\n{r.content}"
            for r in ctx.deps.search_results
        )
        return f"\n\n## Search Results\n\n{results_text}"

    return agent


class ResearchAgent:
    """High-level research agent that orchestrates the workflow."""

    def __init__(
        self,
        provider: Provider = "openai",
        model_name: str | None = None,
    ):
        """Initialize the research agent.

        Args:
            provider: LLM provider to use ("openai", "anthropic", or "gemini")
            model_name: Specific model name (uses provider default if not specified)
        """
        self.provider = provider
        self.model_name = model_name
        self.query_agent = create_query_agent(provider, model_name)
        self.synthesis_agent = create_synthesis_agent(provider, model_name)

    async def generate_queries(self, topic: str) -> SearchQueries:
        """Generate search queries for the given topic.

        Args:
            topic: The topic to research

        Returns:
            Generated search queries
        """
        settings = get_model_settings(self.provider, step="query-generation")
        result = await self.query_agent.run(f"Research topic: {topic}", model_settings=settings)
        return result.output

    def execute_searches(self, queries: list[str]) -> list[SearchResult]:
        """Execute web searches for the given queries.

        Args:
            queries: List of search query strings

        Returns:
            Combined search results from all queries
        """
        all_results: list[SearchResult] = []
        for query in queries:
            results = web_search(query, max_results=3)
            all_results.extend(results)
        return all_results

    async def synthesize(self, topic: str, search_results: list[SearchResult]) -> ResearchReport:
        """Synthesize search results into a research report.

        Args:
            topic: The original research topic
            search_results: Search results to synthesize

        Returns:
            A structured research report
        """
        context = ResearchContext(topic=topic, search_results=search_results)
        settings = get_model_settings(self.provider, step="synthesis")
        result = await self.synthesis_agent.run(
            f"Create a research report about: {topic}",
            deps=context,
            model_settings=settings,
        )
        return result.output
