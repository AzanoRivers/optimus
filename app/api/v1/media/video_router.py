from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    UploadFile,
    File,
    Form,
    status,
)
from fastapi.responses import FileResponse
from urllib.parse import urlparse

from pydantic import BaseModel, field_validator
from typing import Optional
from starlette.background import BackgroundTask

from app.services.job_manager import (
    JobState,
    delete_job,
    delete_upload_folder,
    get_job,
    update_job,
    upload_dir,
)
from app.services.video_compressor import assemble_chunks

logger = logging.getLogger(__name__)

# ── Limits ────────────────────────────────────────────────────────────────────

_MAX_VIDEO_BYTES = 500 * 1024 * 1024  # 500 MB
_MAX_CHUNK_BYTES = (
    90 * 1024 * 1024
)  # 90 MB (browser sends ~10 MB; this is a server-side guard)
_MAX_CHUNKS = 128  # supports up to 500 MB at 4 MB/chunk with headroom
_ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "mkv"}

# ── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(
    prefix="/videos",
    tags=["videos"],
    # Auth heredada del router padre /media — no duplicar aqui
)


# ── Pydantic schemas ──────────────────────────────────────────────────────────


class InitRequest(BaseModel):
    filename: str
    total_size: int
    total_chunks: int
    destination_url: Optional[str] = None

    @field_validator("filename")
    @classmethod
    def validate_extension(cls, v: str) -> str:
        ext = Path(v).suffix.lower().lstrip(".")
        if ext not in _ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported format '{ext}'. Allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}"
            )
        return v

    @field_validator("total_size")
    @classmethod
    def validate_total_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("total_size must be positive.")
        if v > _MAX_VIDEO_BYTES:
            raise ValueError(
                f"Video exceeds the 500 MB limit ({v / 1024 / 1024:.1f} MB received)."
            )
        return v

    @field_validator("total_chunks")
    @classmethod
    def validate_total_chunks(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("total_chunks must be at least 1.")
        if v > _MAX_CHUNKS:
            raise ValueError(f"total_chunks cannot exceed {_MAX_CHUNKS}.")
        return v

    @field_validator("destination_url")
    @classmethod
    def validate_destination_url(cls, v: Optional[str]) -> Optional[str]:
        """Reject non-HTTPS and private/loopback addresses (SSRF prevention)."""
        if v is None:
            return v
        try:
            parsed = urlparse(v)
        except Exception:
            raise ValueError("destination_url is not a valid URL.")
        if parsed.scheme != "https":
            raise ValueError("destination_url must use HTTPS.")
        host = (parsed.hostname or "").lower()
        if not host:
            raise ValueError("destination_url has no valid host.")
        _BLOCKED = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
        _PRIVATE_PREFIXES = ("10.", "172.", "192.168.", "169.254.")
        if host in _BLOCKED or any(host.startswith(p) for p in _PRIVATE_PREFIXES):
            raise ValueError("destination_url must not point to an internal address.")
        return v


class FinalizeRequest(BaseModel):
    upload_id: str


# ── Helpers ───────────────────────────────────────────────────────────────────


def _safe_upload_id(upload_id: str) -> str:
    """Validate upload_id to prevent path traversal."""
    # Must be a valid UUID (no slashes, dots, etc.)
    try:
        return str(uuid.UUID(upload_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid upload_id format.",
        )


def _require_job(jobs: dict, job_id: str) -> JobState:
    job = get_job(jobs, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or expired.",
        )
    return job


# ── Internal helpers ──────────────────────────────────────────────────────────


def _abort_upload(jobs: dict, upload_id: str, error_msg: str) -> None:
    """Mark a job as failed and immediately delete its upload folder from disk.

    Called whenever a non-recoverable error occurs during chunk upload so that
    orphan folders don't accumulate until the periodic cleanup loop runs.
    """
    update_job(jobs, upload_id, status="failed", error_msg=error_msg)
    delete_upload_folder(upload_id)
    logger.warning(
        "Upload aborted (folder deleted): job=%s reason=%r", upload_id, error_msg
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/upload/init", status_code=status.HTTP_201_CREATED)
async def upload_init(body: InitRequest, request: Request) -> dict:
    """
    Start a new video upload session.
    Returns upload_id to use in subsequent chunk and finalize calls.
    """
    upload_id = str(uuid.uuid4())
    job_id = upload_id  # same UUID for simplicity

    # Create chunks directory
    chunks_dir = upload_dir(upload_id) / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    # Store total_chunks in a metadata file so finalize can verify completeness
    meta = upload_dir(upload_id) / "meta.txt"
    meta.write_text(str(body.total_chunks), encoding="utf-8")

    # Register job
    job = JobState(
        job_id=job_id,
        upload_id=upload_id,
        status="uploading",
        destination_url=body.destination_url,
    )
    request.app.state.jobs[job_id] = job

    logger.info(
        "Upload init: job=%s file=%s size=%d chunks=%d",
        job_id,
        body.filename,
        body.total_size,
        body.total_chunks,
    )

    return {
        "upload_id": upload_id,
        "chunk_size_recommended": _MAX_CHUNK_BYTES,
    }


@router.post("/upload/chunk", status_code=status.HTTP_200_OK)
async def upload_chunk(
    request: Request,
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    chunk: UploadFile = File(...),
) -> dict:
    """
    Upload one chunk of a video. Chunks must be sent in order (0-based index).
    Max chunk size: 90 MB.
    """
    upload_id = _safe_upload_id(upload_id)
    job = _require_job(request.app.state.jobs, upload_id)

    if job.status != "uploading":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Upload is in state '{job.status}', cannot receive more chunks.",
        )

    # Read and validate chunk size
    data = await chunk.read()
    if len(data) > _MAX_CHUNK_BYTES:
        msg = f"Chunk exceeds the 90 MB limit ({len(data) / 1024 / 1024:.1f} MB)."
        _abort_upload(request.app.state.jobs, upload_id, msg)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=msg,
        )
    if len(data) == 0:
        msg = "Empty chunk received."
        _abort_upload(request.app.state.jobs, upload_id, msg)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=msg,
        )

    # Validate index
    meta = upload_dir(upload_id) / "meta.txt"
    total_chunks = int(meta.read_text(encoding="utf-8"))
    if chunk_index < 0 or chunk_index >= total_chunks:
        msg = f"chunk_index {chunk_index} out of range (0–{total_chunks - 1})."
        _abort_upload(request.app.state.jobs, upload_id, msg)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=msg,
        )

    # Write part file
    part_path = upload_dir(upload_id) / "chunks" / f"{chunk_index}.part"
    part_path.write_bytes(data)

    # Touch job to reset inactivity timer
    job.touch()

    received = len(list((upload_dir(upload_id) / "chunks").glob("*.part")))
    logger.debug(
        "Chunk %d/%d received for job %s", chunk_index + 1, total_chunks, upload_id
    )

    return {"received": received, "total": total_chunks}


