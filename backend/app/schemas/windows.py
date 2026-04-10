from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WindowListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_path: str
    sha256: str
    perceptual_hash: str
    description: str | None
    structured_data: Any | None
    created_at: datetime


class SimilarWindowItem(BaseModel):
    id: int
    hamming_distance: int = Field(..., ge=0, le=64)
    sha256: str
    image_path: str
    perceptual_hash: str


class SimilarWindowsResponse(BaseModel):
    reference_id: int
    threshold: int = Field(..., ge=0, le=64)
    items: list[SimilarWindowItem]


class WindowUploadResponse(BaseModel):
    id: int = Field(..., description="Primary key in windows table")
    sha256: str = Field(..., description="Hex-encoded SHA-256 of stored bytes")
    size_bytes: int = Field(..., ge=0)
    path: str = Field(..., description="Relative path to the stored file")
