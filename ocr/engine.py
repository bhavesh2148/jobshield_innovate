# ============================================================
# ocr/engine.py — Local Tesseract OCR Engine
# ============================================================
"""
JobShield Phase 6: Local Offline OCR Text Extraction.

Extracts text from job posting screenshots, email captures, and image-format
advertisements using Tesseract OCR. All processing is 100% local — no image
data is transmitted to any external service.

Supported image formats: PNG, JPEG/JPG, WEBP, BMP, TIFF
Requires: Tesseract OCR binary installed on the system.

Installation references:
  Windows: https://github.com/UB-Mannheim/tesseract/wiki
  macOS:   brew install tesseract
  Ubuntu:  sudo apt install tesseract-ocr

Usage:
    from ocr.engine import extract_text_from_image, TesseractUnavailableError

    try:
        text = extract_text_from_image(image_bytes, "image/png")
    except TesseractUnavailableError as e:
        # Guide user to install Tesseract
        ...
"""

import io
import logging
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ── Custom Exceptions ─────────────────────────────────────────
class TesseractUnavailableError(RuntimeError):
    """Raised when Tesseract binary is not found on the system."""

    INSTALL_GUIDE = (
        "Tesseract OCR is not installed or not in PATH. "
        "To enable screenshot-to-text analysis:\n"
        "  • Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki\n"
        "  • macOS:   brew install tesseract\n"
        "  • Ubuntu:  sudo apt install tesseract-ocr\n"
        "After installation, restart the JobShield API server."
    )


class OCRExtractionError(RuntimeError):
    """Raised when OCR processing fails due to image format or content issues."""


# ── Supported MIME Types ──────────────────────────────────────
SUPPORTED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/bmp",
    "image/tiff",
    "image/gif",
}

MIME_TO_PIL_FORMAT = {
    "image/png": "PNG",
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/webp": "WEBP",
    "image/bmp": "BMP",
    "image/tiff": "TIFF",
    "image/gif": "GIF",
}


def _check_tesseract_available() -> bool:
    """
    Checks if the Tesseract OCR binary is available on the system PATH
    or at common Windows installation locations.
    """
    if shutil.which("tesseract"):
        return True

    # Common Windows installation paths
    windows_paths = [
        Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
        Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
        Path(Path.home() / "AppData/Local/Programs/Tesseract-OCR/tesseract.exe"),
    ]
    for p in windows_paths:
        if p.exists():
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = str(p)
                logger.info(f"Tesseract found at: {p}")
            except ImportError:
                pass
            return True

    return False


def _preprocess_image(image_bytes: bytes, mime_type: str):
    """
    Opens and preprocesses image for optimal OCR accuracy.
    Converts to grayscale and applies light sharpening.
    """
    from PIL import Image, ImageEnhance

    try:
        img = Image.open(io.BytesIO(image_bytes))

        # Convert RGBA/P modes to RGB for consistency
        if img.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Convert to grayscale for better OCR accuracy on documents
        img_gray = img.convert("L")

        # Slight sharpening to improve character boundary detection
        enhancer = ImageEnhance.Sharpness(img_gray)
        img_sharp = enhancer.enhance(1.5)

        return img_sharp

    except Exception as e:
        raise OCRExtractionError(f"Image preprocessing failed: {e}") from e


def extract_text_from_image(
    image_bytes: bytes,
    mime_type: str = "image/png",
    language: str = "eng",
    min_chars: int = 10,
) -> str:
    """
    Extracts plain text from a screenshot or image file using Tesseract OCR.

    All processing is performed locally. No data leaves the system.

    Args:
        image_bytes: Raw image file bytes.
        mime_type: MIME type of the image (e.g., "image/png").
        language: Tesseract language code. Default "eng" (English).
        min_chars: Minimum non-whitespace characters required for valid extraction.

    Returns:
        Extracted text string, stripped of excess whitespace.

    Raises:
        TesseractUnavailableError: If Tesseract OCR binary is not installed.
        OCRExtractionError: If the image cannot be processed or yields no text.
        ValueError: If the MIME type is unsupported.
    """
    # ── Validate MIME type ────────────────────────────────────
    mime_lower = mime_type.lower().split(";")[0].strip()
    if mime_lower not in SUPPORTED_MIME_TYPES:
        raise ValueError(
            f"Unsupported image type: '{mime_type}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_MIME_TYPES))}"
        )

    # ── Check Tesseract availability ──────────────────────────
    if not _check_tesseract_available():
        raise TesseractUnavailableError(TesseractUnavailableError.INSTALL_GUIDE)

    # ── Import pytesseract ────────────────────────────────────
    try:
        import pytesseract
    except ImportError:
        raise TesseractUnavailableError(
            "pytesseract Python package is not installed. "
            "Run: pip install pytesseract"
        )

    # ── Preprocess & Extract ──────────────────────────────────
    logger.info(f"OCR extraction started: {mime_type}, {len(image_bytes)} bytes")

    img = _preprocess_image(image_bytes, mime_lower)

    try:
        # PSM 3: Fully automatic page segmentation (best for job posting screenshots)
        custom_config = r"--oem 3 --psm 3"
        raw_text: str = pytesseract.image_to_string(img, lang=language, config=custom_config)
    except Exception as e:
        raise OCRExtractionError(f"Tesseract OCR processing failed: {e}") from e

    # ── Clean and validate output ─────────────────────────────
    cleaned = _clean_ocr_output(raw_text)

    non_whitespace = len(cleaned.replace(" ", "").replace("\n", ""))
    if non_whitespace < min_chars:
        raise OCRExtractionError(
            f"OCR extracted insufficient text ({non_whitespace} chars). "
            "The image may be blank, too low-resolution, or contain no readable text."
        )

    logger.info(f"OCR extraction complete: {len(cleaned)} chars extracted")
    return cleaned


def _clean_ocr_output(raw: str) -> str:
    """
    Normalizes raw Tesseract output:
    - Replaces non-breaking spaces with regular spaces
    - Collapses 3+ consecutive blank lines into 2
    - Strips leading/trailing whitespace per line
    - Removes common Tesseract OCR artifacts (form-feed chars, NUL bytes)
    """
    import re

    # Strip NUL bytes and form-feed characters
    text = raw.replace("\x00", "").replace("\f", "\n")

    # Normalize non-breaking spaces
    text = text.replace("\xa0", " ")

    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.split("\n")]

    # Collapse 3+ consecutive blank lines into 2 blank lines
    normalized_lines = []
    blank_streak = 0
    for line in lines:
        if not line.strip():
            blank_streak += 1
            if blank_streak <= 2:
                normalized_lines.append("")
        else:
            blank_streak = 0
            normalized_lines.append(line)

    return "\n".join(normalized_lines).strip()


def get_ocr_status() -> dict:
    """
    Returns system OCR status for health checks and admin panels.
    """
    available = _check_tesseract_available()
    pytesseract_installed = False
    tesseract_version: Optional[str] = None

    try:
        import pytesseract
        pytesseract_installed = True
        if available:
            try:
                tesseract_version = pytesseract.get_tesseract_version().vstring
            except Exception:
                tesseract_version = "unknown"
    except ImportError:
        pass

    return {
        "ocr_available": available and pytesseract_installed,
        "tesseract_installed": available,
        "pytesseract_installed": pytesseract_installed,
        "tesseract_version": tesseract_version,
        "supported_formats": list(SUPPORTED_MIME_TYPES),
        "install_guide": TesseractUnavailableError.INSTALL_GUIDE if not available else None,
    }