@router.post("/upload/finalize", status_code=status.HTTP_202_ACCEPTED)
async def upload_finalize(body: FinalizeRequest, request: Request) -> dict:
    """
    Signal that all chunks have been uploaded.
    Assembles chunks and enqueues the job for FFmpeg compression.
    Returns 503 if the video processing queue is full.
    """
    upload_id = _safe_upload_id(body.upload_id)
    job = _require_job(request.app.state.jobs, upload_id)

    if job.status != "uploading":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Upload is in state '{job.status}', cannot finalize.",
        )

    # Verify all chunks present
    meta = upload_dir(upload_id) / "meta.txt"
    total_chunks = int(meta.read_text(encoding="utf-8"))
    chunks_dir = upload_dir(upload_id) / "chunks"
    present = {p.stem for p in chunks_dir.glob("*.part")}
    missing = [i for i in range(total_chunks) if str(i) not in present]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing chunks: {missing}. Upload them before finalizing.",
        )

    # Check queue capacity
    video_queue = request.app.state.video_queue
    if video_queue.full():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "server_busy",
                "message": "Video processing queue is full. Please retry in a minute.",
                "retry_after_seconds": 60,
            },
            headers={"Retry-After": "60"},
        )

    # Assemble chunks in thread pool — avoids blocking the event loop
    # for large videos (up to 500 MB of sequential file I/O)
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            None,
            assemble_chunks,
            upload_id,
            total_chunks,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # Transition to queued and enqueue
    update_job(request.app.state.jobs, upload_id, status="queued")
    video_queue.put_nowait(upload_id)

    logger.info(
        "Job %s queued for compression (queue size: %d)", upload_id, video_queue.qsize()
    )

    return {"job_id": upload_id, "status": "queued"}


