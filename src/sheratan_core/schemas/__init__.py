"""Pydantic schemas for Sheratan Core API."""

from __future__ import annotations

from typing import Any, Dict, Optional, List

from pydantic import BaseModel, Field


class CompleteRequest(BaseModel):
    """LLM completion request payload."""

    model: str = Field(default="gpt-4o-mini")
    prompt: str
    max_tokens: int = Field(default=128, ge=1, le=4096)


class CompleteResponse(BaseModel):
    """LLM completion response payload."""

    model: str
    output: str
    usage: Dict[str, Any] = Field(default_factory=dict)


class AckResponse(BaseModel):
    """Generic acknowledgement response."""

    ok: bool = True


class RouterHealthResponse(BaseModel):
    """Health information returned by a router."""

    name: str
    status: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RouterModelsResponse(BaseModel):
    """Model discovery payload returned by a router."""

    name: str
    models: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RelayStatus(BaseModel):
    """Relay status callback payload."""

    job_id: str
    trace_id: Optional[str] = None
    phase: Optional[str] = None
    progress: Optional[int] = None
    message: Optional[str] = None
    ts: Optional[str] = None


class RelayFinal(BaseModel):
    """Relay final callback payload."""

    job_id: str
    trace_id: Optional[str] = None
    status: str
    output: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    ts: Optional[str] = None


__all__ = [
    "CompleteRequest",
    "CompleteResponse",
    "RelayStatus",
    "RelayFinal",
    "AckResponse",
    "RouterHealthResponse",
    "RouterModelsResponse",
]
