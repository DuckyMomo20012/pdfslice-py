"""Logging. Port of lib/logger.ts (winston) onto Python's stdlib logging.

Call sites use `logger.info("message", key=value, ...)` the way the
TypeScript original used `logger.info('message', { key: value })` — extra
keyword arguments are the "meta" object, printed as JSON after the message
and, if `log_file` is set, also written as a JSON line per record.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_COLOR_BY_LEVEL = {
    "debug": "\033[34m",  # blue
    "info": "\033[32m",  # green
    "warn": "\033[33m",  # yellow
    "error": "\033[31m",  # red
}
_RESET = "\033[0m"


class Logger:
    def __init__(self, level: str, log_file: str | Path | None = None) -> None:
        self._level = level
        self._log_file = Path(log_file) if log_file is not None else None
        self._order = {"debug": 0, "info": 1, "warn": 2, "error": 3}

    def _enabled(self, level: str) -> bool:
        return self._order[level] >= self._order[self._level]

    def _emit(self, level: str, message: str, meta: dict[str, Any]) -> None:
        if not self._enabled(level):
            return

        color = _COLOR_BY_LEVEL.get(level, "")
        extra = f" {json.dumps(meta)}" if meta else ""
        stream = sys.stderr if level == "error" else sys.stdout
        print(f"{color}{level}{_RESET}: {message}{extra}", file=stream)

        if self._log_file is not None:
            record = {
                "level": level,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **meta,
            }
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

    def debug(self, message: str, **meta: Any) -> None:
        self._emit("debug", message, meta)

    def info(self, message: str, **meta: Any) -> None:
        self._emit("info", message, meta)

    def warn(self, message: str, **meta: Any) -> None:
        self._emit("warn", message, meta)

    def error(self, message: str, **meta: Any) -> None:
        self._emit("error", message, meta)


def create_logger(
    verbose: bool = False, quiet: bool = False, log_file: str | Path | None = None
) -> Logger:
    level = "error" if quiet else "debug" if verbose else "info"
    return Logger(level=level, log_file=log_file)


# Keep the stdlib logging module importable/usable by consumers who'd rather
# wire pdfslice_py into their own logging config instead of using Logger above.
_stdlib_logger = logging.getLogger("pdfslice_py")
