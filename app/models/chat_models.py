# app/models/chat_models.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message to send to LLM for response")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature for LLM response")
    max_tokens: Optional[int] = Field(150, ge=1, le=8192, description="Maximum tokens in the LLM output")
    provider: Optional[str] = Field(None, description="Override provider for this request (default set in config)")
    model: Optional[str] = Field(None, description="Override model for this request")
    extra_params: Optional[Dict[str, Any]] = Field(
        default=None, description="Provider/model-specific parameters (advanced)"
    )


class ChatResponse(BaseModel):
    response: str = Field(..., description="AI-generated response to the user's message")
    status: str = Field(..., description="Response status: success, error, or fallback")
    provider_used: str = Field(..., description="Provider that generated the response")
    model_used: str = Field(..., description="Model that generated the response")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used in request/response")
    cost: Optional[float] = Field(None, description="Estimated cost for this completion, USD (if available)")
    latency_ms: Optional[int] = Field(None, description="Request latency in milliseconds (if measured)")
    metadata: Optional[dict] = Field(None, description="Provider/model-specific metadata")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall status: healthy/unhealthy")
    providers: Dict[str, Any] = Field(..., description="Health details for each provider")
    timestamp: Optional[str] = Field(None, description="Health check timestamp (ISO 8601, UTC)")
