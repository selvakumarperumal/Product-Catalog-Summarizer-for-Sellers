"""Pydantic models for request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SummarizationResult(BaseModel):
    """Structured output the LLM must return."""

    row_id: list[int] = Field(..., description="Row IDs from the CSV")
    summary: list[str] = Field(..., description="Summary per product row")
