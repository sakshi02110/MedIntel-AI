import pytest
from src.services.pdf_service import PDFService

def test_pdf_validation_empty_bytes():
    service = PDFService()
    result = service.process_upload(b"", "test.pdf")
    assert not result.success
    assert "empty" in result.error.lower()

def test_pdf_validation_wrong_extension():
    service = PDFService()
    result = service.process_upload(b"%PDF-1.4...", "test.txt")
    assert not result.success
    assert "pdf" in result.error.lower()
