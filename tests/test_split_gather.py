from pathlib import Path

from pypdf import PdfWriter

from pdfslice_py.gather import gather_all
from pdfslice_py.logger import create_logger
from pdfslice_py.manifest import read_manifest
from pdfslice_py.split import split_all


def _make_pdf(path: Path, pages: int = 2) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=200, height=200)
    with open(path, "wb") as f:
        writer.write(f)


def test_split_then_gather_round_trip(tmp_path: Path):
    logger = create_logger(quiet=True)
    src = tmp_path / "sample.pdf"
    _make_pdf(src, pages=2)

    results = split_all(tmp_path, logger)
    assert len(results) == 1
    assert results[0].page_count == 2
    assert results[0].skipped is False

    unit_folder = tmp_path / "sample"
    assert unit_folder.is_dir()
    assert (unit_folder / "sample.001.jpg").exists()
    assert (unit_folder / "sample.002.jpg").exists()

    manifest = read_manifest(unit_folder)
    assert manifest is not None
    assert manifest.pageCount == 2
    assert manifest.gatheredAt is None

    reports = gather_all(tmp_path, logger, check_only=True)
    assert len(reports) == 1
    assert reports[0].missing_pages == []
    assert reports[0].action == "check-only"

    gathered = gather_all(tmp_path, logger, backup=False)
    assert gathered[0].action == "created"
    assert (unit_folder / "sample.pdf").exists()

    manifest_after = read_manifest(unit_folder)
    assert manifest_after is not None
    assert manifest_after.gatheredAt is not None

    # second gather with nothing changed should skip regeneration
    gathered_again = gather_all(tmp_path, logger, backup=False)
    assert gathered_again[0].action == "skipped-unchanged"


def test_check_reports_missing_pages(tmp_path: Path):
    logger = create_logger(quiet=True)
    src = tmp_path / "sample.pdf"
    _make_pdf(src, pages=2)
    split_all(tmp_path, logger)

    unit_folder = tmp_path / "sample"
    (unit_folder / "sample.002.jpg").unlink()

    reports = gather_all(tmp_path, logger, check_only=True)
    assert reports[0].missing_pages == [2]
