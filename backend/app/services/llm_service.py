"""LLM service — initialises the model and runs summarization pipelines."""

from __future__ import annotations

import asyncio
import time

import pandas as pd
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.core.exceptions import LLMApiKeyError, LLMProcessingError
from app.core.logging_config import get_logger
from app.models.schemas import SummarizationResult
from app.prompts.templates import ProductSummarizationPrompt
from app.services.file_service import (
    chunk_dataframe,
    df_to_csv_string,
)

logger = get_logger(__name__)

# ── Retry config ─────────────────────────────────────────────────────────────
MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds


class LLMService:
    """Handles LLM initialisation, prompt execution, and DataFrame summarization."""

    def __init__(self) -> None:
        # 1. Validate API key
        if not settings.GOOGLE_API_KEY or settings.GOOGLE_API_KEY == "your-api-key":
            raise LLMApiKeyError("Set GOOGLE_API_KEY or TF_GOOGLE_API_KEY in your environment")

        # 2. Initialise model
        self.model = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            temperature=settings.MODEL_TEMPERATURE,
            api_key=settings.GOOGLE_API_KEY,
        )
        logger.info("LLM ready: %s (temp=%.1f)", settings.MODEL_NAME, settings.MODEL_TEMPERATURE)

        # 3. Prompt + output parser
        self.prompt = ProductSummarizationPrompt().get_prompt()
        self.parser = PydanticOutputParser(pydantic_object=SummarizationResult)

        # 4. LCEL chain: prompt → model → parser
        self.chain = self.prompt | self.model | self.parser

    # ── Core invoke (with retry) ─────────────────────────────────────────────

    async def _invoke_with_retry(self, inputs: dict) -> SummarizationResult:
        """Invoke the chain with exponential-backoff retry."""
        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                start = time.perf_counter()
                result = await asyncio.to_thread(self.chain.invoke, inputs)
                elapsed = (time.perf_counter() - start) * 1000

                logger.info(
                    "LLM call OK: attempt=%d, latency=%.0fms, rows=%d",
                    attempt, elapsed, len(result.row_id),
                )
                return result

            except Exception as e:
                last_error = e
                wait = BACKOFF_BASE ** attempt
                logger.warning(
                    "LLM call failed (attempt %d/%d): %s — retrying in %ds",
                    attempt, MAX_RETRIES, e, wait,
                )
                await asyncio.sleep(wait)

        raise LLMProcessingError(f"LLM failed after {MAX_RETRIES} retries: {last_error}")

    # ── Summarize a single chunk ─────────────────────────────────────────────

    async def summarize_chunk(self, chunk_df: pd.DataFrame) -> SummarizationResult:
        """Summarize a DataFrame chunk via the LLM."""
        csv_text = df_to_csv_string(chunk_df)
        inputs = {
            "product_data": csv_text,
            "format_instructions": self.parser.get_format_instructions(),
        }
        return await self._invoke_with_retry(inputs)

    # ── Summarize a full DataFrame ───────────────────────────────────────────

    async def summarize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Chunk a DataFrame, summarize each chunk, return result DataFrame."""
        chunks = chunk_dataframe(df)

        all_ids: list[int] = []
        all_summaries: list[str] = []

        for i, chunk in enumerate(chunks, 1):
            logger.info("Processing chunk %d/%d (%d rows)", i, len(chunks), len(chunk))
            result = await self.summarize_chunk(chunk)
            all_ids.extend(result.row_id)
            all_summaries.extend(result.summary)

        # Build output DataFrame
        output_df = df.copy()
        output_df["summary"] = ""
        for row_id, summary in zip(all_ids, all_summaries):
            if 0 <= row_id < len(output_df):
                output_df.at[row_id, "summary"] = summary

        logger.info("Summarization complete: %d products", len(df))
        return output_df
