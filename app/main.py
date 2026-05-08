from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import accounts, analytics, auth, dev, journals, strategies, trades
from app.core.config import settings
from app.db import connect_db, disconnect_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_db()
    try:
        yield
    finally:
        await disconnect_db()


app = FastAPI(
    title="Tradejournal API",
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


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.ENVIRONMENT}


app.include_router(auth.router, prefix="/api")
app.include_router(accounts.router, prefix="/api")
app.include_router(trades.router, prefix="/api")
app.include_router(strategies.router, prefix="/api")
app.include_router(journals.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(dev.router, prefix="/api")
