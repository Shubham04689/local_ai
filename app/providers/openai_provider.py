import httpx
from typing import List
from app.providers.base_provider import BaseLLMProvider
from app.models.provider_models import ProviderResponse
import logging

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, endpoint: str, api_key: str, **kwargs):
        super().__init__(endpoint, api_key, **kwargs)
        self.client = httpx.AsyncClient(timeout=30.0)

    async def generate_response(self, message: str, model: str, temperature: float = 0.7, max_tokens: int = 150, **kwargs) -> ProviderResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = await self.client.post(f"{self.endpoint}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            tokens_used = data["usage"]["total_tokens"]

            return ProviderResponse(
                content=content,
                tokens_used=tokens_used,
                estimated_cost=self.estimate_cost(tokens_used, model),
                provider="openai",
                model=model
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def health_check(self) -> bool:
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await self.client.get(f"{self.endpoint}/models", headers=headers, timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = await self.client.get(f"{self.endpoint}/models", headers=headers)
            response.raise_for_status()
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        except Exception as e:
            logger.warning(f"Failed to fetch OpenAI models: {e}")
            return ["gpt-4", "gpt-3.5-turbo"]

    def estimate_cost(self, tokens: int, model: str) -> float:
        cost_per_1k_tokens = {
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.002,
            "gpt-4-turbo": 0.01
        }
        return (tokens / 1000) * cost_per_1k_tokens.get(model, 0.01)

    async def close(self):
        await self.client.aclose()

