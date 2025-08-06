# app/services/llm_service.py

import logging
from typing import Any, Dict, Optional
from app.config.settings import settings
from app.providers.provider_factory import ProviderFactory
from app.models.provider_models import ProviderResponse

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.provider_factory = ProviderFactory()
        self.default_provider = settings.default_llm_provider
        self.default_model = settings.default_llm_model

    async def generate_response(
        self,
        message: str,
        temperature: float = 0.7,
        max_tokens: int = 150,
        provider_override: Optional[str] = None,
        model_override: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate response using the specified or default provider and model.
        Implements fallback to other providers if enabled and primary fails.
        """
        provider_name = provider_override or self.default_provider
        model_name = model_override or self.default_model
        extra_params = extra_params or {}

        try:
            provider = await self.provider_factory.get_provider(provider_name)
            response: ProviderResponse = await provider.generate_response(
                message=message,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_params
            )
            return {
                "response": response.content,
                "status": "success",
                "provider_used": provider_name,
                "model_used": model_name,
                "tokens_used": response.tokens_used,
                "cost": response.estimated_cost,
            }
        except Exception as exc:
            logger.error(f"Provider {provider_name} failed with error: {exc}")
            if not settings.enable_fallback:
                raise Exception(f"Provider {provider_name} failed and fallback disabled")

            # Try fallback providers
            fallback_providers = [
                p for p in settings.fallback_providers if p != provider_name
            ][: settings.max_fallback_attempts]

            for fallback_provider_name in fallback_providers:
                try:
                    fallback_provider = await self.provider_factory.get_provider(fallback_provider_name)
                    fallback_model = settings.llm_provider_configs[fallback_provider_name].get("default_model")
                    fallback_response: ProviderResponse = await fallback_provider.generate_response(
                        message=message,
                        model=fallback_model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    logger.info(f"Fallback to provider {fallback_provider_name} succeeded")
                    return {
                        "response": fallback_response.content,
                        "status": "success_fallback",
                        "provider_used": fallback_provider_name,
                        "model_used": fallback_model,
                        "tokens_used": fallback_response.tokens_used,
                        "cost": fallback_response.estimated_cost,
                    }
                except Exception as fallback_exc:
                    logger.error(f"Fallback provider {fallback_provider_name} also failed: {fallback_exc}")

            raise Exception("All providers failed to generate a response")

    async def health_check(self) -> Dict[str, Dict[str, Any]]:
        """
        Check the health status of all enabled LLM providers.
        Returns a dictionary with provider name keys and status details.
        """
        health_status = {}
        for provider_name in settings.llm_providers:
            try:
                provider = await self.provider_factory.get_provider(provider_name)
                is_healthy = await provider.health_check()
                health_status[provider_name] = {
                    "available": is_healthy,
                    "endpoint": settings.llm_provider_configs[provider_name].get("endpoint"),
                    "default_model": settings.llm_provider_configs[provider_name].get("default_model"),
                }
            except Exception as e:
                health_status[provider_name] = {
                    "available": False,
                    "error": str(e),
                    "endpoint": settings.llm_provider_configs[provider_name].get("endpoint"),
                }
        return health_status

    async def list_providers(self) -> Dict[str, Any]:
        """
        List all configured providers with their basic configuration details.
        """
        providers_info = {}
        for provider_name in settings.llm_providers:
            config = settings.llm_provider_configs.get(provider_name, {})
            providers_info[provider_name] = {
                "endpoint": config.get("endpoint"),
                "default_model": config.get("default_model"),
                "available_models": config.get("available_models", []),
                "supports_streaming": config.get("supports_streaming", False),
                "supports_functions": config.get("supports_functions", False),
            }
        return {
            "default_provider": self.default_provider,
            "default_model": self.default_model,
            "providers": providers_info,
        }
