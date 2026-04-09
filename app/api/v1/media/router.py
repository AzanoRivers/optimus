from __future__ import annotations

import time
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.core.security import verify_api_key
from app.services.image_compressor import (
    SUPPORTED_INPUT_EXTENSIONS,
    compress_image,
)

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
def compress_images(
    files: Annotated[List[UploadFile], File()],
    out: Annotated[Optional[str], Form()] = None,
    size: Annotated[Optional[int], Form()] = None,
) -> StreamingResponse:
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

    # ── Process images sequentially with timeout ─────────────────────────────
    total = len(file_data)
    start = time.time()
    results: list[tuple[str, bytes]] = []  # (output_filename, compressed_bytes)

    for original_name, data, original_ext in file_data:
        try:
            buf, out_ext = compress_image(data, original_ext, out, size)
            stem = Path(original_name).stem
            results.append((f"{stem}.{out_ext}", buf.read()))
        except Exception:
            pass  # Skip corrupt/unreadable files — don't abort the batch

        if time.time() - start >= _TIMEOUT_SECONDS:
            break

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
    exposed = (
        "X-Optimus-Status, X-Optimus-Processed, X-Optimus-Total, "
        "X-Optimus-Input-Size, X-Optimus-Output-Size, X-Optimus-Reduction-Pct, "
        "X-Optimus-Debug-Out, X-Optimus-Debug-Size"
    )
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
        "X-Optimus-Debug-Out": str(out) if out is not None else "None",
        "X-Optimus-Debug-Size": str(size) if size is not None else "None",
        "Access-Control-Expose-Headers": exposed,
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
