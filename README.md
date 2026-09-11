# pdfslice-py

PDF page-image splitter, gatherer, and integrity checker — Python port of
[pdfslice](https://github.com/DuckyMomo20012/pdfslice) (TypeScript).

pdfslice-py helps you break a PDF into one image per page, keep a manifest of
the split output, verify whether all page images are present, and rebuild a
PDF from those images when needed.

## About the Project

This project is designed for workflows where PDF pages need to be processed
as images without losing the source document structure. It keeps the
original PDF intact, writes page-level JPG files into a folder beside the
source, and records metadata so the project can later verify or reconstruct
the full document.

### Features

- Split PDF files into per-page JPG images
- Keep a manifest with page hashes and metadata
- Check for missing page images without rewriting a PDF
- Gather page images back into a single PDF
- Optionally flatten output folders across a directory tree
- Support dry-run mode for safe previewing

### Port notes (vs. the TypeScript original)

- `pdf-to-img` + `sharp` → [`pypdfium2`](https://github.com/pypdfium2-team/pypdfium2)
  + [`Pillow`](https://python-pillow.org/) for rasterizing pages and encoding
  JPEGs. `pypdfium2` (Google's PDFium, BSD-licensed) was chosen over PyMuPDF
  specifically to keep pdfslice-py permissively licensed — PyMuPDF is AGPL.
- `pdf-lib` → [`pypdf`](https://pypdf.readthedocs.io/) for reading page
  counts, and Pillow's multi-page PDF writer for rebuilding a PDF from images
  in `gather`.
- `winston` → a small stdlib-`logging`-based logger with the same
  level/verbose/quiet/log-file behavior.
- `@stricli/core` → [`click`](https://click.palletsprojects.com/) for the CLI.
- The on-disk manifest (`.pdfslice-manifest.json`) uses the exact same
  camelCase JSON schema as the TypeScript version, so a folder split by
  either implementation can be gathered/checked by the other.

## Getting Started

### Prerequisites

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/)

```bash
pip install uv
```

### Install

Install the CLI globally with uv:

```bash
uv tool install .
# or, once published: uv tool install pdfslice-py
```

Or set up for local development:

```bash
uv venv
uv pip install -e ".[test]"
uv run pdfslice --help
```

Install straight from GitHub:

```bash
uv tool install git+https://github.com/DuckyMomo20012/pdfslice-py.git
```

## Usage

The CLI exposes three commands:

```bash
pdfslice split <input> [--level <n>] [--flatten] [--template <string>] [--dry-run] [--verbose] [--quiet] [--log-file <path>]
pdfslice gather <input> [--backup/--no-backup] [--dry-run] [--verbose] [--quiet] [--log-file <path>]
pdfslice check <input> [--verbose] [--quiet] [--log-file <path>]
```

(With `uv run`, prefix each command with `uv run`, e.g. `uv run pdfslice split ./documents`.)

### 1) Split a PDF into images

```bash
pdfslice split ./documents
```

This scans the target folder for PDF files and creates a folder for each
PDF, for example:

```text
documents/
├── sample.pdf
└── sample/
    ├── sample.001.jpg
    ├── sample.002.jpg
    ├── sample.003.jpg
    ├── sample.pdf
    └── .pdfslice-manifest.json
```

The original PDF is preserved and copied into the generated output folder.

#### Directory search depth

```bash
pdfslice split ./documents --level 2
```

Use `--level` to control how deep the search should go when scanning nested
folders.

#### Flatten output

```bash
pdfslice split ./documents --flatten
```

This places each generated output folder at the input root instead of
beside each source PDF.

#### Custom filename template

```bash
pdfslice split ./documents --template "page-{{page_number}}.jpg"
```

Use `{{filename}}` and `{{page_number}}` placeholders to control the page
image filename (default: `{{filename}}.{{page_number}}.jpg`). Exactly one
`{{page_number}}` is required. The template is saved in the manifest, so
`gather`/`check` parse page numbers back out correctly without needing
`--template` repeated.

### 2) Gather images back into a PDF

```bash
pdfslice gather ./documents/sample
```

This rebuilds a combined PDF from the page images in the split unit folder
and **overwrites the original PDF in place** (same filename, same location).
A backup of the previous PDF (`sample.bak-<timestamp>.pdf`) is created first
by default — pass `--no-backup` to skip it.

If the PDF already reflects the current images (nothing has changed since
the last gather), the project skips unnecessary regeneration.

### 3) Check for missing page images

```bash
pdfslice check ./documents/sample
```

This reports missing pages without creating a PDF output. Exits with status
code 1 if any unit has missing pages.

## Common flags

- `--dry-run`: preview actions without writing files
- `--backup` / `--no-backup` (gather only, default on): back up the existing
  PDF before overwriting it
- `--template <string>` (split only): custom page-image filename template
- `--verbose`: print debug logging
- `--quiet`: print only errors
- `--log-file <path>`: write logs as JSON lines as well as console

## Example workflow

```bash
pdfslice split ./input --level 2
pdfslice check ./input/report
pdfslice gather ./input/report
```

## Project Structure

```text
src/pdfslice_py/
├── __init__.py
├── cli.py                 # click CLI: split, gather, check commands
├── discover.py            # find_pdfs, find_images_deep, page_image_name
├── filename_template.py   # {{filename}}/{{page_number}} template compiler
├── gather.py               # rebuild PDF from images / check-only mode
├── hash.py                 # streamed SHA-256 file hashing
├── logger.py                # verbose/quiet/log-file logger
├── manifest.py              # .pdfslice-manifest.json schema + read/write
└── split.py                 # PDF -> per-page JPG splitting
tests/
├── test_discover.py
├── test_filename_template.py
├── test_manifest.py
└── test_split_gather.py
```

## Running Tests

```bash
uv pip install -e ".[test]"
uv run pytest -v
```

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the relevant checks and tests
5. Open a pull request

## License

This project is licensed under the Creative Commons
Attribution-NonCommercial-ShareAlike 4.0 International License, matching the
[TypeScript original](https://github.com/DuckyMomo20012/pdfslice).

See [LICENSE.md](LICENSE.md) for the full text.

## Repository

- Original (TypeScript): https://github.com/DuckyMomo20012/pdfslice
- Author: DuckyMomo20012
