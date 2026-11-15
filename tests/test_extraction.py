import json
from pathlib import Path

import pytest


def test_plaintext_retains_original_text_and_hash(tmp_path):
    from astrology_evidence.corpus.extract import extract_file

    source = tmp_path / "source.txt"
    source.write_bytes(b"Original\ntext\x0cSecond page")
    result = extract_file(source, work_root=tmp_path)
    assert [p.text for p in result.pages] == ["Original\ntext", "Second page"]
    assert result.pages[1].pdf_page_index == 1
    assert result.pages[0].review_state == "pending"
    assert len(result.source_sha256) == 64


def test_page_json_preserves_coordinates_and_printed_labels(tmp_path):
    from astrology_evidence.corpus.extract import extract_file

    source = tmp_path / "pages.json"
    source.write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "text": "Verse",
                        "pdf_page_index": 4,
                        "printed_page": "ii",
                        "bounding_box": [1, 2, 30, 40],
                    }
                ]
            }
        )
    )
    page = extract_file(source, work_root=tmp_path).pages[0]
    assert page.pdf_page_index == 4
    assert page.printed_page == "ii"
    assert page.bounding_box == (1, 2, 30, 40)


@pytest.mark.parametrize(
    "payload",
    [
        {"pages": []},
        {"pages": [{"text": "x", "pdf_page_index": -1}]},
        {"pages": [{"text": "x", "pdf_page_index": 0}] * 2},
        {"pages": [{"text": "x", "pdf_page_index": 0, "bounding_box": [4, 2, 1, 3]}]},
        {"pages": [{"text": "x", "pdf_page_index": 0, "review_state": "approved"}]},
    ],
)
def test_invalid_pages_rejected(tmp_path, payload):
    from astrology_evidence.corpus.extract import extract_file

    source = tmp_path / "pages.json"
    source.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        extract_file(source, work_root=tmp_path)


def test_size_page_and_path_limits(tmp_path):
    from astrology_evidence.corpus.extract import extract_file

    source = tmp_path / "source.txt"
    source.write_text("abc\fdef")
    with pytest.raises(ValueError, match="byte"):
        extract_file(source, work_root=tmp_path, max_bytes=3)
    with pytest.raises(ValueError, match="page"):
        extract_file(source, work_root=tmp_path, max_pages=1)
    child = tmp_path / "child"
    child.mkdir()
    with pytest.raises(ValueError, match="root"):
        extract_file(source, work_root=child)


def test_blank_page_explicitly_requires_ocr(tmp_path):
    from astrology_evidence.corpus.extract import extract_file

    source = tmp_path / "blank.txt"
    source.write_text(" ")
    page = extract_file(source, work_root=tmp_path).pages[0]
    assert page.review_state == "quarantined"
    assert page.error == "ocr_required"
    assert page.ocr_confidence is None


def test_ocr_requires_operator_executable(tmp_path):
    from astrology_evidence.corpus.extract import ocr_image

    image = tmp_path / "scan.png"
    image.write_bytes(b"not a real image")
    with pytest.raises(ValueError, match="executable"):
        ocr_image(image, work_root=tmp_path, executable=Path("tesseract"))


def test_ocr_tsv_confidence_quarantines_and_retains_boxes(tmp_path, monkeypatch):
    from astrology_evidence.corpus.extract import ocr_image

    image = tmp_path / "scan.png"
    image.write_bytes(b"fixture")
    executable = tmp_path / "tesseract.exe"
    executable.write_bytes(b"fixture")

    def fake_run(args, **kwargs):
        assert kwargs["shell"] is False
        assert kwargs["timeout"] == 30
        assert args[3:] == ["-l", "eng", "--psm", "3", "tsv"]
        Path(args[2] + ".tsv").write_text(
            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
            "5\t1\t1\t1\t1\t1\t10\t20\t30\t40\t45\tVerse\n"
        )

    monkeypatch.setattr("subprocess.run", fake_run)
    page = ocr_image(image, work_root=tmp_path, executable=executable, pdf_page_index=7)
    assert page.text == "Verse"
    assert page.ocr_confidence == 0.45
    assert page.review_state == "quarantined"
    assert page.pdf_page_index == 7
    assert page.words[0].bounding_box == (10, 20, 40, 60)


def test_ocr_timeout_fails_explicitly(tmp_path, monkeypatch):
    import subprocess

    from astrology_evidence.corpus.extract import ocr_image

    image = tmp_path / "scan.png"
    image.write_bytes(b"fixture")
    executable = tmp_path / "tesseract.exe"
    executable.write_bytes(b"fixture")

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("tesseract", 30)

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(ValueError, match="timed out"):
        ocr_image(image, work_root=tmp_path, executable=executable)


def test_native_pdf_preserves_page_order_and_quarantines_empty(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace

    from astrology_evidence.corpus.extract import extract_file

    source = tmp_path / "native.pdf"
    source.write_bytes(b"%PDF-test-adapter")
    reader = SimpleNamespace(
        is_encrypted=False,
        pages=[
            SimpleNamespace(extract_text=lambda: "Native verse"),
            SimpleNamespace(extract_text=lambda: ""),
        ],
    )
    monkeypatch.setitem(sys.modules, "pypdf", SimpleNamespace(PdfReader=lambda *a, **k: reader))
    result = extract_file(source, work_root=tmp_path)
    assert result.pages[0].text == "Native verse"
    assert result.pages[1].pdf_page_index == 1
    assert result.pages[1].error == "ocr_required"
    with pytest.raises(ValueError, match="page"):
        extract_file(source, work_root=tmp_path, max_pages=1)
