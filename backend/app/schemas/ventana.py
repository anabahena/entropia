from typing import Any

from pydantic import BaseModel, Field


class VentanaAnalysisResult(BaseModel):
    description: str = Field(..., description="Natural-language analysis from VentanaAI")
    structured_data: dict[str, Any] | list[Any] | None = Field(
        default=None,
        description="Structured fields extracted or inferred by the model",
    )
