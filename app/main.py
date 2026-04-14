import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.guide import get_guide
from app.services.job_manager import Dict, JobState, cleanup_jobs_loop, purge_temp_root
from app.services.video_compressor import video_worker

logger = logging.getLogger(__name__)

# ── Concurrency limits ────────────────────────────────────────────────────────
_EXECUTOR_WORKERS = 2  # threads for CPU-bound work (Pillow, FFmpeg)
_MAX_IMAGES_IN_FLIGHT = 6  # 503 if exceeded
_MAX_VIDEO_QUEUE = 5  # asyncio.Queue maxsize; 503 if full


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    purge_temp_root()

    executor = ThreadPoolExecutor(max_workers=_EXECUTOR_WORKERS)
    jobs: Dict[str, JobState] = {}

    app.state.executor = executor
    app.state.jobs = jobs
    app.state.images_in_flight = 0
    app.state.max_images_in_flight = _MAX_IMAGES_IN_FLIGHT
    app.state.ffmpeg_semaphore = asyncio.Semaphore(1)
    app.state.video_queue = asyncio.Queue(maxsize=_MAX_VIDEO_QUEUE)

    cleanup_task = asyncio.create_task(cleanup_jobs_loop(jobs))
    app.state.cleanup_task = cleanup_task

    video_worker_task = asyncio.create_task(video_worker(app))
    app.state.video_worker_task = video_worker_task

    logger.info(
        "Optimus startup: executor=%d workers, max_images=%d, video_queue=%d",
        _EXECUTOR_WORKERS,
        _MAX_IMAGES_IN_FLIGHT,
        _MAX_VIDEO_QUEUE,
    )

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    video_worker_task.cancel()
    try:
        await video_worker_task
    except asyncio.CancelledError:
        pass
    executor.shutdown(wait=False)
    logger.info("Optimus shutdown complete.")


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
