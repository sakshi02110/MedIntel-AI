"""
PDF Processing Service for MedIntel AI.

Handles:
- PDF validation (delegated to validators.py)
- Multi-page text extraction with pdfplumber
- Table-aware extraction (lab reports often embed values in tables)
"""

import io
from dataclasses import dataclass, field
from typing import List, Optional

import pdfplumber

from src.utils.logger import get_logger
from src.utils.validators import validate_pdf_upload
from src.utils.helpers import clean_text

logger = get_logger("medintel.pdf_service")


@dataclass
class PDFExtractionResult:
    """
    Encapsulates the outcome of a PDF processing operation.

    Attributes:
        success:     Whether extraction succeeded.
        text:        Full concatenated text from all pages.
        page_count:  Number of pages in the PDF.
        pages_text:  Per-page text (useful for chunking in RAG).
        error:       Human-readable error message if success=False.
        filename:    Original uploaded filename.
        char_count:  Total characters in extracted text.
    """

    success: bool
    text: str = ""
    page_count: int = 0
    pages_text: List[str] = field(default_factory=list)
    error: Optional[str] = None
    filename: str = ""

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()


class PDFService:
    """
    Validates and extracts text from uploaded medical report PDFs.

    Strategy:
    1. Validate size / type / page count via :func:`validate_pdf_upload`.
    2. For each page, extract plain text *and* tables.
    3. Merge table rows as pipe-delimited lines into the page text.
    4. Return a :class:`PDFExtractionResult`.
    """

    # Separator used between table rows when injected into page text
    TABLE_ROW_SEPARATOR = " | "

    def process_upload(self, file_bytes: bytes, filename: str) -> PDFExtractionResult:
        """
        Entry point: validate then extract text from an uploaded PDF.

        Args:
            file_bytes: Raw bytes of the uploaded file.
            filename:   Original filename (used for logging + error messages).

        Returns:
            :class:`PDFExtractionResult` with text or error details.
        """
        logger.info(f"process_upload called: '{filename}' ({len(file_bytes):,} bytes)")

        # ── Step 1: Validate ──────────────────────────────────────────────────
        is_valid, message = validate_pdf_upload(file_bytes, filename)
        if not is_valid:
            logger.warning(f"Validation failed for '{filename}': {message}")
            return PDFExtractionResult(success=False, error=message, filename=filename)

        # ── Step 2: Extract ───────────────────────────────────────────────────
        return self._extract(file_bytes, filename)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _extract(self, file_bytes: bytes, filename: str) -> PDFExtractionResult:
        """Extract text and tables from all PDF pages."""
        pages_text: List[str] = []

        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                page_count = len(pdf.pages)
                logger.debug(f"Opened '{filename}': {page_count} pages.")

                for page_idx, page in enumerate(pdf.pages, start=1):
                    page_content = self._extract_page(page, page_idx)
                    pages_text.append(page_content)
                    logger.debug(
                        f"  Page {page_idx}/{page_count}: "
                        f"{len(page_content):,} chars extracted."
                    )

            combined = clean_text("\n\n".join(pages_text))

            if not combined:
                logger.warning(
                    f"No text found in '{filename}'. "
                    "The PDF may be a scanned image (not OCR'd)."
                )
                return PDFExtractionResult(
                    success=False,
                    error=(
                        "⚠️ No text could be extracted from this PDF. "
                        "It appears to be a scanned image. "
                        "Please upload a text-based (digitally created) PDF."
                    ),
                    filename=filename,
                    page_count=page_count,
                )

            logger.info(
                f"Extraction complete: '{filename}' → "
                f"{len(combined):,} chars, {page_count} page(s)."
            )
            return PDFExtractionResult(
                success=True,
                text=combined,
                page_count=page_count,
                pages_text=pages_text,
                filename=filename,
            )

        except Exception as exc:
            logger.error(
                f"Failed to extract text from '{filename}': {exc}", exc_info=True
            )
            return PDFExtractionResult(
                success=False,
                error=f"❌ Error reading PDF: {exc}",
                filename=filename,
            )

    def _extract_page(self, page, page_idx: int) -> str:
        """
        Extract text from a single pdfplumber page, appending table data.

        pdfplumber's ``extract_text`` handles flowing text; ``extract_tables``
        captures structured lab-value tables that may not appear in the text flow.
        """
        # Plain text
        page_text: str = page.extract_text() or ""

        # Tables → pipe-delimited rows
        table_lines: List[str] = []
        try:
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                for row in table:
                    cells = [str(c).strip() if c is not None else "" for c in row]
                    row_line = self.TABLE_ROW_SEPARATOR.join(cells)
                    if row_line.replace("|", "").strip():  # skip fully empty rows
                        table_lines.append(row_line)
        except Exception as exc:
            logger.debug(f"Table extraction warning on page {page_idx}: {exc}")

        if table_lines:
            page_text = page_text + "\n" + "\n".join(table_lines)

        return page_text
