# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SlideForge is a Python PPT UI component library for agent-generated presentation decks. Agents describe slides with a JSON DSL (or Python namespace API), and SlideForge renders reusable, themed, editable `.pptx` files using `python-pptx`.

## Commands

```bash
# Install dependencies (uses uv package manager)
uv sync --dev

# Run tests
uv run pytest

# Run a single test file
uv run pytest tests/test_parser.py

# Run a single test function
uv run pytest tests/test_parser.py::test_deck_from_dict_builds_pages_and_blocks

# Generate demo deck (outputs examples/demo.pptx + screenshots)
uv run python examples/demo_deck.py

# Skip screenshot export when generating demo
uv run python examples/demo_deck.py --no-screenshots
```

## Architecture

### Layered Model

The core principle: **Slide/Page owns page chrome. Layout owns space allocation. Component owns content rendering. Master owns shared deck-level page rules. Theme owns visual tokens.**

Components must not render page titles, footers, page numbers, or deck-wide decorations. A component receives a `Box` and renders only inside that box.

### Package Structure

- `ppt_ui/core/` — Fundamental types: `Deck`, `Page`, `Block`, `Component`, `Theme`, `SlideMaster`, `PageLayout`, `ComponentRegistry`, `DiagnosticBag`
- `ppt_ui/components/` — Concrete component implementations in `blocks.py` (TextComponent, MetricCardsComponent, LineChartComponent, etc.) and `registry.py` (default component registry factory)
- `ppt_ui/renderer/pptx_renderer.py` — `PptxRenderer`: low-level drawing abstraction over `python-pptx` (rect, text, line, circle, card, chart, table, icon)
- `ppt_ui/schema/` — JSON DSL parser: `deck_from_json()`, `deck_from_dict()`, validation pipeline
- `ppt_ui/icons/` — Icon provider system: IconifyApiProvider (default), IconifyJsonProvider, LocalSvgIconProvider, UrlTemplateIconProvider
- `ppt_ui/themes/` — Built-in theme JSON files (tech_blue, academic_clean, business_navy, data_dashboard, medical_teal, dark_tech, claude_warm)
- `ppt_ui/export/` — Screenshot export via PowerPoint COM automation (Windows only, requires pywin32)
- `ppt_ui/api.py` — Namespace API: `page`, `slide`, `chart`, `data`, `layout`, `block`, `basic`, `table`, `narrative`, `media`, `master`, `theme`

### Key Data Flow

1. **JSON DSL path**: `deck_from_json(path)` → parse/validate → `Deck` object → `deck.render(output_path)` → `PptxRenderer` → `.pptx` file
2. **Python API path**: `Deck()` → `deck.add_page(page.standard(...))` → `deck.render(path)`
3. **Render lifecycle per page**: resolve master → render background → render back chrome (accent bar, title, subtitle) → resolve layout → render blocks/components → render fore chrome (footer, page number)

### Component Type Naming

Components use `family.variant` names registered in `ComponentRegistry`:
- `basic.text`, `data.metric_cards`, `data.progress`
- `chart.line`, `chart.bar`, `chart.pie`, `chart.donut`
- `table.comparison`, `table.basic`
- `narrative.timeline`, `narrative.process_flow`, `narrative.roadmap`
- `media.icon`, `media.image`

### Layout System

All coordinates use **inches**. Two layout modes:
- **grid**: `col` (1-based), `span`, `row`, `row_span` — resolved inside page's content grid (default 12×6)
- **absolute**: `x`, `y`, `w`, `h` — direct inch placement

### Theme System

Themes are JSON files under `ppt_ui/themes/`. Theme loading supports: built-in names (`"default_blue"`), file paths, directory themes (`theme.json` entry), inline dicts, and `extends` inheritance. Token references like `{colors.primary}` are resolved in component defaults.

### Diagnostics

Validation produces structured `Diagnostic` objects (error/warning/info) with codes like `UNKNOWN_COMPONENT_TYPE`, `CHART_SERIES_LENGTH_MISMATCH`. Use `DiagnosticBag` during parsing; `DiagnosticError` is raised on blocking errors. Diagnostics are stored on `deck.diagnostics`.

## DSL Version

The current target schema version is `0.2`. The DSL uses `pages` (not `slides`) at the top level, and component-specific data lives under `props`.
