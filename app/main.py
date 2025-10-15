import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import get_logger

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    debug=settings.app_debug,
)

# Log configuration source on startup

logger = get_logger(__name__)
logger.info(f"🔧 Configuration: {settings.config_source}")


@app.get("/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "config_source": settings.config_source,
        "app_name": settings.app_name,
        "version": settings.app_version,
    }


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_reload,
    )
