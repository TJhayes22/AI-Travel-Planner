"""FastAPI application entry point."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .api.routes.destinations import router as destinations_router
from .api.routes.search import router as search_router
from .config import get_settings
from .db.session import get_db

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

# Allow the Next.js dev server (browser-side fetches, e.g. the search page)
# to call this API. Update this list when a real frontend domain exists.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)
app.include_router(destinations_router)


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