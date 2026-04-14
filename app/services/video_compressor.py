from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
from pathlib import Path

from fastapi import FastAPI

from app.services.job_manager import (
    delete_upload_folder,
    update_job,
    upload_dir,
)

logger = logging.getLogger(__name__)

# ── FFmpeg availability check at import time ──────────────────────────────────

_FFMPEG = shutil.which("ffmpeg")
if _FFMPEG is None:
    logger.warning(
        "ffmpeg not found in PATH. Video compression will fail at runtime. "
        "Install via: sudo dnf install -y ffmpeg"
    )


# ── Blocking compressor (runs inside ThreadPoolExecutor) ──────────────────────


def compress_video_file(input_path: Path, output_path: Path) -> tuple[int, int]:
    """
    Compress a video using FFmpeg.

    Codec : libx264, CRF 23, preset medium
    Audio : AAC 128 k
    Returns (input_size_bytes, output_size_bytes).
    Raises RuntimeError if ffmpeg is not installed or exits with a non-zero code.
    """
    if _FFMPEG is None:
        raise RuntimeError("ffmpeg is not installed. Run: sudo dnf install -y ffmpeg")

    input_size = input_path.stat().st_size

    cmd = [
        _FFMPEG,
        "-y",  # overwrite output without asking
        "-i",
        str(input_path),
        "-c:v",
        "libx264",
        "-crf",
        "23",
        "-preset",
        "medium",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",  # optimise for web streaming
        str(output_path),
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        timeout=1800,  # 30 min hard limit
    )

    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace")[-1000:]
        raise RuntimeError(f"FFmpeg failed (exit {result.returncode}): {stderr}")

    output_size = output_path.stat().st_size
    return input_size, output_size


# ── Assemble chunks into a single file ────────────────────────────────────────


def assemble_chunks(upload_id: str, total_chunks: int) -> Path:
    """
    Concatenate ordered .part files into assembled/video.mp4.
    Returns the assembled file path.
    Raises FileNotFoundError if any chunk is missing.
    """
    base = upload_dir(upload_id)
    chunks_dir = base / "chunks"
    assembled_dir = base / "assembled"
    assembled_dir.mkdir(parents=True, exist_ok=True)

    output = assembled_dir / "video.mp4"
    with output.open("wb") as out_f:
        for i in range(total_chunks):
            part = chunks_dir / f"{i}.part"
            if not part.exists():
                raise FileNotFoundError(f"Chunk {i} missing for upload {upload_id}")
            out_f.write(part.read_bytes())

    return output


# ── Video worker coroutine ────────────────────────────────────────────────────


async def video_worker(app: FastAPI) -> None:
    """
    Consumes jobs from app.state.video_queue one at a time.
    Acquires ffmpeg_semaphore to guarantee a single FFmpeg process runs at once.
    Offloads the blocking compress_video_file call to app.state.executor.
    """
    while True:
        job_id: str = await app.state.video_queue.get()

        job = app.state.jobs.get(job_id)
        if job is None:
            app.state.video_queue.task_done()
            continue

        async with app.state.ffmpeg_semaphore:
            update_job(app.state.jobs, job_id, status="processing")

            input_path = upload_dir(job.upload_id) / "assembled" / "video.mp4"
            output_path = upload_dir(job.upload_id) / "compressed" / "video.mp4"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            loop = asyncio.get_event_loop()
            try:
                in_size, out_size = await loop.run_in_executor(
                    app.state.executor,
                    compress_video_file,
                    input_path,
                    output_path,
                )
                reduction = round((1 - out_size / in_size) * 100, 1) if in_size else 0.0
                update_job(
                    app.state.jobs,
                    job_id,
                    status="done",
                    progress_pct=100,
                    input_size=in_size,
                    output_size=out_size,
                    reduction_pct=reduction,
                )
                # Free disk: remove assembled file, keep only compressed output
                assembled = upload_dir(job.upload_id) / "assembled"
                if assembled.exists():
                    import shutil as _shutil

                    _shutil.rmtree(assembled, ignore_errors=True)

                logger.info(
                    "Video job %s done: %.1f%% reduction (%d → %d bytes)",
                    job_id,
                    reduction,
                    in_size,
                    out_size,
                )

            except Exception as exc:
                logger.exception("Video job %s failed: %s", job_id, exc)
                update_job(
                    app.state.jobs,
                    job_id,
                    status="failed",
                    error_msg=str(exc),
                )
                delete_upload_folder(job.upload_id)

        app.state.video_queue.task_done()
