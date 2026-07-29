"""FastAPI application entry point."""

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .api.routes.search import router as search_router
from .config import get_settings
from .db.session import get_db

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.include_router(search_router)


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    response: dict[str, str] = {"api": "ok"}

    try:
        await db.execute(text("SELECT 1"))
        response["database"] = "ok"
    except Exception as exc:
        response["database"] = "error"
        response["detail"] = str(exc)

    return response