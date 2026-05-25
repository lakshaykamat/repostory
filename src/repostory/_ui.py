"""Terminal output helpers — color, size, and duration formatting."""

from __future__ import annotations

import os
import sys


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stderr.isatty()


def _wrap(code: str, text: str) -> str:
    if not _supports_color():
        return text
    return f"\033[{code}m{text}\033[0m"


def bold(text: str) -> str:
    return _wrap("1", text)


def dim(text: str) -> str:
    return _wrap("2", text)


def green(text: str) -> str:
    return _wrap("32", text)


def yellow(text: str) -> str:
    return _wrap("33", text)


def red(text: str) -> str:
    return _wrap("31", text)


def cyan(text: str) -> str:
    return _wrap("36", text)


def fmt_ms(seconds: float) -> str:
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    return f"{seconds:.2f}s"


def fmt_size(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{int(num_bytes)}{unit}" if unit == "B" else f"{num_bytes:.1f}{unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f}TB"


def plural(n: int, singular: str, plural_form: str | None = None) -> str:
    word = plural_form if plural_form is not None else singular + "s"
    return f"{n:,} {singular if n == 1 else word}"
