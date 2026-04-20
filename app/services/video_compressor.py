from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path

import httpx
from fastapi import FastAPI

from app.services.job_manager import (
    delete_upload_folder,
    update_job,
    upload_dir,
)

logger = logging.getLogger(__name__)

# ── Binary availability check at import time ──────────────────────────────────

_FFMPEG = shutil.which("ffmpeg")
if _FFMPEG is None:
    logger.warning(
        "ffmpeg not found in PATH. Video compression will fail at runtime. "
        "Install via: sudo dnf install -y ffmpeg"
    )

_FFPROBE = shutil.which("ffprobe")
if _FFPROBE is None:
    logger.warning(
        "ffprobe not found in PATH. Progress tracking will be disabled "
        "(progress_pct will remain 0 during compression)."
    )


# ── ffprobe: get video duration in microseconds ───────────────────────────────


async def ffprobe_duration_us(input_path: Path) -> int:
    """
    Return the video duration in microseconds using ffprobe.
    Returns 0 if ffprobe is unavailable or the output cannot be parsed
    (compression continues normally; progress_pct stays at 0).
    """
    if _FFPROBE is None:
        return 0
    try:
        proc = await asyncio.create_subprocess_exec(
            _FFPROBE,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(input_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        return int(float(stdout.decode().strip()) * 1_000_000)
    except Exception:
        return 0


# ── Internal: read FFmpeg -progress pipe and update job.progress_pct ─────────


async def _read_progress(
    proc: asyncio.subprocess.Process,
    jobs: dict,
    job_id: str,
    duration_us: int,
) -> None:
    """
    Read FFmpeg stdout (-progress pipe:1) line by line.
    Updates progress_pct on the job (0–99) while FFmpeg runs.
    Reaching 100 is the responsibility of the caller after confirming exit 0.
    """
    async for raw_line in proc.stdout:  # type: ignore[union-attr]
        line = raw_line.decode().strip()
        if line.startswith("out_time_ms=") and duration_us > 0:
            try:
                # Despite the name, out_time_ms contains microseconds
                elapsed_us = int(line.split("=", 1)[1])
                pct = min(int(elapsed_us / duration_us * 100), 99)
                update_job(jobs, job_id, progress_pct=pct)
            except (ValueError, ZeroDivisionError):
                pass


# ── Async compressor (called directly from video_worker) ─────────────────────


async def compress_video_file(
    input_path: Path,
    output_path: Path,
    jobs: dict,
    job_id: str,
) -> tuple[int, int]:
    """
    Compress a video using FFmpeg (async, non-blocking).

    Codec : libx264, CRF 23, preset medium
    Audio : AAC 128 k
    Writes progress_pct (0–99) to the job while running.
    Sets progress_pct=100 is the caller's responsibility on success.
    Returns (input_size_bytes, output_size_bytes).
    Raises RuntimeError if ffmpeg is unavailable, times out, or exits non-zero.
    """
    if _FFMPEG is None:
        raise RuntimeError("ffmpeg is not installed. Run: sudo dnf install -y ffmpeg")

    input_size = input_path.stat().st_size
    duration_us = await ffprobe_duration_us(input_path)

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
        "-progress",
        "pipe:1",  # write progress key=value pairs to stdout
        "-nostats",  # suppress redundant stderr stats
        str(output_path),
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Store proc reference on the job so the cancel endpoint can kill it
    _job = jobs.get(job_id)
    if _job is not None:
        _job.ffmpeg_proc = proc

    try:
        await asyncio.wait_for(
            _read_progress(proc, jobs, job_id, duration_us),
            timeout=1800.0,  # 30-minute hard limit
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()  # drain pipes to avoid child-process hang
        raise RuntimeError("FFmpeg timed out after 30 minutes")
    finally:
        # Always clear proc reference — job may no longer exist if cancelled
        _job = jobs.get(job_id)
        if _job is not None:
            _job.ffmpeg_proc = None

    await proc.wait()

    if proc.returncode != 0:
        stderr_bytes = await proc.stderr.read()  # type: ignore[union-attr]
        stderr = stderr_bytes.decode(errors="replace")[-1000:]
        raise RuntimeError(f"FFmpeg failed (exit {proc.returncode}): {stderr}")

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
    Calls compress_video_file directly (async — no executor needed for FFmpeg).

    Cancellation: the cancel endpoint removes the job from app.state.jobs and
    kills ffmpeg_proc if running. The worker detects the missing job at two
    checkpoints (before and after acquiring the semaphore) and skips gracefully.
    """
    while True:
        job_id: str = await app.state.video_queue.get()

        # Checkpoint 1: job was cancelled while queued → skip
        job = app.state.jobs.get(job_id)
        if job is None:
            app.state.video_queue.task_done()
            continue

        # Captured on compression success; drives the R2 upload below the semaphore.
        _destination_url = None

        async with app.state.ffmpeg_semaphore:
            # Checkpoint 2: job was cancelled while waiting for the semaphore
            job = app.state.jobs.get(job_id)
            if job is None:
                app.state.video_queue.task_done()
                continue

            update_job(app.state.jobs, job_id, status="processing")

            input_path = upload_dir(job.upload_id) / "assembled" / "video.mp4"
            output_path = upload_dir(job.upload_id) / "compressed" / "video.mp4"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                in_size, out_size = await compress_video_file(
                    input_path,
                    output_path,
                    app.state.jobs,
                    job_id,
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
                    shutil.rmtree(assembled, ignore_errors=True)

                logger.info(
                    "Video job %s done: %.1f%% reduction (%d → %d bytes)",
                    job_id,
                    reduction,
                    in_size,
                    out_size,
                )

                # Capture URL so the R2 upload runs after releasing the semaphore,
                # allowing the next queued job to start compressing immediately.
                _destination_url = job.destination_url

            except Exception as exc:
                # If the job was cancelled while FFmpeg was running, the cancel
                # endpoint already deleted the folder and removed the job from
                # the registry — don't overwrite state or double-delete.
                if app.state.jobs.get(job_id) is None:
                    logger.info("Video job %s: FFmpeg interrupted by cancel.", job_id)
                else:
                    logger.exception("Video job %s failed: %s", job_id, exc)
                    update_job(
                        app.state.jobs,
                        job_id,
                        status="failed",
                        error_msg=str(exc),
                    )
                    delete_upload_folder(job.upload_id)

        # ── R2 direct upload (outside ffmpeg_semaphore) ───────────────────────
        # The next queued job can start compressing while this file is pushed
        # to R2.  Uses asyncio.to_thread so the disk read is non-blocking.
        if _destination_url:
            r2_path = upload_dir(job.upload_id) / "compressed" / "video.mp4"
            r2_upload_ok = False
            try:
                file_bytes = await asyncio.to_thread(r2_path.read_bytes)
                async with httpx.AsyncClient(timeout=300.0) as http:
                    r2_resp = await http.put(
                        _destination_url,
                        content=file_bytes,
                        headers={"Content-Type": "video/mp4"},
                    )
                r2_resp.raise_for_status()
                # Signal R2 success BEFORE touching disk so the browser always
                # sees file_deleted=True and uses the fast complete path.
                update_job(app.state.jobs, job_id, file_deleted=True)
                r2_upload_ok = True
                logger.info(
                    "Video job %s: pushed %d bytes directly to R2.",
                    job_id,
                    len(file_bytes),
                )
            except Exception as r2_exc:
                logger.warning(
                    "Video job %s: direct R2 upload failed (%s). "
                    "File kept for legacy Vercel download.",
                    job_id,
                    r2_exc,
                )

            # Separate block: a disk error here must not shadow a successful R2 upload.
            if r2_upload_ok:
                try:
                    delete_upload_folder(job.upload_id)
                except Exception as del_exc:
                    logger.warning(
                        "Video job %s: local folder delete failed after R2 upload "
                        "(%s). Periodic cleanup will handle it.",
                        job_id,
                        del_exc,
                    )

        app.state.video_queue.task_done()
