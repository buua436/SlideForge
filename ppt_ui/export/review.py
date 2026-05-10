from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from ppt_ui.export.contact_sheet import ShowcaseItem, build_demo_showcase
from ppt_ui.export.screenshots import export_pptx_screenshots


@dataclass(frozen=True)
class ReviewExportResult:
    screenshots: list[Path]
    showcase: Path


def build_screenshot_review(
    screenshots: Sequence[str | Path],
    showcase_path: str | Path,
    *,
    title: str = "SlideForge Component Gallery",
    subtitle: str = "Agent-driven PPT UI framework demo deck",
    items: Sequence[ShowcaseItem] | None = None,
) -> ReviewExportResult:
    """Build a contact sheet from existing screenshots."""

    paths = [Path(item) for item in screenshots]
    showcase = build_demo_showcase(paths, showcase_path, title=title, subtitle=subtitle, items=items)
    return ReviewExportResult(screenshots=paths, showcase=showcase)


def export_pptx_review(
    pptx_path: str | Path,
    screenshots_dir: str | Path,
    showcase_path: str | Path,
    *,
    width: int = 1920,
    height: int = 1080,
    title: str = "SlideForge Component Gallery",
    subtitle: str = "Agent-driven PPT UI framework demo deck",
    items: Sequence[ShowcaseItem] | None = None,
) -> ReviewExportResult:
    """Export screenshots and build a single review contact sheet."""

    screenshots = export_pptx_screenshots(pptx_path, screenshots_dir, width=width, height=height)
    return build_screenshot_review(screenshots, showcase_path, title=title, subtitle=subtitle, items=items)
