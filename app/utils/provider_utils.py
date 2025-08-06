import asyncio
from typing import Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)

async def test_provider_connectivity(endpoint: str, headers: Dict[str, str] = None, timeout: int = 5) -> bool:
    """Test if a provider endpoint is reachable"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(endpoint, headers=headers or {})
            return response.status_code < 500
    except Exception as e:
        logger.debug(f"Connectivity test failed for {endpoint}: {e}")
        return False

def estimate_tokens(text: str) -> int:
    """Rough estimation of token count based on word count"""
    return int(len(text.split()) * 1.3)

def format_provider_error(provider: str, error: Exception) -> str:
    error_map = {
        "openai": "OpenAI API error",
        "anthropic": "Anthropic Claude API error",
        "ollama": "Local Ollama server error",
        "gemini": "Google Gemini API error"
    }
    provider_name = error_map.get(provider.lower(), f"{provider} API error")
    return f"{provider_name}: {str(error)}"

async def batch_health_check(providers: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
    async def check(name: str, config: Dict[str, Any]):
        headers = {}
        if config.get("api_key"):
            headers["Authorization"] = f"Bearer {config['api_key']}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(config["endpoint"], headers=headers)
                return name, response.status_code < 500
        except Exception as e:
            logger.debug(f"Health check failed for {name}: {e}")
            return name, False

    tasks = [check(name, cfg) for name, cfg in providers.items()]
    results = await asyncio.gather(*tasks)
    return dict(results)
