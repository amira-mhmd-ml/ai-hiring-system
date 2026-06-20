
from pathlib import Path

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from agents.cv_analyzer import (
    extract_text_from_pdf,
    CVAnalysis,
    analyze_single_cv,
    call_with_retry
)
import asyncio


def test_extract_text_from_valid_pdf(tmp_path: Path):

    import fitz

    pdf_path = tmp_path / "valid_cv.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "John Doe - Software Engineer with 5 years experience in Python and AI.")
    doc.save(str(pdf_path))
    doc.close()

    text = extract_text_from_pdf(str(pdf_path))

    assert text is not None
    assert len(text.strip()) > 0
    assert "John Doe" in text


def test_extract_text_from_empty_pdf(tmp_path: Path):
    import fitz

    pdf_path = tmp_path / "empty_cv.pdf"
    doc = fitz.open()
    doc.new_page() 
    doc.save(str(pdf_path))
    doc.close()

    text = extract_text_from_pdf(str(pdf_path))

    assert len(text.strip()) < 100


def test_extract_text_from_corrupted_pdf(tmp_path: Path):
    fake_pdf_path = tmp_path / "corrupted.pdf"
    fake_pdf_path.write_bytes(b"this is not a real pdf file content")

    with pytest.raises(Exception):
        extract_text_from_pdf(str(fake_pdf_path))


def test_cv_analysis_schema_valid_data():
    data = CVAnalysis(
        candidate_name="Sara Ahmed",
        years_of_experience=3,
        technical_skills=["Python", "LangChain"],
        education="BSc Computer Science",
        previous_roles=["AI Engineer"],
        strength_summary="Strong in LLM applications",
        weakness_summary="Limited production scale experience"
    )

    assert data.candidate_name == "Sara Ahmed"
    assert data.years_of_experience == 3
    assert len(data.technical_skills) == 2


def test_cv_analysis_schema_missing_required_field():
    with pytest.raises(Exception):
        CVAnalysis(
            candidate_name="Sara Ahmed",
            technical_skills=["Python"],
            education="BSc",
            previous_roles=[],
            strength_summary="Good",
            weakness_summary="None"
        )


def test_cv_analysis_invalid_type_rejected():
    with pytest.raises(Exception):
        CVAnalysis(
            candidate_name="Sara Ahmed",
            years_of_experience="not a number",
            technical_skills=["Python"],
            education="BSc",
            previous_roles=[],
            strength_summary="Good",
            weakness_summary="None"
        )


@pytest.mark.asyncio
async def test_analyze_single_cv_handles_unreadable_pdf(tmp_path: Path):
    import fitz

    pdf_path = tmp_path / "scanned_image.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(pdf_path))
    doc.close()

    semaphore = asyncio.Semaphore(1)
    rate_limiter = asyncio.Semaphore(1)

    result = await analyze_single_cv(str(pdf_path), semaphore, rate_limiter)

    assert result["status"] == "failed"
    assert "Unreadable" in result["reason"] or "OCR" in result["reason"]


@pytest.mark.asyncio
async def test_retry_logic_succeeds_on_first_attempt():
    mock_chain = AsyncMock()
    mock_chain.ainvoke.return_value = "success"

    result = await call_with_retry(mock_chain, {"input": "test"}, max_retries=3)

    assert result == "success"
    assert mock_chain.ainvoke.call_count == 1


@pytest.mark.asyncio
async def test_retry_logic_succeeds_after_failures():
    mock_chain = AsyncMock()
    mock_chain.ainvoke.side_effect = [
        Exception("API Error 1"),
        Exception("API Error 2"),
        "success after retries"
    ]

    with patch("asyncio.sleep", new_callable=AsyncMock):  # تسريع الاختبار
        result = await call_with_retry(mock_chain, {"input": "test"}, max_retries=3)

    assert result == "success after retries"
    assert mock_chain.ainvoke.call_count == 3


@pytest.mark.asyncio
async def test_retry_logic_raises_after_max_retries():
    mock_chain = AsyncMock()
    mock_chain.ainvoke.side_effect = Exception("Persistent API Error")

    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(Exception, match="Persistent API Error"):
            await call_with_retry(mock_chain, {"input": "test"}, max_retries=3)

    assert mock_chain.ainvoke.call_count == 3