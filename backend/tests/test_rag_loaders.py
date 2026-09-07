from pathlib import Path
import pytest
from app.rag.loaders.base import clean_text, compute_file_hash, extract_metadata_from_text
from app.rag.loaders.factory import get_loader_for_file
from app.rag.loaders.html_loader import HTMLLoader
from app.rag.loaders.txt_loader import TextLoader


def test_clean_text_utility():
    dirty = "  SEBI   Circular   \r\n\r\n\r\n\tGuidelines on   Large Cap  \x00\x08  "
    cleaned = clean_text(dirty)
    assert cleaned == "SEBI Circular\n\nGuidelines on Large Cap"


def test_compute_file_hash(tmp_path: Path):
    test_file = tmp_path / "sample.txt"
    test_file.write_text("Test content for hashing", encoding="utf-8")
    hash1 = compute_file_hash(test_file)
    assert len(hash1) == 64

    # Hash should be deterministic
    hash2 = compute_file_hash(test_file)
    assert hash1 == hash2


def test_extract_metadata_from_comment_headers(tmp_path: Path):
    doc_path = tmp_path / "test_doc.txt"
    content = """# Title: RBI Sovereign Gold Bond
# Organization: RBI
# Document Type: circular
# Topic: gold_investments
# Asset Class: gold
# Publication Date: 2024-01-15

Detailed regulatory text follows here.
"""
    meta = extract_metadata_from_text(content, doc_path)
    assert meta.title == "RBI Sovereign Gold Bond"
    assert meta.organization == "RBI"
    assert meta.topic == "gold_investments"
    assert meta.asset_class == "gold"
    assert meta.publication_date == "2024-01-15"


def test_txt_loader(tmp_path: Path):
    test_file = tmp_path / "sebi_doc.txt"
    test_file.write_text(
        "# Organization: SEBI\n# Topic: mutual_funds\n\nLarge Cap fund must invest 80% in top 100 stocks.",
        encoding="utf-8",
    )
    loader = TextLoader()
    doc = loader.load(test_file)
    assert doc.metadata.organization == "SEBI"
    assert doc.metadata.topic == "mutual_funds"
    assert "80% in top 100 stocks" in doc.content
    assert len(doc.file_hash) == 64


def test_html_loader_strips_scripts_and_extracts_clean_text(tmp_path: Path):
    html_file = tmp_path / "rbi_fd.html"
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>RBI Master Direction - Bank Deposits</title>
</head>
<body>
    <script>alert("malicious script");</script>
    <nav><a href="/home">Home</a></nav>
    <h1>Fixed Deposit Regulations</h1>
    <p>DICGC provides deposit insurance coverage up to INR 5,00,000 per depositor.</p>
</body>
</html>"""
    html_file.write_text(html_content, encoding="utf-8")
    loader = HTMLLoader()
    doc = loader.load(html_file)
    assert doc.metadata.title == "RBI Master Direction - Bank Deposits"
    assert "alert" not in doc.content
    assert "DICGC provides deposit insurance coverage up to INR 5,00,000" in doc.content


def test_loader_factory_resolution_and_unsupported_error(tmp_path: Path):
    txt_loader = get_loader_for_file(tmp_path / "test.txt")
    assert isinstance(txt_loader, TextLoader)

    html_loader = get_loader_for_file(tmp_path / "test.html")
    assert isinstance(html_loader, HTMLLoader)

    with pytest.raises(ValueError) as exc:
        get_loader_for_file(tmp_path / "unsupported.exe")
    assert "Unsupported document format" in str(exc.value)
