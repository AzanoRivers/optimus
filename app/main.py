from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings

# ─── Future versioned routers go here ───────────────────────────────────────
# from app.api.v1.router import router as v1_router
# from app.api.v2.router import router as v2_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    # startup logic here (db connections, caches, etc.)
    yield
    # shutdown / cleanup logic here


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ─── Future versioned routers registration ───────────────────────────────────
# app.include_router(v1_router, prefix="/api/v1")
# app.include_router(v2_router, prefix="/api/v2")


@app.get("/", tags=["status"])
async def root() -> dict:
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "status": "ok",
    }
