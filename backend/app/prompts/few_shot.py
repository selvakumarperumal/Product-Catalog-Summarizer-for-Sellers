"""Few-shot example manager.

Loads examples from config/prompts.yaml and formats them for injection
into prompts. Few-shot examples dramatically improve consistency for
structured tasks like product summarization.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from app.core.logging_config import get_logger

logger = get_logger(__name__)

_PROMPTS_PATH = Path(__file__).resolve().parents[2] / "config" / "prompts.yaml"


def _load_examples() -> list[dict]:
    with open(_PROMPTS_PATH) as f:
        data = yaml.safe_load(f)
    return data.get("few_shot_examples", [])


_EXAMPLES: list[dict] = _load_examples()


def get_examples(k: int | None = None) -> list[dict]:
    """Return k few-shot examples (all if k is None)."""
    if k is None:
        return _EXAMPLES
    return _EXAMPLES[:k]


def format_examples(k: int | None = None) -> str:
    """Format few-shot examples as a string block for prompt injection.

    Returns a block like:
        Example 1:
        Input: ...
        Output: ...

        Example 2:
        ...
    """
    examples = get_examples(k)
    parts: list[str] = []
    for i, ex in enumerate(examples, 1):
        parts.append(
            f"Example {i}:\n"
            f"Input:\n{ex['input'].strip()}\n"
            f"Output:\n{ex['output'].strip()}"
        )
    formatted = "\n\n".join(parts)
    logger.debug("Formatted %d few-shot examples", len(examples))
    return formatted
