"""Request/Response models for search service."""

from pydantic import BaseModel, Field
from typing import Any


class SemanticSearchRequest(BaseModel):
    collection: str = Field(min_length=1)
    vector: list[float] = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    score_threshold: float | None = None
    filter: dict[str, Any] | None = None
    with_payload: bool = True
    with_vectors: bool = False


class KeywordSearchRequest(BaseModel):
    collection: str = Field(min_length=1)
    query: str = Field(min_length=1)
    field: str = Field(default="text")
    limit: int = Field(default=10, ge=1, le=100)
    filter: dict[str, Any] | None = None


class HybridSearchRequest(BaseModel):
    collection: str = Field(min_length=1)
    vector: list[float] = Field(min_length=1)
    query: str = Field(default="")
    query_field: str = Field(default="text")
    limit: int = Field(default=10, ge=1, le=100)
    score_threshold: float | None = None
    filter: dict[str, Any] | None = None
    vector_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    keyword_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    with_payload: bool = True


class MultiSearchRequest(BaseModel):
    collections: list[str] = Field(min_length=1)
    vector: list[float] = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    filter: dict[str, Any] | None = None
    with_payload: bool = True


class PointPayload(BaseModel):
    """Payload with ACL metadata fields."""
    text: str = Field(default="")
    department: str = Field(default="public")
    owner: str = Field(default="")
    classification: str = Field(default="public")
    tags: list[str] = Field(default_factory=list)
    # Any extra fields allowed
    model_config = {"extra": "allow"}


class PointData(BaseModel):
    id: int | str
    vector: list[float] = Field(min_length=1)
    payload: PointPayload


class UpsertRequest(BaseModel):
    collection: str = Field(min_length=1)
    points: list[PointData] = Field(min_length=1)


class IngestDocumentRequest(BaseModel):
    """Upload a document — auto chunk + embed + store."""
    collection: str = Field(min_length=1)
    text: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    chunk_size: int = Field(default=512, ge=100, le=4000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)
    id_prefix: str = Field(default="")
