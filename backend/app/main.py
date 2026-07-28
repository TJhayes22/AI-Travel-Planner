"""FastAPI application entry point."""

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db.session import get_db

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)


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