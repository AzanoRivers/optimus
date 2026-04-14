"""
Machine-readable API reference for AI agents.
Served at GET /guide-ai — no authentication required.
"""

from fastapi.responses import JSONResponse

_GUIDE_AI = {
    "meta": {
        "name": "OptimusApi",
        "version": "1.0.0",
        "author": "AzanoRivers",
        "base_url": "https://optimus.azanolabs.com",
        "description": (
            "REST API for lossless/lossy image compression and async video compression. "
            "Powered by Pillow (images) and FFmpeg (video). "
            "Images are processed synchronously; videos use a chunked-upload + async-job flow."
        ),
        "human_guide_url": "https://optimus.azanolabs.com/guide",
    },
    # ── Authentication ────────────────────────────────────────────────────────
    "authentication": {
        "type": "api_key",
        "header": "X-API-Key",
        "scope": "All endpoints under /api/v1/ require X-API-Key. GET /guide and GET /guide-ai are public.",
        "on_missing_or_invalid": "HTTP 401",
    },
    # ── Image compression ─────────────────────────────────────────────────────
    "images": {
        "compress": {
            "method": "POST",
            "path": "/api/v1/media/images/compress",
            "auth_required": True,
            "request_content_type": "multipart/form-data",
            "description": (
                "Compress one or more images. "
                "Single image -> raw file response. "
                "Multiple images -> ZIP archive (compressed_images.zip)."
            ),
            "params": {
                "files": {
                    "type": "file[]",
                    "location": "form-data",
                    "required": True,
                    "allowed_extensions": ["jpg", "jpeg", "png", "webp"],
                    "max_files": 10,
                    "max_per_file_bytes": 52428800,
                    "max_batch_bytes": 209715200,
                    "description": "One or more image files to compress.",
                },
                "out": {
                    "type": "string",
                    "location": "query_param or form-data",
                    "required": False,
                    "default": "keep original format",
                    "allowed_values": ["jpg", "webp", "png"],
                    "description": (
                        "Output format. Converts all images in the batch. "
                        "Recommended: pass as URL query param (?out=webp) to avoid multipart issues."
                    ),
                },
                "size": {
                    "type": "integer",
                    "location": "query_param or form-data",
                    "required": False,
                    "default": None,
                    "range": "1–8000",
                    "description": (
                        "Max pixels on the longest side. Aspect ratio preserved. Never upscales. "
                        "Recommended: pass as URL query param (?size=1920)."
                    ),
                },
                "lossy": {
                    "type": "boolean",
                    "location": "query_param or form-data",
                    "required": False,
                    "default": False,
                    "description": (
                        "Lossy PNG compression via color quantization (256 colors, ~80% size reduction). "
                        "Only applies when output format is PNG. Ignored for webp/jpg output. "
                        "Recommended: pass as URL query param (?lossy=true)."
                    ),
                },
            },
            "recommended_url_patterns": [
                "POST /api/v1/media/images/compress?out=webp",
                "POST /api/v1/media/images/compress?out=webp&size=1920",
                "POST /api/v1/media/images/compress?lossy=true",
            ],
            "response": {
                "single_image": {
                    "http_status": 200,
                    "content_type": "image/jpeg | image/png | image/webp",
                    "body": "Raw compressed image bytes.",
                },
                "batch": {
                    "http_status": 200,
                    "content_type": "application/zip",
                    "filename": "compressed_images.zip",
                    "body": "ZIP archive containing all compressed images.",
                },
                "partial_timeout": {
                    "http_status": 206,
                    "description": "Timeout reached after at least 1 image was processed. Partial results returned.",
                    "header": "X-Optimus-Status: partial",
                },
            },
            "response_headers": {
                "X-Optimus-Status": "complete | partial",
                "X-Optimus-Processed": "integer — images successfully compressed",
                "X-Optimus-Total": "integer — total images received in request",
                "X-Optimus-Input-Size": "integer — total input size in bytes",
                "X-Optimus-Output-Size": "integer — total output size in bytes",
                "X-Optimus-Reduction-Pct": "float — e.g. 83.6 (percentage size reduction)",
            },
            "limits": {
                "max_files_per_request": 10,
                "max_file_size_bytes": 52428800,
                "max_batch_size_bytes": 209715200,
                "timeout_seconds": 85,
                "timeout_partial_behavior": "Returns HTTP 206 with already-processed images if >= 1 succeeded.",
                "timeout_zero_behavior": "Returns HTTP 408 if 0 images were processed.",
            },
            "http_status_codes": {
                "200": "All images processed successfully.",
                "206": "Partial — timeout hit after >= 1 image processed. X-Optimus-Status: partial.",
                "401": "Missing or invalid X-API-Key.",
                "408": "Timeout — 0 images processed within 85 s.",
                "422": "Validation error: unsupported format, file too large, invalid params.",
                "503": "Server busy — max concurrent image jobs reached. Body: { retry_after_seconds: N }.",
            },
        },
    },
    # ── Video compression ─────────────────────────────────────────────────────
    "videos": {
        "description": (
            "Video compression is async due to the Cloudflare 100 MB per-request limit and "
            "FFmpeg processing time (can take minutes for large files). "
            "Use this 5-step flow: init -> upload chunks sequentially -> finalize -> poll status -> download. "
            "To cancel at any point, call DELETE /upload/{upload_id}."
        ),
        "flow": [
            "1. POST   /api/v1/media/videos/upload/init          — start session, get upload_id",
            "2. POST   /api/v1/media/videos/upload/chunk         — send chunks in order (0, 1, 2…)",
            "3. POST   /api/v1/media/videos/upload/finalize      — signal upload complete, get job_id",
            "4. GET    /api/v1/media/videos/status/{job_id}      — poll every 3 s until done or failed",
            "5. GET    /api/v1/media/videos/download/{job_id}    — download compressed file (one-time)",
            "cancel:   DELETE /api/v1/media/videos/upload/{upload_id} — cancel and clean up at any step",
        ],
        "job_states": {
            "uploading": "Server is receiving chunks.",
            "queued": "All chunks received. Waiting for FFmpeg worker slot (max 1 concurrent).",
            "processing": "FFmpeg is compressing the video. progress_pct rises from 0 to 99.",
            "done": "Compression complete. File ready to download.",
            "failed": "FFmpeg error or processing timeout (1800 s). Check error_msg field.",
            "expired": "Upload session abandoned — no chunk activity for 15 minutes.",
        },
        "endpoints": {
            "init": {
                "method": "POST",
                "path": "/api/v1/media/videos/upload/init",
                "auth_required": True,
                "request_content_type": "application/json",
                "body_fields": {
                    "filename": {
                        "type": "string",
                        "required": True,
                        "description": "Original filename including extension.",
                        "allowed_extensions": ["mp4", "mov", "avi", "mkv"],
                        "example": "my_video.mp4",
                    },
                    "total_size": {
                        "type": "integer",
                        "required": True,
                        "unit": "bytes",
                        "min": 1,
                        "max": 524288000,
                        "description": "Total size of the video file in bytes. Max 500 MB (524,288,000).",
                    },
                    "total_chunks": {
                        "type": "integer",
                        "required": True,
                        "min": 1,
                        "max": 10,
                        "description": "Number of chunks the video will be split into.",
                    },
                },
                "response": {
                    "http_status": 201,
                    "body": {
                        "upload_id": "UUID string — use this in every subsequent /chunk and /finalize call",
                        "chunk_size_recommended": 94371840,
                    },
                },
            },
            "chunk": {
                "method": "POST",
                "path": "/api/v1/media/videos/upload/chunk",
                "auth_required": True,
                "request_content_type": "multipart/form-data",
                "critical_notes": [
                    "Do NOT set Content-Type header manually. Let the HTTP client set it automatically "
                    "when using FormData — it needs to include the multipart boundary.",
                    "Chunks MUST be sent sequentially in order starting at index 0.",
                ],
                "body_fields": {
                    "upload_id": {
                        "type": "string",
                        "form_field": True,
                        "required": True,
                        "description": "The UUID returned by /init.",
                    },
                    "chunk_index": {
                        "type": "integer",
                        "form_field": True,
                        "required": True,
                        "description": "0-based index of this chunk. Must send in strict order: 0, 1, 2…",
                    },
                    "chunk": {
                        "type": "file",
                        "form_field": True,
                        "required": True,
                        "max_bytes": 94371840,
                        "description": "Binary slice of the video file. Max 90 MB per chunk.",
                    },
                },
                "response": {
                    "http_status": 200,
                    "body": {
                        "received": "integer — number of chunks received so far",
                        "total": "integer — total chunks expected (from /init)",
                    },
                },
            },
            "finalize": {
                "method": "POST",
                "path": "/api/v1/media/videos/upload/finalize",
                "auth_required": True,
                "request_content_type": "application/json",
                "body_fields": {
                    "upload_id": {
                        "type": "string",
                        "required": True,
                        "description": "The same UUID used during chunk uploads.",
                    },
                },
                "response": {
                    "http_status": 202,
                    "body": {
                        "job_id": "UUID string — use this for /status and /download",
                        "status": "queued",
                    },
                },
                "error_503": "Video job queue is full (max 5 jobs). Body: { detail: 'queue full', retry_after_seconds: 60 }.",
            },
            "status": {
                "method": "GET",
                "path": "/api/v1/media/videos/status/{job_id}",
                "auth_required": True,
                "path_params": {
                    "job_id": "UUID string returned by /finalize",
                },
                "body": None,
                "polling_guidance": "Poll every 3 seconds. Stop polling when status is 'done' or 'failed'.",
                "response": {
                    "http_status": 200,
                    "body": {
                        "job_id": "UUID string",
                        "status": "uploading | queued | processing | done | failed | expired",
                        "progress_pct": (
                            "integer 0–100. "
                            "Rises from 0 to 99 while status=processing. "
                            "Reaches 100 only when status=done. "
                            "Use directly as CSS progress bar width percentage. "
                            "Show indeterminate spinner when status=queued."
                        ),
                        "input_size": "integer bytes — populated when status=done",
                        "output_size": "integer bytes — populated when status=done",
                        "reduction_pct": "float e.g. 67.3 — populated when status=done",
                        "error_msg": "string | null — populated when status=failed",
                        "file_deleted": "boolean — true after a successful download",
                    },
                },
            },
            "download": {
                "method": "GET",
                "path": "/api/v1/media/videos/download/{job_id}",
                "auth_required": True,
                "path_params": {
                    "job_id": "UUID string returned by /finalize",
                },
                "body": None,
                "precondition": "status must equal 'done' before calling this endpoint.",
                "response": {
                    "http_status": 200,
                    "content_type": "video/mp4",
                    "body": "Raw compressed video bytes.",
                },
                "critical_notes": [
                    "The file is permanently deleted from the server after transfer. Download is one-time only.",
                    "MUST use fetch() with the X-API-Key header to download. "
                    "window.location.href cannot send custom headers and will return 401.",
                    "Use fetch() -> response.blob() -> URL.createObjectURL() -> anchor click pattern.",
                ],
                "error_410": "File already downloaded or job expired.",
            },
            "cancel": {
                "method": "DELETE",
                "path": "/api/v1/media/videos/upload/{upload_id}",
                "auth_required": True,
                "path_params": {
                    "upload_id": "UUID string returned by /init (same as job_id).",
                },
                "body": None,
                "description": (
                    "Cancel and clean up a video upload or compression job at any stage. "
                    "Works in all states: uploading, queued, processing, done, failed. "
                    "If FFmpeg is actively running (processing), it is killed immediately. "
                    "All temporary files (chunks, assembled, compressed) are deleted from the server. "
                    "The job is removed from the in-memory registry."
                ),
                "response": {
                    "http_status": 200,
                    "body": {
                        "cancelled": True,
                        "job_id": "UUID string of the cancelled job",
                    },
                },
                "error_404": "Job not found (already cancelled, expired, or never created).",
            },
        },
        "limits": {
            "max_video_size_bytes": 524288000,
            "max_chunk_size_bytes": 94371840,
            "max_chunks_per_upload": 10,
            "max_concurrent_queue_size": 5,
            "processing_timeout_seconds": 1800,
            "file_retention_after_done_minutes": 30,
            "upload_session_expiry_minutes": 15,
        },
        "http_status_codes": {
            "201": "Init successful — upload session created.",
            "200": "Chunk accepted or status/download success.",
            "202": "Finalize accepted — job queued.",
            "401": "Missing or invalid X-API-Key.",
            "410": "File already downloaded or expired.",
            "422": "Validation error — check body field names, types, and allowed values.",
            "503": "Video queue full. Body: { retry_after_seconds: 60 }.",
        },
    },
    # ── Global errors ─────────────────────────────────────────────────────────
    "global_http_status_codes": {
        "401": "Missing or invalid X-API-Key header on any protected endpoint.",
        "422": "Request validation failed. FastAPI returns field-level error detail in body.",
        "503": "Server busy. Body always includes retry_after_seconds.",
    },
    # ── JavaScript pseudocode for AI-generated integrations ───────────────────
    "example_video_flow_js": """
// Full video compression flow (JavaScript)
const API   = 'https://optimus.azanolabs.com';
const KEY   = 'your-api-key';
const CHUNK = 80 * 1024 * 1024; // 80 MB chunks

async function compressVideo(file) {
  const totalChunks = Math.ceil(file.size / CHUNK);

  // 1. Init
  const { upload_id } = await fetch(`${API}/api/v1/media/videos/upload/init`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-API-Key': KEY },
    body: JSON.stringify({ filename: file.name, total_size: file.size, total_chunks: totalChunks }),
  }).then(r => r.json());

  // 2. Chunks — sequential, order is mandatory
  for (let i = 0; i < totalChunks; i++) {
    const form = new FormData();
    form.append('upload_id', upload_id);
    form.append('chunk_index', String(i));   // form field, not JSON
    form.append('chunk', file.slice(i * CHUNK, (i + 1) * CHUNK));
    // DO NOT set Content-Type — FormData sets it with the correct boundary automatically
    await fetch(`${API}/api/v1/media/videos/upload/chunk`, {
      method: 'POST', headers: { 'X-API-Key': KEY }, body: form,
    });
  }

  // 3. Finalize
  const { job_id } = await fetch(`${API}/api/v1/media/videos/upload/finalize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-API-Key': KEY },
    body: JSON.stringify({ upload_id }),
  }).then(r => r.json());

  // 4. Poll every 3 s
  let job;
  do {
    await new Promise(r => setTimeout(r, 3000));
    job = await fetch(`${API}/api/v1/media/videos/status/${job_id}`,
      { headers: { 'X-API-Key': KEY } }).then(r => r.json());
    // progressBar.value = job.progress_pct;
  } while (job.status === 'queued' || job.status === 'processing');

  // 5. Download via fetch+blob (window.location.href cannot send X-API-Key)
  if (job.status === 'done') {
    const res  = await fetch(`${API}/api/v1/media/videos/download/${job_id}`,
      { headers: { 'X-API-Key': KEY } });
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    Object.assign(document.createElement('a'),
      { href: url, download: 'compressed.mp4' }).click();
    URL.revokeObjectURL(url);
  }
}
""",
    "example_image_compress_curl": [
        "# Keep original format",
        "curl -X POST https://optimus.azanolabs.com/api/v1/media/images/compress -H 'X-API-Key: KEY' -F 'files=@photo.jpg' --output compressed.jpg",
        "",
        "# Convert to WebP (recommended - highest compression)",
        "curl -X POST 'https://optimus.azanolabs.com/api/v1/media/images/compress?out=webp' -H 'X-API-Key: KEY' -F 'files=@photo.png' --output compressed.webp",
        "",
        "# Resize to max 1920px and convert to WebP",
        "curl -X POST 'https://optimus.azanolabs.com/api/v1/media/images/compress?out=webp&size=1920' -H 'X-API-Key: KEY' -F 'files=@photo.jpg' --output compressed.webp",
        "",
        "# Lossy PNG (~80% reduction)",
        "curl -X POST 'https://optimus.azanolabs.com/api/v1/media/images/compress?lossy=true' -H 'X-API-Key: KEY' -F 'files=@photo.png' --output compressed.png",
        "",
        "# Batch (returns ZIP)",
        "curl -X POST 'https://optimus.azanolabs.com/api/v1/media/images/compress?out=webp' -H 'X-API-Key: KEY' -F 'files=@a.jpg' -F 'files=@b.png' --output result.zip",
    ],
}


def get_guide_ai() -> JSONResponse:
    return JSONResponse(content=_GUIDE_AI)
