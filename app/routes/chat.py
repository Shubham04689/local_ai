# app/routes/chat.py

from fastapi import APIRouter, HTTPException, status
from app.services.llm_service import LLMService
from app.models.chat_models import ChatRequest, ChatResponse, HealthResponse

router = APIRouter(prefix="/api/v1", tags=["chat"])

@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_endpoint(request: ChatRequest):
    """
    Accepts chat prompts and streams/returns the response from the appropriate LLM provider/model.
    Takes optional `provider` and `model` overrides to support universal/multi-provider features.
    """
    try:
        llm_service = LLMService()
        response_data = await llm_service.generate_response(
            message=request.message,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            provider_override=request.provider,
            model_override=request.model,
            extra_params=request.extra_params,
        )
        return ChatResponse(**response_data)
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Returns overall status and per-provider health for all configured LLM backends.
    """
    llm_service = LLMService()
    health_status = await llm_service.health_check()
    overall = "healthy" if any(p["available"] for p in health_status.values()) else "unhealthy"
    return HealthResponse(status=overall, providers=health_status)
