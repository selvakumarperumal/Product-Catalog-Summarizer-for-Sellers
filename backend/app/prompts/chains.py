"""Prompt chaining — multi-step LLM pipelines using LCEL.

A chain runs the summarizer first, then optionally feeds the output
into a quality reviewer for self-critique.
"""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence

from app.core.logging_config import get_logger
from app.prompts.templates import ProductSummarizationPrompt, ReviewPrompt

logger = get_logger(__name__)


def build_summarize_chain(llm) -> RunnableSequence:
    """Build a simple summarization LCEL chain: prompt → llm → parse."""
    prompt = ProductSummarizationPrompt().get_prompt()
    chain = prompt | llm
    logger.info("Built summarization chain")
    return chain


def build_review_chain(llm) -> RunnableSequence:
    """Build a review chain that scores a summary against original data."""
    prompt = ReviewPrompt().get_prompt()
    chain = prompt | llm | StrOutputParser()
    logger.info("Built review chain")
    return chain


def build_summarize_and_review_chain(llm) -> dict:
    """Return both chains for a two-step pipeline.

    Usage:
        chains = build_summarize_and_review_chain(llm)
        summary = chains["summarize"].invoke({...})
        review  = chains["review"].invoke({
            "original_data": ...,
            "generated_summary": summary,
            "format_instructions": ""
        })
    """
    return {
        "summarize": build_summarize_chain(llm),
        "review": build_review_chain(llm),
    }
