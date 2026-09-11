"""PDF -> per-page JPG splitting. Direct port of lib/split.ts.

pdf-to-img + sharp (TS) map to pypdfium2 + Pillow here: pypdfium2 (Google's
PDFium, BSD-licensed — chosen over PyMuPDF's AGPL license for a permissively
licensed CLI) rasterizes each page at 2x scale (matching pdf-to-img's
`{ scale: 2 }`), Pillow re-encodes it to JPEG at quality 90.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pypdfium2 as pdfium
from pypdf import PdfReader

from .discover import find_pdfs, page_image_name
from .filename_template import DEFAULT_TEMPLATE
from .hash import hash_file
from .logger import Logger
from .manifest import Manifest, ManifestImageEntry, write_manifest

_RENDER_SCALE = 2  # ~2x native resolution, matches pdf-to-img's `{ scale: 2 }`
_JPEG_QUALITY = 90


@dataclass
class SplitResult:
    pdf: str
    output_folder: str
    page_count: int
    images: list[str] = field(default_factory=list)
    skipped: bool = False


def _folder_name_for(pdf_path: str | Path) -> str:
    return Path(pdf_path).stem


def split_all(
    input: str | Path,  # noqa: A002 - mirrors TS `input` option name
    logger: Logger,
    level: int = 1,
    flatten: bool = False,
    template: str = DEFAULT_TEMPLATE,
    dry_run: bool = False,
) -> list[SplitResult]:
    pdfs = find_pdfs(input, level)
    logger.info(f"Found {len(pdfs)} PDF file(s) under {input}", level=level)

    results: list[SplitResult] = []
    for pdf_path in pdfs:
        results.append(
            _split_one(
                pdf_path,
                input=input,
                flatten=flatten,
                template=template,
                dry_run=dry_run,
                logger=logger,
            )
        )
    return results


def _split_one(
    pdf_path: str,
    *,
    input: str | Path,  # noqa: A002
    flatten: bool,
    template: str,
    dry_run: bool,
    logger: Logger,
) -> SplitResult:
    base_name = _folder_name_for(pdf_path)
    parent_dir = Path(input) if flatten else Path(pdf_path).parent
    output_folder = parent_dir / base_name
    dest_pdf_path = output_folder / Path(pdf_path).name

    logger.info(f"Processing {pdf_path}", output_folder=str(output_folder))

    if dry_run:
        logger.info(f"[dry-run] would create folder {output_folder}")
        logger.info(f"[dry-run] would move {pdf_path} -> {dest_pdf_path} (copy, original kept)")
        page_count = len(PdfReader(pdf_path).pages)
        for i in range(1, page_count + 1):
            logger.info(f"[dry-run] would create image {page_image_name(base_name, i, template)}")
        return SplitResult(
            pdf=str(pdf_path),
            output_folder=str(output_folder),
            page_count=page_count,
            images=[],
            skipped=True,
        )

    output_folder.mkdir(parents=True, exist_ok=True)

    # "Move" without deleting the original: copy into the new folder. The
    # original PDF at its source path is left untouched, per spec.
    if not dest_pdf_path.exists():
        shutil.copyfile(pdf_path, dest_pdf_path)

    page_count = len(PdfReader(str(dest_pdf_path)).pages)

    images: list[str] = []
    image_entries: list[ManifestImageEntry] = []

    doc = pdfium.PdfDocument(str(dest_pdf_path))
    try:
        for i in range(page_count):
            page = doc[i]
            bitmap = page.render(scale=_RENDER_SCALE)
            img = bitmap.to_pil().convert("RGB")

            page_num = i + 1
            file_name = page_image_name(base_name, page_num, template)
            image_path = output_folder / file_name
            img.save(image_path, "JPEG", quality=_JPEG_QUALITY)
            file_hash = hash_file(image_path)
            images.append(str(image_path))
            image_entries.append(ManifestImageEntry(file=file_name, page=page_num, hash=file_hash))
            logger.debug("Wrote page image", file_name=file_name, page=page_num)

            bitmap.close()
            page.close()
    finally:
        doc.close()

    source_pdf_hash = hash_file(dest_pdf_path)
    manifest = Manifest(
        version=1,
        sourcePdf=dest_pdf_path.name,
        sourcePdfHash=source_pdf_hash,
        pageCount=page_count,
        images=image_entries,
        updatedAt=datetime.now(timezone.utc).isoformat(),
        filenameTemplate=template,
    )
    write_manifest(output_folder, manifest)

    logger.info(f"Split complete: {page_count} page(s)", output_folder=str(output_folder))
    return SplitResult(
        pdf=str(dest_pdf_path),
        output_folder=str(output_folder),
        page_count=page_count,
        images=images,
        skipped=False,
    )
