from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextOverflowResult:
    text: str
    truncated: bool = False


def apply_text_overflow(text: str, *, overflow: str = "fit", max_chars: int | None = None) -> TextOverflowResult:
    """Apply renderer-independent text overflow rules."""

    strategy = overflow.lower().strip()
    if strategy != "truncate" or max_chars is None or max_chars <= 0:
        return TextOverflowResult(text=text)
    if len(text) <= max_chars:
        return TextOverflowResult(text=text)
    if max_chars <= 3:
        return TextOverflowResult(text=text[:max_chars], truncated=True)
    return TextOverflowResult(text=text[: max_chars - 3].rstrip() + "...", truncated=True)
