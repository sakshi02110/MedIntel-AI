"""
Input validators for MedIntel AI.

Validates uploaded PDF files for type, size, page count, and integrity
before any downstream processing occurs.
"""

import io
import os
from typing import Tuple

import pdfplumber

from src.utils.logger import get_logger

logger = get_logger("medintel.validators")

# ── Limits ────────────────────────────────────────────────────────────────────
MAX_FILE_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20")) * 1024 * 1024
MAX_PAGES: int = int(os.getenv("MAX_PDF_PAGES", "50"))
PDF_MAGIC_BYTES: bytes = b"%PDF-"


def validate_pdf_upload(file_bytes: bytes, filename: str) -> Tuple[bool, str]:
    """
    Validate an uploaded PDF file through multiple checks.

    Validation order:
    1. Non-empty check
    2. File extension check (.pdf)
    3. File size ≤ MAX_UPLOAD_SIZE_MB
    4. PDF magic-bytes header (%PDF-)
    5. Openable by pdfplumber (not corrupted)
    6. Page count ≤ MAX_PDF_PAGES
    7. At least one page exists

    Args:
        file_bytes: Raw bytes of the uploaded file.
        filename:   Original filename from the uploader.

    Returns:
        ``(True, success_message)`` if valid.
        ``(False, error_message)``  if invalid.
    """
    logger.debug(f"Validating '{filename}' ({len(file_bytes):,} bytes)")

    # 1. Empty file
    if not file_bytes:
        return False, "❌ The uploaded file is empty."

    # 2. Extension
    if not filename.lower().endswith(".pdf"):
        return False, "❌ Only PDF files are accepted. Please upload a `.pdf` file."

    # 3. Size
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        size_mb = len(file_bytes) / (1024 * 1024)
        return (
            False,
            f"❌ File size ({size_mb:.1f} MB) exceeds the {MAX_FILE_SIZE_BYTES // (1024*1024)} MB limit.",
        )

    # 4. Magic bytes
    if not file_bytes.startswith(PDF_MAGIC_BYTES):
        return (
            False,
            "❌ The file does not appear to be a valid PDF (missing `%PDF-` header). "
            "It may have been corrupted or renamed.",
        )

    # 5 & 6 & 7. Open with pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            page_count = len(pdf.pages)

            if page_count == 0:
                return False, "❌ The PDF contains no readable pages."

            if page_count > MAX_PAGES:
                return (
                    False,
                    f"❌ The PDF has {page_count} pages, which exceeds the {MAX_PAGES}-page limit. "
                    "Please upload the relevant section of the report only.",
                )

    except Exception as exc:
        logger.error(f"pdfplumber failed on '{filename}': {exc}")
        return (
            False,
            f"❌ The PDF appears to be corrupted or password-protected: {exc}",
        )

    logger.info(f"Validation passed: '{filename}' ({page_count} pages)")
    return True, f"✅ PDF validated successfully ({page_count} page(s))."
