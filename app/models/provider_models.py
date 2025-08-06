from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ProviderResponse(BaseModel):
    content: str = Field(..., description="Final AI-generated content/answer")
    tokens_used: int = Field(..., description="Number of tokens used for this request/response")
    estimated_cost: float = Field(..., description="Estimated USD cost of this call (0.0 for free/local models)")
    provider: str = Field(..., description="Provider name (e.g., openai, ollama, anthropic)")
    model: str = Field(..., description="Model that generated the response (e.g., gpt-4, model_123, claude-3-opus)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional details from provider/model (if any)")


class ProviderConfig(BaseModel):
    endpoint: str = Field(..., description="Base API endpoint URL")
    api_key: str = Field(..., description="Provider API key (blank for local models)")
    default_model: str = Field(..., description="Default model for provider")
    available_models: list = Field(default_factory=list, description="List of other available models")
    supports_streaming: bool = Field(default=False, description="Does provider support streaming responses?")
    supports_functions: bool = Field(default=False, description="Does provider support function-calling/completion?")
    extra_params: dict = Field(default_factory=dict, description="Other provider-specific config fields")
