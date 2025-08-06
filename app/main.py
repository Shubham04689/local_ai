from fastapi import FastAPI
from app.routes.chat import router as chat_router
from app.config.settings import settings
from app.utils.logging_config import setup_logging

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url=settings.api_docs_url,
    redoc_url=settings.api_redoc_url
)

setup_logging()  # Configure logging system

app.include_router(chat_router)

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Universal AI Chatbot API",
        "status": "running",
        "version": settings.api_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
