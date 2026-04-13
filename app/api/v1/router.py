from fastapi import APIRouter, Depends, Request

from app.api.v1.media.router import router as media_router
from app.core.security import verify_api_key

router = APIRouter()

router.include_router(media_router)


@router.get("/status", tags=["status"], dependencies=[Depends(verify_api_key)])
async def server_status(request: Request) -> dict:
    """
    Returns current server capacity and queue state.
    Useful for the frontend to decide whether to submit work or wait.
    """
    state = request.app.state
    video_queued = state.video_queue.qsize()

    # Count active video jobs (processing state)
    video_processing = sum(
        1
        for job in state.jobs.values()
        if job.status == "processing"
    )

    return {
        "status": "ok",
        "worker": "single-async",
        "images_in_flight": state.images_in_flight,
        "images_capacity": state.max_images_in_flight,
        "video_jobs_queued": video_queued,
        "video_jobs_processing": video_processing,
        "video_jobs_total": len(state.jobs),
        "video_queue_capacity": state.video_queue.maxsize,
    }
