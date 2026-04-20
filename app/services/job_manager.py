from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Root directory for all video upload/processing data
TEMP_ROOT = Path("/home/opc/temp_optimus")


# ──────────────────────────────────────────────────────────────────────────────
# JobState
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class JobState:
    job_id: str
    upload_id: str
    status: str  # uploading | queued | processing | done | failed | expired
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    progress_pct: int = 0
    input_size: int = 0
    output_size: int = 0
    reduction_pct: float = 0.0
    error_msg: Optional[str] = None
    file_deleted: bool = False
    # Presigned R2 PUT URL — when set, video_worker uploads compressed file
    # directly to R2 instead of waiting for Vercel to pull it.
    destination_url: Optional[str] = None
    # Reference to the active FFmpeg subprocess — set by compress_video_file,
    # cleared on completion. Used by the cancel endpoint to kill the process.
    # Typed as Any to avoid importing asyncio.subprocess at module level.
    ffmpeg_proc: Optional[Any] = field(default=None, repr=False)

    def touch(self) -> None:
        self.updated_at = datetime.utcnow()

    def seconds_since_update(self) -> float:
        return (datetime.utcnow() - self.updated_at).total_seconds()


# ──────────────────────────────────────────────────────────────────────────────
# Registry helpers
# ──────────────────────────────────────────────────────────────────────────────

# Module-level registry — populated into app.state at startup.
# Direct use is intentional: all helpers operate on the dict passed in.


def get_job(jobs: Dict[str, JobState], job_id: str) -> Optional[JobState]:
    return jobs.get(job_id)


def update_job(jobs: Dict[str, JobState], job_id: str, **kwargs) -> None:
    job = jobs.get(job_id)
    if job is None:
        return
    for key, value in kwargs.items():
        setattr(job, key, value)
    job.touch()


def delete_job(jobs: Dict[str, JobState], job_id: str) -> None:
    jobs.pop(job_id, None)


# ──────────────────────────────────────────────────────────────────────────────
# Disk helpers
# ──────────────────────────────────────────────────────────────────────────────


def upload_dir(upload_id: str) -> Path:
    return TEMP_ROOT / upload_id


def delete_upload_folder(upload_id: str) -> None:
    path = upload_dir(upload_id)
    if path.exists():
        try:
            shutil.rmtree(path)
            logger.info("Deleted upload folder: %s", path)
        except Exception:
            logger.exception("Failed to delete upload folder: %s", path)


def purge_temp_root() -> int:
    """
    Delete all subdirectories inside TEMP_ROOT.
    Called at app startup to clean up leftovers from a previous process.
    Returns the count of deleted folders.
    """
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    count = 0
    for entry in TEMP_ROOT.iterdir():
        if entry.is_dir():
            try:
                shutil.rmtree(entry)
                count += 1
            except Exception:
                logger.exception("Failed to purge orphan folder: %s", entry)
    if count:
        logger.info("Startup cleanup: removed %d orphan upload folder(s).", count)
    return count


# ──────────────────────────────────────────────────────────────────────────────
# Periodic cleanup coroutine
# ──────────────────────────────────────────────────────────────────────────────


async def cleanup_jobs_loop(jobs: Dict[str, JobState]) -> None:
    """
    Background coroutine that runs every 5 minutes and enforces expiry rules:

      - uploading, no activity > 15 min  → delete folder + remove from registry
      - queued/processing, no update > 30 min → mark failed + delete folder
      - done, file still on disk > 30 min → delete folder, keep state
      - done, file already deleted > 30 min  → remove from registry
      - failed > 1 h                     → remove from registry
      - expired > 1 h                    → remove from registry
    """
    import asyncio  # local import — avoids top-level issues with Python 3.9

    while True:
        await asyncio.sleep(300)  # 5 minutes
        to_remove = []

        for job_id, job in list(jobs.items()):
            age = job.seconds_since_update()

            if job.status == "uploading" and age > 900:  # 15 min
                delete_upload_folder(job.upload_id)
                to_remove.append(job_id)

            elif job.status in ("queued", "processing") and age > 1800:  # 30 min
                update_job(
                    jobs, job_id, status="failed", error_msg="Processing timeout."
                )
                delete_upload_folder(job.upload_id)

            elif job.status == "done" and not job.file_deleted and age > 1800:  # 30 min
                delete_upload_folder(job.upload_id)
                update_job(jobs, job_id, file_deleted=True)

            elif job.status == "done" and job.file_deleted and age > 1800:  # 30 min
                # no-op if folder was already deleted; handles the edge case
                # where the post-R2-upload disk delete failed.
                delete_upload_folder(job.upload_id)
                to_remove.append(job_id)

            elif job.status in ("failed", "expired") and age > 3600:  # 1 h
                to_remove.append(job_id)

        for job_id in to_remove:
            jobs.pop(job_id, None)

        if to_remove:
            logger.info(
                "Cleanup: removed %d expired job(s) from registry.", len(to_remove)
            )
