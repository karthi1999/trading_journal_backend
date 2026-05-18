from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import (
    accounts,
    analytics,
    auth,
    dev,
    expenses,
    financial_profile,
    investments,
    journals,
    strategies,
    trades,
)
from app.core.config import settings
from app.db import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(
    title="Tracker API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_UPLOAD_DIR)), name="uploads")


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.ENVIRONMENT}


app.include_router(auth.router, prefix="/api")
app.include_router(accounts.router, prefix="/api")
app.include_router(trades.router, prefix="/api")
app.include_router(strategies.router, prefix="/api")
app.include_router(journals.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(financial_profile.router, prefix="/api")
app.include_router(investments.router, prefix="/api")
app.include_router(expenses.router, prefix="/api")
app.include_router(dev.router, prefix="/api")
