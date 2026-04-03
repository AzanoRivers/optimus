from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.router import router as v1_router
from app.guide import get_guide


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

app.include_router(v1_router, prefix="/api/v1")


@app.get("/", tags=["status"])
async def root() -> dict:
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "status": "ok",
    }


@app.get("/guide", tags=["guide"], include_in_schema=False)
def guide():
    return get_guide()
