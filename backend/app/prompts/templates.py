"""Prompt templates for product catalog summarization.

Loads system & human prompts from config/prompts.yaml and builds
Langchain ChatPromptTemplate objects.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

from app.core.logging_config import get_logger

logger = get_logger(__name__)

_PROMPTS_PATH = Path(__file__).resolve().parents[2] / "config" / "prompts.yaml"


def _load_prompts() -> dict:
    """Load prompts YAML once."""
    with open(_PROMPTS_PATH) as f:
        return yaml.safe_load(f)


_PROMPTS: dict = _load_prompts()


class ProductSummarizationPrompt:
    """Builds the ChatPromptTemplate for batch product summarization."""

    def __init__(self) -> None:
        system_text = _PROMPTS["system_prompts"]["summarizer"]
        human_text = _PROMPTS["human_prompts"]["summarize_batch"]

        self._system = SystemMessagePromptTemplate.from_template(system_text)
        self._human = HumanMessagePromptTemplate.from_template(human_text)

        logger.info("ProductSummarizationPrompt loaded")

    def get_prompt(self) -> ChatPromptTemplate:
        """Return the full chat prompt (system + human)."""
        return ChatPromptTemplate.from_messages([self._system, self._human])


class SingleProductPrompt:
    """Builds the ChatPromptTemplate for single-product summarization."""

    def __init__(self) -> None:
        system_text = _PROMPTS["system_prompts"]["summarizer"]
        human_text = _PROMPTS["human_prompts"]["summarize_single"]

        self._system = SystemMessagePromptTemplate.from_template(system_text)
        self._human = HumanMessagePromptTemplate.from_template(human_text)

    def get_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([self._system, self._human])


class ReviewPrompt:
    """Builds the ChatPromptTemplate for quality review of summaries."""

    def __init__(self) -> None:
        system_text = _PROMPTS["system_prompts"]["reviewer"]
        human_text = _PROMPTS["human_prompts"]["review"]

        self._system = SystemMessagePromptTemplate.from_template(system_text)
        self._human = HumanMessagePromptTemplate.from_template(human_text)

    def get_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([self._system, self._human])


def get_system_prompt(name: str) -> str:
    """Get a raw system prompt template by name."""
    return _PROMPTS["system_prompts"][name]


def get_human_prompt(name: str) -> str:
    """Get a raw human prompt template by name."""
    return _PROMPTS["human_prompts"][name]