@router.get("/status/{job_id}", status_code=status.HTTP_200_OK)
async def video_status(job_id: str, request: Request) -> dict:
    """
    Poll the status of a video compression job.
    This endpoint reads only from memory — responds in under 1 ms.
    """
    job_id = _safe_upload_id(job_id)
    job = _require_job(request.app.state.jobs, job_id)

    return {
        "job_id": job_id,
        "status": job.status,
        "progress_pct": job.progress_pct,
        "input_size": job.input_size,
        "output_size": job.output_size,
        "reduction_pct": job.reduction_pct,
        "error_msg": job.error_msg,
        "file_deleted": job.file_deleted,
    }


@router.delete("/upload/{upload_id}", status_code=status.HTTP_200_OK)
async def cancel_upload(upload_id: str, request: Request) -> dict:
    """
    Cancel an in-progress upload or compression job.

    Works in any state:
      - uploading / queued: deletes chunks from disk, removes job from registry.
        The video_worker skips the job when it dequeues it (job no longer exists).
      - processing: kills the active FFmpeg process, deletes all data, removes job.
        The video_worker detects the missing job after the exception and logs it.
      - done (file not yet downloaded): deletes the compressed file, removes job.
      - failed / expired: cleans up any remaining disk data, removes job.

    Idempotent: returns 404 if the job is already gone.
    """
    upload_id = _safe_upload_id(upload_id)
    job = _require_job(request.app.state.jobs, upload_id)

    # Kill FFmpeg if it is actively running
    if job.ffmpeg_proc is not None:
        try:
            job.ffmpeg_proc.kill()
            logger.info("Job %s: FFmpeg process killed by cancel request.", upload_id)
        except Exception:
            logger.debug("Job %s: FFmpeg kill failed (already finished?).", upload_id)

    # Delete all data from disk (chunks, assembled, compressed)
    delete_upload_folder(job.upload_id)

    # Remove from in-memory registry so video_worker skips it if queued
    delete_job(request.app.state.jobs, upload_id)

    logger.info("Job %s cancelled and cleaned up.", upload_id)
    return {"cancelled": True, "job_id": upload_id}


@router.get("/download/{job_id}", status_code=status.HTTP_200_OK)
async def video_download(job_id: str, request: Request) -> FileResponse:
    """
    Download the compressed video.
    Only available when status is 'done' and file has not been deleted yet.
    The file is deleted from the server automatically once the transfer completes.
    """
    job_id = _safe_upload_id(job_id)
    job = _require_job(request.app.state.jobs, job_id)

    if job.status != "done":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Video is not ready for download (status: '{job.status}').",
        )

    if job.file_deleted:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="The compressed file has already been downloaded or has expired.",
        )

    output_path = upload_dir(job.upload_id) / "compressed" / "video.mp4"
    if not output_path.exists():
        # File missing despite flag — mark deleted and inform client
        update_job(request.app.state.jobs, job_id, file_deleted=True)
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="The compressed file is no longer available on the server.",
        )

    # Mark file as deleted immediately so concurrent requests don't race
    update_job(request.app.state.jobs, job_id, file_deleted=True)

    def _cleanup() -> None:
        delete_upload_folder(job.upload_id)
        logger.info("Video job %s: file deleted after successful download.", job_id)

    return FileResponse(
        path=str(output_path),
        media_type="video/mp4",
        filename="compressed_video.mp4",
        headers={"Cache-Control": "no-store"},
        background=BackgroundTask(_cleanup),
    )
