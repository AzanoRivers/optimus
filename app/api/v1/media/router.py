from __future__ import annotations

import asyncio
import logging
import time
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Annotated, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse

from app.core.security import verify_api_key
from app.services.image_compressor import (
    SUPPORTED_INPUT_EXTENSIONS,
    compress_image,
)

logger = logging.getLogger(__name__)

_MAX_FILES = 10
_MAX_FILE_BYTES = 50 * 1024 * 1024  # 50 MB
_MAX_BATCH_BYTES = 200 * 1024 * 1024  # 200 MB
_TIMEOUT_SECONDS = 85

_CONTENT_TYPE = {
    "jpg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}

router = APIRouter(
    prefix="/media",
    tags=["media"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("/images/compress")
async def compress_images(
    request: Request,
    files: Annotated[List[UploadFile], File()],
    out: Annotated[Optional[str], Form()] = None,
    size: Annotated[Optional[int], Form()] = None,
    lossy: Annotated[Optional[bool], Form()] = None,
    out_q: Annotated[Optional[str], Query(alias="out", include_in_schema=False)] = None,
    size_q: Annotated[
        Optional[int], Query(alias="size", include_in_schema=False)
    ] = None,
    lossy_q: Annotated[
        Optional[bool], Query(alias="lossy", include_in_schema=False)
    ] = None,
) -> StreamingResponse:
    # ── Merge form fields with query params (query params as fallback) ────────
    out = out if out is not None else out_q
    size = size if size is not None else size_q
    lossy_png = bool(lossy if lossy is not None else lossy_q)

    # ── Check server capacity before accepting work ───────────────────────────
    state = request.app.state
    if state.images_in_flight >= state.max_images_in_flight:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "server_busy",
                "message": "Server is busy processing too many images. Please retry in a few seconds.",
                "retry_after_seconds": 5,
            },
            headers={"Retry-After": "5"},
        )

    # ── Validate params ──────────────────────────────────────────────────────
    if not files:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No files provided.",
        )
    if len(files) > _MAX_FILES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Too many files. Maximum is {_MAX_FILES} per request.",
        )

    if out is not None:
        out = out.lower().strip()
        if out == "jpeg":
            out = "jpg"
        if out not in {"jpg", "webp", "png"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid 'out' format. Must be jpg, webp, or png.",
            )

    if size is not None and (size < 1 or size > 8000):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="'size' must be between 1 and 8000.",
        )

    # ── Read + validate all files upfront ───────────────────────────────────
    # List of (original_filename, raw_bytes, extension_without_dot)
    file_data: list[tuple[str, bytes, str]] = []
    total_bytes = 0

    for f in files:
        ext = Path(f.filename or "").suffix.lower().lstrip(".")
        if ext not in SUPPORTED_INPUT_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Unsupported file type for '{f.filename}'. "
                    "Allowed: jpg, jpeg, png, webp."
                ),
            )

        data = f.file.read()

        if len(data) > _MAX_FILE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"'{f.filename}' exceeds the 50 MB per-file limit.",
            )

        total_bytes += len(data)
        if total_bytes > _MAX_BATCH_BYTES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Total batch size exceeds the 200 MB limit.",
            )

        file_data.append((f.filename or f"image_{len(file_data)}.{ext}", data, ext))

    # ── Process images via thread pool (non-blocking event loop) ─────────────
    total = len(file_data)
    start = time.time()
    results: list[tuple[str, bytes]] = []  # (output_filename, compressed_bytes)

    loop = asyncio.get_event_loop()
    state.images_in_flight += len(file_data)
    try:
        for original_name, data, original_ext in file_data:
            try:
                buf, out_ext = await loop.run_in_executor(
                    state.executor,
                    compress_image,
                    data,
                    original_ext,
                    out,
                    size,
                    lossy_png,
                )
                stem = Path(original_name).stem
                results.append((f"{stem}.{out_ext}", buf.read()))
            except Exception as exc:
                logger.exception("Failed to compress '%s': %s", original_name, exc)

            if time.time() - start >= _TIMEOUT_SECONDS:
                break
    finally:
        state.images_in_flight -= len(file_data)

    processed = len(results)

    # ── Timeout with nothing processed → 408 ────────────────────────────────
    if processed == 0:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Processing timed out before any image could be completed.",
        )

    # ── Build response headers ───────────────────────────────────────────────
    optimus_status = "complete" if processed == total else "partial"
    http_status = (
        status.HTTP_200_OK
        if optimus_status == "complete"
        else status.HTTP_206_PARTIAL_CONTENT
    )
    input_bytes_total = sum(len(d) for _, d, _ in file_data)
    output_bytes_total = sum(len(b) for _, b in results)
    reduction_pct = (
        round((1 - output_bytes_total / input_bytes_total) * 100, 1)
        if input_bytes_total > 0
        else 0
    )
    headers = {
        "X-Optimus-Status": optimus_status,
        "X-Optimus-Processed": str(processed),
        "X-Optimus-Total": str(total),
        "X-Optimus-Input-Size": str(input_bytes_total),
        "X-Optimus-Output-Size": str(output_bytes_total),
        "X-Optimus-Reduction-Pct": str(reduction_pct),
        "Access-Control-Expose-Headers": (
            "X-Optimus-Status, X-Optimus-Processed, X-Optimus-Total, "
            "X-Optimus-Input-Size, X-Optimus-Output-Size, X-Optimus-Reduction-Pct"
        ),
    }

    # ── Single image → direct StreamingResponse ──────────────────────────────
    if len(results) == 1:
        filename, compressed_bytes = results[0]
        ext = Path(filename).suffix.lower().lstrip(".")
        content_type = _CONTENT_TYPE.get(ext, "application/octet-stream")
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return StreamingResponse(
            iter([compressed_bytes]),
            status_code=http_status,
            media_type=content_type,
            headers=headers,
        )

    # ── Multiple images → ZIP StreamingResponse ───────────────────────────────
    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, compressed_bytes in results:
            zf.writestr(filename, compressed_bytes)
    zip_buf.seek(0)

    headers["Content-Disposition"] = 'attachment; filename="compressed_images.zip"'
    return StreamingResponse(
        zip_buf,
        status_code=http_status,
        media_type="application/zip",
        headers=headers,
    )


@router.post("/videos/compress", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def compress_videos() -> dict:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Video compression is not available yet. Coming soon.",
    )
