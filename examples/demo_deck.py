from __future__ import annotations

import sys
import argparse
import json
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ppt_ui.export import ScreenshotExportError, ShowcaseItem, build_demo_showcase, export_pptx_screenshots
from ppt_ui import builtin_theme_names
from ppt_ui.schema.parser import deck_from_json
from ppt_ui.schema.parser import deck_from_dict


SHOWCASE_ITEMS = [
    ShowcaseItem("page.cover", "cover page chrome"),
    ShowcaseItem("page.section", "section transition"),
    ShowcaseItem("basic.text", "text and bullets"),
    ShowcaseItem("data.metric_cards", "metric cards"),
    ShowcaseItem("data.progress", "progress bars"),
    ShowcaseItem("chart.line/bar", "editable shape charts"),
    ShowcaseItem("chart.pie/donut", "native PPT charts"),
    ShowcaseItem("table.comparison", "comparison table"),
    ShowcaseItem("narrative.timeline", "status timeline"),
    ShowcaseItem("narrative.process_flow", "process cards"),
    ShowcaseItem("narrative.roadmap", "roadmap bars"),
    ShowcaseItem("media.icon", "icon source gallery"),
]


def _theme_slug(theme_name: str) -> str:
    return theme_name.removeprefix("theme.").replace(".", "_")


def _render_deck_with_theme(source: Path, theme_name: str, output: Path) -> None:
    data = json.loads(source.read_text(encoding="utf-8"))
    data["theme"] = theme_name
    deck = deck_from_dict(data, base_dir=source.parent)
    deck.render(output)


def _export_assets(output: Path, screenshots_dir: Path, showcase_path: Path, *, showcase_title: str, showcase_subtitle: str) -> None:
    screenshots = export_pptx_screenshots(output, screenshots_dir)
    print(f"Generated {len(screenshots)} screenshots in {screenshots_dir}")
    showcase = build_demo_showcase(
        screenshots,
        showcase_path,
        title=showcase_title,
        subtitle=showcase_subtitle,
        items=SHOWCASE_ITEMS,
    )
    print(f"Generated showcase image {showcase}")


def _render_theme_demos(source: Path, output_dir: Path, themes: Sequence[str], *, no_screenshots: bool) -> None:
    custom_demos_dir = source.parent / "demos"
    for theme_name in themes:
        slug = _theme_slug(theme_name)
        theme_dir = output_dir / slug
        theme_dir.mkdir(parents=True, exist_ok=True)
        output = theme_dir / "demo.pptx"
        custom_json = custom_demos_dir / f"{slug}.json"
        deck_source = custom_json if custom_json.exists() else source
        _render_deck_with_theme(deck_source, theme_name, output)
        print(f"Generated {output}")
        if not no_screenshots:
            _export_assets(
                output,
                theme_dir / "screenshots",
                theme_dir / "showcase.png",
                showcase_title=f"SlideForge Theme Demo: {slug}",
                showcase_subtitle=f"{theme_name} · Agent-driven PPT UI framework",
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a SlideForge example deck from namespaced JSON DSL.")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).with_name("demo.pptx")),
        help="Output PPTX path. Defaults to examples/demo.pptx.",
    )
    parser.add_argument(
        "--screenshots-dir",
        default=str(Path(__file__).with_name("demo_screenshots")),
        help="Directory for per-slide PNG screenshots. It is overwritten on each run.",
    )
    parser.add_argument(
        "--no-screenshots",
        action="store_true",
        help="Skip PNG screenshot export.",
    )
    parser.add_argument(
        "--showcase",
        default=str(Path(__file__).with_name("demo_showcase.png")),
        help="Output path for the combined screenshot showcase. Defaults to examples/demo_showcase.png.",
    )
    parser.add_argument(
        "--theme-demos-dir",
        default=str(Path(__file__).with_name("theme_demos")),
        help="Directory where demo assets for every built-in theme are written.",
    )
    parser.add_argument(
        "--skip-theme-demos",
        action="store_true",
        help="Only generate the primary demo output and skip per-theme demo folders.",
    )
    args = parser.parse_args()

    source = Path(__file__).with_name("sample_deck.json")
    output = Path(args.output)
    deck = deck_from_json(source)
    deck.render(output)
    print(f"Generated {output}")

    if not args.no_screenshots:
        try:
            _export_assets(
                output,
                Path(args.screenshots_dir),
                Path(args.showcase),
                showcase_title="SlideForge Component Gallery",
                showcase_subtitle="Agent-driven PPT UI framework demo deck",
            )
        except ScreenshotExportError as exc:
            raise SystemExit(f"Screenshot export failed: {exc}") from exc

    if not args.skip_theme_demos:
        try:
            _render_theme_demos(source, Path(args.theme_demos_dir), builtin_theme_names(), no_screenshots=args.no_screenshots)
        except ScreenshotExportError as exc:
            raise SystemExit(f"Theme demo screenshot export failed: {exc}") from exc


if __name__ == "__main__":
    main()
