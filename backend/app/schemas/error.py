from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class ErrorEnvelope(BaseModel):
    error_code: str = Field(..., description="String classification code of the error")
    message: str = Field(..., description="Human-readable explanation of the error")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional context or validation details")
