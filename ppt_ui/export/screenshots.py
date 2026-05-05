from __future__ import annotations

import re
import shutil
from pathlib import Path


class ScreenshotExportError(RuntimeError):
    """Raised when PPTX slide screenshots cannot be exported."""


def export_pptx_screenshots(
    pptx_path: str | Path,
    output_dir: str | Path,
    *,
    width: int = 1920,
    height: int = 1080,
) -> list[Path]:
    """Export each slide in a PPTX file as PNG screenshots.

    This uses PowerPoint COM automation on Windows because python-pptx writes
    editable decks but does not render slides to images.
    """

    pptx = Path(pptx_path).resolve()
    screenshots_dir = Path(output_dir).resolve()
    if not pptx.exists():
        raise ScreenshotExportError(f"PPTX file does not exist: {pptx}")

    temp_dir = screenshots_dir.with_name(f"{screenshots_dir.name}__tmp")
    _reset_directory(temp_dir)
    try:
        exported = _export_with_powerpoint(pptx, temp_dir, width, height)
        normalized = _normalize_exported_names(exported)
        _replace_directory(temp_dir, screenshots_dir)
        return [screenshots_dir / path.name for path in normalized]
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def _reset_directory(path: Path) -> None:
    if path.exists():
        if not path.is_dir():
            raise ScreenshotExportError(f"Screenshot target is not a directory: {path}")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _replace_directory(source: Path, target: Path) -> None:
    if target.exists():
        if not target.is_dir():
            raise ScreenshotExportError(f"Screenshot target is not a directory: {target}")
        shutil.rmtree(target)
    source.rename(target)


def _export_with_powerpoint(pptx: Path, output_dir: Path, width: int, height: int) -> list[Path]:
    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        raise ScreenshotExportError(
            "PowerPoint screenshot export requires pywin32 on Windows. "
            "Run `uv sync --dev` to install project dependencies."
        ) from exc

    pythoncom.CoInitialize()
    app = None
    presentation = None
    try:
        app = win32com.client.DispatchEx("PowerPoint.Application")
        presentation = app.Presentations.Open(str(pptx), ReadOnly=True, Untitled=False, WithWindow=False)
        presentation.Export(str(output_dir), "PNG", width, height)
        return sorted(
            [path for path in output_dir.iterdir() if path.suffix.lower() == ".png"],
            key=_slide_index,
        )
    except Exception as exc:
        raise ScreenshotExportError(
            "Failed to export PPTX screenshots via PowerPoint. "
            "Please make sure Microsoft PowerPoint is installed and available."
        ) from exc
    finally:
        if presentation is not None:
            presentation.Close()
        if app is not None:
            app.Quit()
        pythoncom.CoUninitialize()


def _normalize_exported_names(paths: list[Path]) -> list[Path]:
    normalized: list[Path] = []
    for path in paths:
        if not path.exists():
            matches = sorted(path.parent.glob(f"{path.stem}.*"))
            if not matches:
                continue
            path = matches[0]

        index = _slide_index(path)
        target = path.with_name(f"slide_{index:02d}.png")
        if target.exists() and target != path:
            target.unlink()
        path.rename(target)
        normalized.append(target)
    return normalized


def _slide_index(path: Path) -> int:
    match = re.search(r"(\d+)", path.stem)
    if match is None:
        return 0
    return int(match.group(1))
