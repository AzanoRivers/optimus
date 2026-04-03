from __future__ import annotations

from io import BytesIO
from typing import Optional

from PIL import Image

# Pillow save parameters per output format (keyed by extension without dot)
_FORMAT_SAVE_PARAMS: dict[str, dict] = {
    "jpg": {"format": "JPEG", "quality": 75, "optimize": True},
    "jpeg": {"format": "JPEG", "quality": 75, "optimize": True},
    "png": {"format": "PNG", "optimize": True},
    "webp": {"format": "WEBP", "quality": 75, "method": 6},
}

# Formats that do not support an alpha channel
_NO_ALPHA_FORMATS = {"jpg", "jpeg"}

# Allowed input extensions (without dot)
SUPPORTED_INPUT_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

# Allowed output format values for the `out` param
SUPPORTED_OUTPUT_FORMATS = {"jpg", "webp", "png"}


def compress_image(
    data: bytes,
    original_ext: str,
    out_format: Optional[str] = None,
    max_size: Optional[int] = None,
) -> tuple[BytesIO, str]:
    """
    Compress a single image in-memory.

    Args:
        data:         Raw image bytes from UploadFile.
        original_ext: Source extension without dot, lowercase (e.g. "jpg").
        out_format:   Target format ("jpg", "webp", "png") or None to keep original.
        max_size:     Max pixel dimension on longest side, or None for no resize.

    Returns:
        Tuple of (BytesIO buffer positioned at 0, output extension without dot).

    Raises:
        ValueError: On unsupported output format.
    """
    target_ext = out_format if out_format else original_ext
    # Normalise jpeg → jpg for lookup and output filename consistency
    if target_ext == "jpeg":
        target_ext = "jpg"

    save_params = _FORMAT_SAVE_PARAMS.get(target_ext)
    if save_params is None:
        raise ValueError(f"Unsupported output format: '{target_ext}'")

    img = Image.open(BytesIO(data))

    # Resize to fit within max_size × max_size, preserving aspect ratio.
    # thumbnail() never upscales — images already within bounds are untouched.
    if max_size is not None:
        img.thumbnail((max_size, max_size), Image.LANCZOS)

    # Handle color-mode conversions required by certain output formats
    if target_ext in _NO_ALPHA_FORMATS:
        if img.mode in ("RGBA", "LA", "PA"):
            # Flatten transparency onto a white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "PA":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode == "CMYK":
            img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")
    else:
        # PNG and WEBP support RGBA; CMYK is still not ideal for web formats
        if img.mode == "CMYK":
            img = img.convert("RGB")

    buf = BytesIO()
    img.save(buf, **save_params)
    buf.seek(0)
    return buf, target_ext
