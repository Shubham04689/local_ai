import asyncio
import subprocess
import sys
import uvicorn
import logging
from app.utils.logging_config import setup_logging
from app.config.settings import settings
from app.utils.provider_utils import batch_health_check

async def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Universal AI Chatbot Application...")
    logger.info(f"Configured providers: {settings.llm_providers}")
    logger.info(f"Default provider: {settings.default_llm_provider}")

    # Check provider connectivity
    enabled_providers = {
        name: config for name, config in settings.llm_provider_configs.items() if name in settings.llm_providers
    }

    health_results = await batch_health_check(enabled_providers)

    available = [name for name, healthy in health_results.items() if healthy]
    unavailable = [name for name, healthy in health_results.items() if not healthy]

    logger.info(f"Available providers: {available}")
    if unavailable:
        logger.warning(f"Unavailable providers: {unavailable}")

    # Switch default provider if current is unavailable
    if settings.default_llm_provider not in available:
        if available:
            new_default = available[0]
            logger.warning(f"Default provider {settings.default_llm_provider} unavailable. Using {new_default} instead.")
            settings.default_llm_provider = new_default
        else:
            logger.error("No LLM providers are available! Exiting.")
            sys.exit(1)

    # Attempt to start Ollama locally if configured but unavailable
    if "ollama" in settings.llm_providers and "ollama" not in available:
        logger.info("Trying to start local Ollama server...")
        try:
            subprocess.run(["ollama", "serve"], check=False, capture_output=True)
            await asyncio.sleep(5)  # Give time for Ollama to start
            health_results = await batch_health_check({"ollama": settings.llm_provider_configs["ollama"]})
            if health_results.get("ollama", False):
                logger.info("Ollama server started successfully")
            else:
                logger.warning("Failed to start Ollama server")
        except Exception as e:
            logger.error(f"Failed to start Ollama server: {e}")

    # Start FastAPI server
    logger.info(f"Starting FastAPI on {settings.api_host}:{settings.api_port}...")
    config = uvicorn.Config(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )
    server = uvicorn.Server(config)
    try:
        await server.serve()
    except Exception as e:
        logger.error(f"Failed to start FastAPI server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
