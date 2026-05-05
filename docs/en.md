# SlideForge User Documentation

> Pre-v1 status: the codebase is being migrated to the `Page + Blocks + Master` architecture defined in [docs/design.md](design.md). Some older `slide.*` and single-component-per-slide API sections in this document are no longer the latest implementation. For now, use `docs/design.md`, `examples/sample_deck.json`, and tests as the source of truth. The official user docs will be regenerated after the API stabilizes.

SlideForge is a Python PPT UI component library designed for agent-generated presentations. It describes decks with structured JSON DSL or a Python namespace API, routes those descriptions through a component registry and parser, and renders editable `.pptx` files with `python-pptx`. Users and agents do not need to call low-level APIs such as `add_textbox` or `add_shape`; they choose components such as `slide.title`, `data.metric_cards`, `chart.line`, and `narrative.timeline`.

This document is based on the current codebase. APIs marked as “Implemented” exist in the current project. APIs marked as “Planned” are architectural goals or roadmap items and should not be treated as available.

## Table Of Contents

- [Introduction](#introduction)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Directory Structure](#directory-structure)
- [Core Concepts](#core-concepts)
- [JSON DSL Guide](#json-dsl-guide)
- [Python API Guide](#python-api-guide)
- [Component API](#component-api)
- [Theme System](#theme-system)
- [Layout System](#layout-system)
- [Renderer](#renderer)
- [Export Screenshots](#export-screenshots)
- [Full Examples](#full-examples)
- [Agent Usage Guide](#agent-usage-guide)
- [Component Extension Guide](#component-extension-guide)
- [FAQ](#faq)
- [Roadmap](#roadmap)

## Introduction

SlideForge helps agents generate professional, consistent, editable PowerPoint decks without writing verbose `python-pptx` shape code. It models a deck as a component tree. Components own layout, theme tokens, typography, cards, tables, charts, and narrative patterns. Agents only need to produce semantic JSON.

Compared with direct `python-pptx` usage:

| Approach | Main concern | Result |
| --- | --- | --- |
| Direct `python-pptx` | Coordinates, shapes, textboxes, colors, font sizes | Flexible but repetitive, hard to maintain, easy for agents to make inconsistent pages |
| SlideForge | Component type, content fields, theme tokens, layout regions | Consistent style, reusable components, editable `.pptx` output |

SlideForge is suitable for thesis defenses, project proposals, data reports, business presentations, automated weekly reports, experiment summaries, operational analysis, retrospectives, and agent-generated reporting workflows.

## Architecture

SlideForge uses this rendering pipeline:

```text
JSON DSL
  -> Component Registry / Parser
  -> Deck / Slide / Component Tree
  -> PptxRenderer
  -> editable .pptx
```

| Layer | Responsibility | Current implementation |
| --- | --- | --- |
| JSON DSL | Structured input from an agent or user. | `examples/sample_deck.json`, `ppt_ui/schema/deck_schema.py` |
| Component Registry / Parser | Routes `type` values to component factories and avoids a large parser if/else chain. | `ppt_ui/core/registry.py`, `ppt_ui/schema/parser.py` |
| Deck / Slide / Component Tree | Internal presentation model containing theme and slide components. | `Deck`, `Slide`, `Component` |
| PptxRenderer | Central rendering layer wrapping `python-pptx`. | `ppt_ui/renderer/pptx_renderer.py` |
| editable `.pptx` | Final PowerPoint file with editable objects. | `Deck.render(path)` |

Components should not expose `python-pptx` details to agents. The stable agent-facing interface is JSON DSL; Python users can also assemble decks with the namespace API.

## Installation

### Requirements

| Item | Requirement |
| --- | --- |
| Python | `>=3.10` |
| Package manager | `uv` recommended |
| PPTX generation | `python-pptx>=1.0.2` |
| Screenshot export | Windows + Microsoft PowerPoint + `pywin32` |

### Install Dependencies

```bash
uv sync --dev
```

If you only need `.pptx` generation, the core dependency is `python-pptx`. If you need per-slide PNG screenshots, Windows requires `pywin32` and a local PowerPoint installation.

## Quick Start

Generate the demo deck:

```bash
uv run python examples/demo_deck.py
```

Default output:

| Output | Path |
| --- | --- |
| PPTX | `examples/demo.pptx` |
| Screenshot directory | `examples/demo_screenshots/` |
| Combined showcase image | `examples/demo_showcase.png` |
| Per-theme demo folders | `examples/theme_demos/<theme_name>/` |

Each per-theme folder contains:

| Output | Path |
| --- | --- |
| PPTX | `examples/theme_demos/<theme_name>/demo.pptx` |
| Screenshot directory | `examples/theme_demos/<theme_name>/screenshots/` |
| Combined showcase image | `examples/theme_demos/<theme_name>/showcase.png` |

Specify output path:

```bash
uv run python examples/demo_deck.py --output examples/custom_demo.pptx
```

Specify screenshot directory:

```bash
uv run python examples/demo_deck.py --screenshots-dir examples/custom_screenshots
```

Disable screenshot export:

```bash
uv run python examples/demo_deck.py --no-screenshots
```

Skip per-theme demo folders:

```bash
uv run python examples/demo_deck.py --skip-theme-demos
```

Generate a PPTX from a custom JSON file:

```python
from ppt_ui.schema.parser import deck_from_json

deck = deck_from_json("examples/sample_deck.json")
deck.render("examples/demo.pptx")
```

The current `examples/demo_deck.py` always reads `examples/sample_deck.json`. A CLI `--source` option is planned.

## Directory Structure

| Path | Responsibility | Main classes/functions | Relationship |
| --- | --- | --- | --- |
| `ppt_ui/core/presentation.py` | Deck management. | `Deck.add_slide()`, `Deck.render()` | Calls `PptxRenderer` to write PPTX |
| `ppt_ui/core/slide.py` | Slide base class. | `Slide.render(ctx, box)` | Base for all page-level components |
| `ppt_ui/core/component.py` | Component base class and render context. | `Component`, `RenderContext` | Shared lifecycle for slides and blocks |
| `ppt_ui/core/theme.py` | Theme tokens and theme loading. | `Theme`, `ThemeLoader`, `ThemeRegistry`, `ColorTokens`, `FontTokens`, `get_theme()` | Consumed by renderer and components |
| `ppt_ui/themes/` | Built-in JSON theme definitions. | `*.json` theme files | Loaded by `ThemeLoader` through the theme registry |
| `ppt_ui/core/layout.py` | Layout region calculations. | `Box`, `PageBox` | Components split inch-based regions |
| `ppt_ui/core/registry.py` | Component registry. | `ComponentRegistry` | Parser creates slides by `type` |
| `ppt_ui/components/basic.py` | Basic block components. | `Title`, `TextBlock`, `Divider`, `Icon` | Internal/basic placeholder layer |
| `ppt_ui/components/slides.py` | Slide and layout components. | `TitleSlide`, `SectionSlide`, `GridSlide`, etc. | Powers `slide.*` and `layout.*` |
| `ppt_ui/components/data.py` | Data and chart components. | `MetricCard`, `LineChartSlide`, `ComparisonTableSlide`, etc. | Powers `data.*`, `chart.*`, `table.*` |
| `ppt_ui/components/narrative.py` | Narrative and analysis components. | `TimelineSlide`, `ProcessFlowSlide`, `SWOTSlide`, etc. | Powers `narrative.*` |
| `ppt_ui/renderer/pptx_renderer.py` | PPTX rendering layer. | `PptxRenderer` and helper methods | Wraps `python-pptx` |
| `ppt_ui/schema/deck_schema.py` | JSON TypedDict definitions. | `DeckDict`, `SlideDict` | Lightweight typing, not full validation |
| `ppt_ui/schema/parser.py` | JSON to Deck/Slide parser. | `deck_from_json()`, `deck_from_dict()`, `build_default_registry()` | Registers namespace types and legacy aliases |
| `ppt_ui/export/screenshots.py` | PPTX screenshot export. | `export_pptx_screenshots()` | Uses PowerPoint COM and overwrites output directory |
| `ppt_ui/icons/provider.py` | Frontend-style icon provider adapters. | `IconRegistry`, `IconifyApiProvider`, `IconifyJsonProvider`, `LocalSvgIconProvider` | Resolves Iconify-compatible SVG sources for PPT rendering |
| `ppt_ui/api.py` | Public namespace API. | `chart`, `data`, `layout`, `narrative`, `slide`, `table` | Recommended Python entrypoint |
| `examples/demo_deck.py` | Demo generation script. | `main()` | Reads sample JSON, generates PPTX and screenshots |
| `examples/sample_deck.json` | Agent JSON DSL sample. | namespace `type` values | Demo data source |
| `tests/` | Tests. | `test_parser.py` | Covers parser, registry, namespace API |

## Core Concepts

### Deck

`Deck` manages a full presentation. It contains a theme, title, and slide list. Calling `Deck.render(path)` creates a `PptxRenderer`, renders every slide, and saves an editable `.pptx`.

| Attribute/method | Type | Description |
| --- | --- | --- |
| `slides` | `list[Slide]` | Slide component list |
| `theme` | `Theme` | Active theme |
| `title` | `str` | Deck title |
| `add_slide(slide)` | method | Append a slide |
| `render(output_path)` | method | Generate PPTX and return the path |

```python
from ppt_ui import Deck, slide

deck = Deck(title="Quarterly Review")
deck.add_slide(slide.title(title="Quarterly Review", subtitle="Generated by SlideForge"))
deck.render("examples/review.pptx")
```

Note: `Deck.render()` only writes PPTX. Screenshot export is handled by `ppt_ui.export.export_pptx_screenshots()` or `examples/demo_deck.py`.

### Slide

`Slide` is the page-level component base class. Each slide implements:

```python
def render(self, ctx: RenderContext, box: PageBox) -> None:
    ...
```

Lifecycle:

1. `Deck.render()` creates a `PptxRenderer`.
2. `PptxRenderer.render_deck()` creates a blank PowerPoint slide.
3. The renderer creates `RenderContext(slide, theme, renderer)`.
4. The slide component draws inside a `PageBox`.

To add a slide, subclass `Slide`, define dataclass fields, implement `render()`, and register it in `ComponentRegistry`.

### Component

`Component` is the block-level base class and can be reused by multiple slide wrappers. For example, `MetricCard` is a block component; `MetricCardsSlide` arranges multiple cards into one page.

```python
@dataclass
class Component:
    def render(self, ctx: RenderContext, box: Box) -> None:
        raise NotImplementedError
```

### RenderContext

| Field | Description |
| --- | --- |
| `slide` | Current `python-pptx` slide object |
| `theme` | Current `Theme` |
| `renderer` | Current `PptxRenderer` |

Components should draw through `ctx.renderer` instead of scattering low-level `python-pptx` calls throughout component code.

### Box

`Box` is an inch-based layout region.

| Method | Description |
| --- | --- |
| `inset(left, top, right=None, bottom=None)` | Returns an inner region with padding |
| `split_cols(count, gutter=0.0)` | Splits a region into columns |
| `split_rows(count, gutter=0.0)` | Splits a region into rows |
| `top(height)` | Returns the top region |
| `bottom(height)` | Returns the bottom region |
| `remaining_below(top_height, gap=0.0)` | Returns the remaining region below a top slice |

### Theme

`Theme` is the design token container: colors, typography, spacing, radius, shadow, chart palette, and component-level styles. The default built-in theme is `theme.tech_blue`.

### ComponentRegistry

`ComponentRegistry` routes DSL `type` values to component factories. It supports namespace types:

```json
{"type": "chart.line"}
```

It also supports family + variant routing:

```json
{"type": "chart", "variant": "line"}
```

The default registry also keeps legacy aliases such as `title_slide`, `metric_cards`, and `comparison_table`.

## JSON DSL Guide

### Top-Level Structure

The current parser implements only `title`, `theme`, and `slides`. Other top-level fields are planned or controlled externally by scripts.

```json
{
  "title": "SlideForge Demo",
  "theme": "default_blue",
  "slides": [
    {
      "type": "slide.title",
      "title": "Reusable PPT UI Component Library",
      "subtitle": "For defenses, project proposals, data reports, and business presentations"
    }
  ]
}
```

| Field | Type | Required | Default | Status | Description |
| --- | --- | --- | --- | --- | --- |
| `title` | `string` | No | `"SlideForge Deck"` | Implemented | Deck title |
| `theme` | `string/object` | No | `default_blue` | Implemented | Built-in name, external JSON file, external theme directory, or inline theme object |
| `slides` | `array<object>` | No | `[]` | Implemented | Slide list |
| `metadata` | `object` | No | none | Planned | Ignored by current parser |
| `export` | `object` | No | none | Planned | Currently controlled by demo CLI arguments |
| `screenshot` | `object` | No | none | Planned | Currently controlled by `--screenshots-dir` and `--no-screenshots` |
| `page_size` | `object/string` | No | theme size | Planned | Currently controlled by `Theme.slide_width/slide_height` |
| `language` | `string` | No | none | Planned | Ignored by current parser |
| `author` | `string` | No | none | Planned | Ignored by current parser |
| `date` | `string` | No | none | Planned | Ignored by parser; `slide.title.date` is available for cover pages |
| `version` | `string` | No | none | Planned | Ignored by current parser |

### Common Slide Fields

Different components support different fields. The current parser maps fields directly into component dataclasses and does not implement a universal `props/style/layout` merge layer.

| Field | Type | Status | Description |
| --- | --- | --- | --- |
| `type` | `string` | Implemented | Must exist in the registry, for example `chart.line` |
| `variant` | `string` | Implemented | Optional routing through `type + variant`, for example `{"type": "chart", "variant": "line"}` |
| `title` | `string` | Implemented for most components | Main slide title |
| `subtitle` | `string` | Implemented for most components | Slide subtitle |
| `content` | `string/object` | Planned | No universal handling yet |
| `items` | `array` | Partially implemented | Used by `layout.contents`, `layout.grid`, `data.progress_bars`, `narrative.timeline`, etc. |
| `blocks` | `array` | Planned | No generic block tree parser yet |
| `cards` | `array` | Partially implemented | Used by `data.metric_cards`, `layout.three_info_cards` |
| `data` | `object` | Planned | Charts currently use direct fields such as `categories`, `series`, and `segments` |
| `style` | `object` | Planned | No per-slide style override yet |
| `layout` | `object` | Planned | No per-slide layout override yet |
| `footer` | `string/object` | Planned | Most slides call `add_footer()` internally |
| `notes` | `string` | Planned | Speaker notes are not written yet |
| `metadata` | `object` | Planned | Ignored by current parser |
| `hidden` | `boolean` | Planned | Current parser does not skip slides |
| `page_number` | `string/number` | Planned | Only `layout.header_footer.page` displays page text |

### Namespace Type Convention

Agents should use namespace types.

| Namespace | Implemented | Planned |
| --- | --- | --- |
| `slide` | `slide.title`, `slide.section`, `slide.conclusion`, `slide.qa` | `slide.content` |
| `layout` | `layout.contents`, `layout.two_column`, `layout.grid`, `layout.image_text`, `layout.three_info_cards`, `layout.quote`, `layout.header_footer`, `layout.design_spec` | `layout.cards`, `layout.blank` |
| `data` | `data.metric_card`, `data.metric_cards`, `data.progress_bars`, `data.gantt`, `data.heatmap`, `data.ab_comparison`, `data.highlight_insight`, `data.annotations` | `data.progress` alias |
| `chart` | `chart.line`, `chart.bar`, `chart.pie`, `chart.donut` | `chart.scatter`, `chart.area`, more charts |
| `table` | `table.comparison` | `table.basic` |
| `narrative` | `narrative.timeline`, `narrative.process_flow`, `narrative.roadmap`, `narrative.swot`, `narrative.problem_solution`, `narrative.logic_pyramid`, `narrative.risk_table`, `narrative.milestone`, `narrative.relation_table`, `narrative.story_structure` | More analysis templates |
| `media` | `media.icon` | `media.image` enhancements |
| `theme` | `theme.tech_blue`, `theme.academic_clean`, `theme.business_navy`, `theme.data_dashboard`, `theme.medical_teal`, `theme.dark_tech`, `theme.claude_warm` | More external theme packages |

## Python API Guide

Import namespace APIs from `ppt_ui`:

```python
from ppt_ui import Deck, chart, data, layout, narrative, slide, table

deck = Deck(title="SlideForge Demo")
deck.add_slide(slide.title(title="Reusable PPT UI Component Library", subtitle="Agent-driven PPT UI Framework"))
deck.add_slide(
    data.metric_cards(
        title="Metric Overview",
        cards=[
            data.metric_card(label="Accuracy", value="92.3%", delta="+3.1%", note="vs. previous", icon="AC"),
            data.metric_card(label="AUC", value="0.948", delta="+0.026", note="validation", icon="AU"),
        ],
    )
)
deck.add_slide(
    chart.line(
        title="Trend Analysis",
        categories=["4/29", "5/6", "5/13"],
        series=[{"name": "Metric A", "values": [320, 540, 580]}],
    )
)
deck.render("examples/api_demo.pptx")
```

JSON entrypoint:

```python
from ppt_ui.schema.parser import deck_from_json

deck = deck_from_json("examples/sample_deck.json")
deck.render("examples/demo.pptx")
```

## Component API

### Component Status Matrix

| Type | Python API | Status |
| --- | --- | --- |
| `slide.title` | `slide.title(...)` | Implemented |
| `slide.section` | `slide.section(...)` | Implemented |
| `slide.content` | none | Planned |
| `slide.conclusion` | `slide.conclusion(...)` | Implemented |
| `slide.qa` | `slide.qa(...)` | Implemented |
| `layout.two_column` | `layout.two_column(...)` | Implemented |
| `layout.grid` | `layout.grid(...)` | Implemented |
| `layout.cards` | none | Planned |
| `layout.blank` | none | Planned |
| `data.metric_card` | `data.metric_card(...)` | Implemented; JSON wraps it as a single-card slide |
| `data.metric_cards` | `data.metric_cards(...)` | Implemented |
| `data.progress` | none | Planned |
| `data.progress_bars` | `data.progress_bars(...)` | Implemented |
| `data.gantt` | `data.gantt(...)` | Implemented |
| `chart.line` | `chart.line(...)` | Implemented |
| `chart.bar` | `chart.bar(...)` | Implemented |
| `chart.pie` | `chart.pie(...)` | Implemented |
| `chart.donut` | `chart.donut(...)` | Implemented |
| `table.basic` | none | Planned |
| `table.comparison` | `table.comparison(...)` | Implemented |
| `narrative.timeline` | `narrative.timeline(...)` | Implemented |
| `narrative.process_flow` | `narrative.process_flow(...)` | Implemented |
| `narrative.roadmap` | `narrative.roadmap(...)` | Implemented |
| `narrative.swot` | `narrative.swot(...)` | Implemented |
| `narrative.problem_solution` | `narrative.problem_solution(...)` | Implemented |
| `narrative.logic_pyramid` | `narrative.logic_pyramid(...)` | Implemented |
| `media.image` | local image path block | Implemented |
| `media.icon` | remote Iconify-compatible icon block | Implemented |

### slide.title

Purpose: cover slide for reports, project openings, and presentation title pages.

```python
deck.add_slide(slide.title(title="Reusable PPT UI Component Library", subtitle="For data reports", presenter="SlideForge", date="2026.05.03"))
```

```json
{"type": "slide.title", "title": "Reusable PPT UI Component Library", "subtitle": "For data reports", "presenter": "SlideForge", "date": "2026.05.03", "logo": "YOUR LOGO"}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `type` | `string` | JSON yes | none | `slide.title` |
| `title` | `string` | yes | `""` | Main title |
| `subtitle` | `string` | no | `""` | Subtitle |
| `presenter` | `string` | no | `""` | Presenter |
| `date` | `string` | no | `""` | Date text |
| `logo` | `string` | no | `"YOUR LOGO"` | Top-left logo text |

Default style: white background, blue-purple accent bar, large title, lightweight geometric decoration, and a subtle footer. Long titles may be auto-fit by PowerPoint.

### slide.section

Purpose: chapter transition slide.

```python
deck.add_slide(slide.section(number="01", title="Layout Components", subtitle="Build standard report pages quickly", keywords=["Title", "Two Column", "Grid"]))
```

```json
{"type": "slide.section", "number": "01", "title": "Layout Components", "subtitle": "Build standard report pages quickly", "keywords": ["Title", "Two Column", "Grid"]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `type` | `string` | JSON yes | none | `slide.section` |
| `number` | `string` | no | `"01"` | Section number |
| `title` | `string` | yes | `""` | Section title |
| `subtitle` | `string` | no | `""` | Section description |
| `keywords` | `array<string>` | no | `[]` | Keyword pills |

Default style: large number, section heading, keyword pills, and light progress decoration. Use 3-6 keywords.

### slide.conclusion

Purpose: conclusion and outlook slide.

```python
deck.add_slide(slide.conclusion(points=[{"title": "Reuse", "description": "Reduce repeated layout work"}], closing="Build better decks together."))
```

```json
{"type": "slide.conclusion", "title": "Conclusion", "points": [{"title": "Reuse", "description": "Reduce repeated layout work"}], "closing": "Build better decks together."}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `type` | `string` | JSON yes | none | `slide.conclusion` |
| `title` | `string` | no | built-in default | Slide title |
| `points` | `array<object>` | no | `[]` | Conclusion cards |
| `points[].title` | `string` | yes | none | Card title |
| `points[].description` | `string` | yes | none | Card description |
| `closing` | `string` | no | built-in text | Closing line |

Default style: gradient hero container, conclusion cards, emphasized closing line. Prefer 2-3 points.

### slide.qa

Purpose: Q&A ending slide.

```python
deck.add_slide(slide.qa(project="SlideForge", description="Discuss component design, themes, and agent pipelines."))
```

```json
{"type": "slide.qa", "title": "Q&A", "subtitle": "Thank you", "project": "SlideForge", "description": "Discuss component design, themes, and agent pipelines."}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `type` | `string` | JSON yes | none | `slide.qa` |
| `title` | `string` | no | `"Q&A"` | Main visual text |
| `subtitle` | `string` | no | built-in text | Subtitle |
| `project` | `string` | no | `"SlideForge"` | Project name |
| `description` | `string` | no | built-in text | Description |

Default style: centered Q&A title, project name, description card, and light decoration.

### layout.contents

Purpose: table of contents slide.

```python
deck.add_slide(layout.contents(items=[{"number": "01", "title": "Layout Components"}]))
```

```json
{"type": "layout.contents", "title": "Contents", "subtitle": "CONTENTS", "items": [{"number": "01", "title": "Layout Components"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `title` | `string` | no | `"目录"` | Slide title |
| `subtitle` | `string` | no | `"CONTENTS"` | Subtitle |
| `items` | `array<object>` | yes | `[]` | Contents items |
| `items[].number` | `string` | yes | none | Item number |
| `items[].title` | `string` | yes | none | Item title |

Default style: centered card list with section labels. Use 3-6 items.

### layout.two_column

Purpose: two-column content slide for side-by-side explanation or comparison.

```python
deck.add_slide(layout.two_column(title="Why Components", left_title="Agent Friendly", left_items=["Semantic input"], right_title="MVP Scope", right_items=["JSON to PPTX"]))
```

```json
{"type": "layout.two_column", "title": "Why Components", "left_title": "Agent Friendly", "left_items": ["Semantic input"], "right_title": "MVP Scope", "right_items": ["JSON to PPTX"]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `title` | `string` | yes | `""` | Slide title |
| `left_title` | `string` | yes | `""` | Left column title |
| `left_items` | `array<string>` | yes | `[]` | Left bullet items |
| `right_title` | `string` | yes | `""` | Right column title |
| `right_items` | `array<string>` | yes | `[]` | Right bullet items |

Default style: two lightweight cards, section labels, and bullet lists. Prefer 3-5 bullets per column.

### layout.grid

Purpose: grid information cards for capability matrices, module lists, and rules.

```python
deck.add_slide(layout.grid(title="Grid Layout", columns=3, items=[{"title": "Title", "description": "Consistent heading area", "icon": "T"}]))
```

```json
{"type": "layout.grid", "title": "Grid Layout", "columns": 3, "items": [{"title": "Title", "description": "Consistent heading area", "icon": "T"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `title` | `string` | yes | `""` | Slide title |
| `subtitle` | `string` | no | built-in text | Subtitle |
| `columns` | `integer` | no | `3` | Number of columns |
| `items` | `array<object>` | yes | `[]` | Grid items |
| `items[].title` | `string` | yes | none | Card title |
| `items[].description` | `string` | no | `""` | Card description |
| `items[].icon` | `string` | no | `""` | Text icon placeholder |

Default style: light cards and circular icon placeholders. Large `columns` values can make content cramped.

### layout.image_text

Purpose: image-text mixed layout. Currently it renders a visual placeholder instead of loading a real image.

```python
deck.add_slide(layout.image_text(title="Image And Text", image_label="Visual", body="Core idea", bullets=["Text left, visual right"], image_side="right"))
```

```json
{"type": "layout.image_text", "title": "Image And Text", "image_label": "Visual", "body": "Core idea", "bullets": ["Text left, visual right"], "image_side": "right"}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `title` | `string` | yes | `""` | Slide title |
| `subtitle` | `string` | no | built-in text | Subtitle |
| `image_label` | `string` | no | `"Image"` | Visual placeholder label |
| `body` | `string` | no | `""` | Body text |
| `bullets` | `array<string>` | no | `[]` | Bullet points |
| `image_side` | `string` | no | `"right"` | `left` or `right` |

Default style: one visual placeholder card and one text card. Real image insertion is planned as `media.image`.

### layout.three_info_cards

Purpose: three information cards for capabilities, value pillars, or module summaries.

```python
deck.add_slide(layout.three_info_cards(title="Three Cards", cards=[{"title": "Product", "description": "Improve efficiency", "icon": "P"}]))
```

```json
{"type": "layout.three_info_cards", "title": "Three Cards", "cards": [{"title": "Product", "description": "Improve efficiency", "icon": "P"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `title` | `string` | yes | `""` | Slide title |
| `subtitle` | `string` | no | built-in text | Subtitle |
| `cards` | `array<object>` | yes | `[]` | Card list |
| `cards[].title` | `string` | yes | none | Card title |
| `cards[].description` | `string` | yes | none | Card description |
| `cards[].icon` | `string` | no | `""` | Text icon placeholder |

Default style: three light cards with circular icon placeholders. Prefer exactly three cards.

### layout.quote

Purpose: quote block for insight emphasis, expert quotes, or section transitions.

```python
deck.add_slide(layout.quote(title="Quote", quote="Technology should make business simpler.", source="SlideForge"))
```

```json
{"type": "layout.quote", "title": "Quote", "quote": "Technology should make business simpler.", "source": "SlideForge"}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `title` | `string` | yes | `""` | Slide title |
| `subtitle` | `string` | no | built-in text | Subtitle |
| `quote` | `string` | yes | `""` | Quote text |
| `source` | `string` | no | `""` | Quote source |

Default style: centered quote card with emphasized quotation mark. Keep quote text short.

### layout.header_footer

Purpose: header/footer placeholder and template rule slide.

```python
deck.add_slide(layout.header_footer(title="Header Footer", section="02", body="Content area", page="/ 12"))
```

```json
{"type": "layout.header_footer", "title": "Header Footer", "section": "02", "body": "Content area", "source": "Source: internal data", "page": "/ 12"}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `title` | `string` | yes | `""` | Slide title |
| `section` | `string` | no | `"01"` | Top-right section label |
| `body` | `string` | no | built-in text | Placeholder body |
| `source` | `string` | no | built-in text | Source text |
| `page` | `string` | no | `"/ 12"` | Page text |
| `subtitle` | `string` | no | built-in text | Subtitle |

Default style: title area, content frame, source text, and page text. It is not automatic pagination.

### layout.design_spec

Purpose: design-system specification slide for tokens and component rules.

```python
deck.add_slide(layout.design_spec(specs=["Title", "Body", "Accent", "Whitespace", "Radius", "Shadow"]))
```

```json
{"type": "layout.design_spec", "title": "Design Spec", "specs": ["Title", "Body", "Accent", "Whitespace", "Radius", "Shadow"]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `title` | `string` | no | built-in title | Slide title |
| `subtitle` | `string` | no | built-in text | Subtitle |
| `specs` | `array<string>` | yes | `[]` | Spec entries |

Default style: 2x3 rule grid. Prefer 4-6 items.

### data.metric_card

Purpose: single metric card. The Python API returns a block-level `MetricCard`; JSON `data.metric_card` is wrapped by the parser into a single-card `MetricCardsSlide`.

```python
card = data.metric_card(label="Accuracy", value="92.3%", delta="+3.1%", note="vs. previous", icon="AC")
```

```json
{"type": "data.metric_card", "title": "Single Metric", "label": "Accuracy", "value": "92.3%", "delta": "+3.1%", "note": "vs. previous", "icon": "AC"}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `label` | `string` | yes | none | Metric label |
| `value` | `string` | yes | none | Main value |
| `delta` | `string` | no | `""` | Change value; `+` uses success color, otherwise warning color |
| `note` | `string` | no | built-in text | Comparison note |
| `icon` | `string` | no | `""` | Text icon placeholder |

Default style: light rounded card, top-right icon, main value, and delta. JSON usage should include `title` to create a complete slide.

### data.metric_cards

Purpose: metric card group for experiment summaries, operational dashboards, business reviews, and weekly reports.

```python
deck.add_slide(data.metric_cards(title="Metric Overview", cards=[data.metric_card(label="AUC", value="0.948")]))
```

```json
{"type": "data.metric_cards", "title": "Metric Overview", "subtitle": "For data reports", "scenarios": "Experiment summary / Ops overview", "cards": [{"label": "Accuracy", "value": "92.3%", "delta": "+3.1%", "note": "vs. previous", "icon": "AC"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `title` | `string` | yes | `""` | Slide title |
| `subtitle` | `string` | no | `""` | Subtitle |
| `scenarios` | `string` | no | built-in text | Scenario note |
| `cards` | `array<object>` | yes | `[]` | Metric cards |
| `cards[].label` | `string` | yes | none | Metric label |
| `cards[].value` | `string` | yes | none | Main value |
| `cards[].delta` | `string` | no | `""` | Change value |
| `cards[].note` | `string` | no | built-in text | Comparison note |
| `cards[].icon` | `string` | no | `""` | Text icon placeholder |

Default style: horizontal metric cards plus an explanatory region. Prefer 2-4 cards.

### data.progress_bars

Purpose: progress bars for project progress, completion rate, and phase health.

```python
deck.add_slide(data.progress_bars(title="Project Progress", items=[{"label": "Implementation", "value": 0.6, "color": "7C3AED"}]))
```

```json
{"type": "data.progress_bars", "title": "Project Progress", "items": [{"label": "Implementation", "value": 0.6, "color": "7C3AED"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `title` | `string` | yes | `""` | Slide title |
| `subtitle` | `string` | no | built-in text | Subtitle |
| `items` | `array<object>` | yes | `[]` | Progress items |
| `items[].label` | `string` | yes | none | Name |
| `items[].value` | `number` | yes | none | 0-1 value; rendering clamps it |
| `items[].color` | `string` | no | theme primary | HEX color |

Default style: card container, light track, colored progress. `data.progress` is a planned alias.

### data.gantt

Purpose: Gantt chart for scheduling and delivery cadence.

```python
deck.add_slide(data.gantt(title="Project Plan", periods=["May", "Jun"], tasks=[{"label": "Design", "start": 0, "end": 1}]))
```

```json
{"type": "data.gantt", "title": "Project Plan", "periods": ["May", "Jun"], "tasks": [{"label": "Design", "start": 0, "end": 1, "color": "2563EB"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `periods` | `array<string>` | yes | `[]` | Timeline columns |
| `tasks` | `array<object>` | yes | `[]` | Tasks |
| `tasks[].label` | `string` | yes | none | Task name |
| `tasks[].start` | `integer` | yes | none | Start column index |
| `tasks[].end` | `integer` | yes | none | End column index |
| `tasks[].color` | `string` | no | automatic | HEX color |

Default style: light table background and colored bars. `start/end` are column indexes, not parsed dates.

### data.heatmap

Purpose: heatmap matrix for feature usage, cohort behavior, or scenario intensity.

```python
deck.add_slide(data.heatmap(title="Usage Heatmap", row_labels=["New"], col_labels=["Feature A"], values=[[68]]))
```

```json
{"type": "data.heatmap", "title": "Usage Heatmap", "row_labels": ["New"], "col_labels": ["Feature A"], "values": [[68]]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `row_labels` | `array<string>` | yes | `[]` | Row labels |
| `col_labels` | `array<string>` | yes | `[]` | Column labels |
| `values` | `array<array<number>>` | yes | `[]` | Value matrix |

Default style: values map to gray, light blue, and primary blue. Missing cells render as 0.

### data.ab_comparison

Purpose: A/B experiment result table.

```python
deck.add_slide(data.ab_comparison(title="Experiment Results", headers=["Metric", "A", "B"], rows=[["CTR", "4.1%", "4.8%"]], note="B performs better"))
```

```json
{"type": "data.ab_comparison", "title": "Experiment Results", "headers": ["Metric", "A", "B"], "rows": [["CTR", "4.1%", "4.8%"]], "note": "B performs better"}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `headers` | `array<string>` | yes | `[]` | Table headers |
| `rows` | `array<array<string>>` | yes | `[]` | Table rows |
| `note` | `string` | no | `""` | Bottom conclusion note |

Default style: uses the unified `add_table()` helper and a success-colored note. Keep row lengths aligned with headers.

### data.highlight_insight

Purpose: highlighted insight card for key conclusions and next actions.

```python
deck.add_slide(data.highlight_insight(title="Key Insight", summary="Conversion increased by 24%", bullets=["Version B wins"], next_step="Optimize funnel"))
```

```json
{"type": "data.highlight_insight", "title": "Key Insight", "summary": "Conversion increased by 24%", "bullets": ["Version B wins"], "next_step": "Optimize funnel"}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `summary` | `string` | yes | `""` | Main insight |
| `bullets` | `array<string>` | no | `[]` | Supporting bullets |
| `next_step` | `string` | no | `""` | Next action |

Default style: soft primary card, bullet list, and bottom next-step strip. Keep the summary within two lines.

### data.annotations

Purpose: data annotation list for anomalies, events, and context.

```python
deck.add_slide(data.annotations(title="Data Notes", annotations=["5/13 campaign launched"], note="Outliers removed"))
```

```json
{"type": "data.annotations", "title": "Data Notes", "annotations": ["5/13 campaign launched"], "note": "Outliers removed"}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `annotations` | `array<string>` | yes | `[]` | Annotation list |
| `note` | `string` | no | `""` | Bottom note |

Default style: numbered labels with annotation rows. Prefer 2-5 annotations.

### chart.line

Purpose: line chart for trends, experiment curves, and staged changes.

```python
deck.add_slide(chart.line(title="Trend", categories=["4/29", "5/6"], series=[{"name": "Metric A", "values": [320, 540]}]))
```

```json
{"type": "chart.line", "title": "Trend", "categories": ["4/29", "5/6"], "series": [{"name": "Metric A", "values": [320, 540], "color": "2563EB"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `categories` | `array<string>` | yes | `[]` | X-axis categories |
| `series` | `array<object>` | yes | `[]` | Data series |
| `series[].name` | `string` | yes | none | Series name |
| `series[].values` | `array<number>` | yes | none | Values |
| `series[].color` | `string` | no | automatic | HEX color |
| `subtitle` | `string` | no | built-in text | Subtitle |

Default style: custom-drawn line chart and legend. Keep series lengths aligned with categories.

### chart.bar

Purpose: bar chart for category comparison, ranking, and version differences.

```python
deck.add_slide(chart.bar(title="Channel Conversion", categories=["APP"], series=[{"name": "Conversions", "values": [680]}]))
```

```json
{"type": "chart.bar", "title": "Channel Conversion", "categories": ["APP"], "series": [{"name": "Conversions", "values": [680]}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `categories` | `array<string>` | yes | `[]` | X-axis categories |
| `series` | `array<object>` | yes | `[]` | Data series |
| `series[].name` | `string` | yes | none | Series name |
| `series[].values` | `array<number>` | yes | none | Values |
| `series[].color` | `string` | no | automatic | HEX color |

Default style: custom grouped bars and grid lines. Missing values render as 0.

### chart.pie

Purpose: pie chart for proportions, source distribution, and composition.

```python
deck.add_slide(chart.pie(title="Channel Share", segments=[{"label": "Product A", "value": 42}]))
```

```json
{"type": "chart.pie", "title": "Channel Share", "segments": [{"label": "Product A", "value": 42, "color": "2563EB"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `segments` | `array<object>` | yes | `[]` | Slices |
| `segments[].label` | `string` | yes | none | Label |
| `segments[].value` | `number` | yes | none | Value |
| `segments[].color` | `string` | no | automatic | HEX color |

Default style: editable `python-pptx` chart object with a right-side percentage legend.

### chart.donut

Purpose: donut chart for proportions with a central total or key number.

```python
deck.add_slide(chart.donut(title="Traffic Sources", center_label="Total", center_value="56,780", segments=[{"label": "Search", "value": 38.6}]))
```

```json
{"type": "chart.donut", "title": "Traffic Sources", "center_label": "Total", "center_value": "56,780", "segments": [{"label": "Search", "value": 38.6}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `segments` | `array<object>` | yes | `[]` | Donut slices |
| `segments[].label` | `string` | yes | none | Label |
| `segments[].value` | `number` | yes | none | Value |
| `segments[].color` | `string` | no | automatic | HEX color |
| `center_label` | `string` | no | built-in text | Center label |
| `center_value` | `string` | no | `""` | Center value |

Default style: editable doughnut chart, center text, and right-side percentage list.

### table.comparison

Purpose: comparison table for multiple options and recommendation conclusions.

```python
deck.add_slide(table.comparison(title="Comparison", headers=["Dimension", "Plan A", "Plan B"], rows=[["Cost", "Medium", "Low"]], conclusion="Prefer Plan A."))
```

```json
{"type": "table.comparison", "title": "Comparison", "headers": ["Dimension", "Plan A", "Plan B"], "rows": [["Cost", "Medium", "Low"]], "conclusion": "Prefer Plan A."}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `headers` | `array<string>` | yes | `[]` | Headers |
| `rows` | `array<array<string>>` | yes | `[]` | Rows |
| `conclusion` | `string` | no | built-in recommendation | Bottom conclusion |

Default style: light bordered card, blue header, subtle separators, and recommendation tag behavior for short final-column values.

### narrative.timeline

Purpose: status timeline for project phases, R&D plans, and delivery cadence.

```python
deck.add_slide(narrative.timeline(title="Timeline", items=[{"label": "Research", "date": "2026.05", "description": "Define scope", "status": "done"}]))
```

```json
{"type": "narrative.timeline", "title": "Timeline", "items": [{"label": "Research", "date": "2026.05", "description": "Define scope", "status": "done"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `items` | `array<object>` | yes | `[]` | Timeline nodes |
| `items[].label` | `string` | yes | none | Phase name |
| `items[].date` | `string` | no | `""` | Time label |
| `items[].description` | `string` | no | `""` | Short description |
| `items[].status` | `string` | no | `"normal"` | `done`, `active`, or other |

Default style: `done` is solid blue, `active` is purple highlight, normal nodes are gray. Prefer 4-6 nodes.

### narrative.process_flow

Purpose: process flow for implementation plans, workflows, and generation pipelines.

```python
deck.add_slide(narrative.process_flow(title="Implementation Flow", steps=[{"title": "Requirements", "description": "Define goals", "output": "Checklist"}]))
```

```json
{"type": "narrative.process_flow", "title": "Implementation Flow", "steps": [{"title": "Requirements", "description": "Define goals", "output": "Checklist"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `steps` | `array<object>` | yes | `[]` | Process steps |
| `steps[].title` | `string` | yes | none | Stage name |
| `steps[].description` | `string` | no | `""` | One-line description |
| `steps[].output` | `string` | no | `""` | Deliverable |

Default style: horizontal step cards, light arrows, and bottom pipeline note. Prefer 4-5 steps.

### narrative.roadmap

Purpose: roadmap for quarterly plans and capability-building cadence.

```python
deck.add_slide(narrative.roadmap(title="Roadmap", periods=["Q1", "Q2"], rows=[{"label": "Product", "start": 0, "end": 2}]))
```

```json
{"type": "narrative.roadmap", "title": "Roadmap", "periods": ["Q1", "Q2"], "rows": [{"label": "Product", "start": 0, "end": 2, "color": "2563EB"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `periods` | `array<string>` | yes | `[]` | Period columns |
| `rows` | `array<object>` | yes | `[]` | Roadmap bars |
| `rows[].label` | `string` | yes | none | Row label |
| `rows[].start` | `integer` | yes | none | Start column index |
| `rows[].end` | `integer` | yes | none | End column index |
| `rows[].color` | `string` | no | automatic | HEX color |

Default style: period headers and horizontal bars. Keep indexes within the `periods` range.

### narrative.swot

Purpose: SWOT four-quadrant analysis for strategy, option assessment, and retrospectives.

```python
deck.add_slide(narrative.swot(title="SWOT", quadrants=[{"title": "Strengths", "subtitle": "Core advantages", "items": ["Rich components"]}]))
```

```json
{"type": "narrative.swot", "title": "SWOT", "quadrants": [{"title": "Strengths", "subtitle": "Core advantages", "items": ["Rich components"]}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `quadrants` | `array<object>` | yes | `[]` | Quadrants, preferably four |
| `quadrants[].title` | `string` | yes | none | Quadrant title |
| `quadrants[].subtitle` | `string` | no | `""` | Subtitle |
| `quadrants[].items` | `array<string>` | no | `[]` | Bullet points |

Default style: 2x2 light cards with a center SWOT badge.

### narrative.problem_solution

Purpose: map key problems to executable solutions.

```python
deck.add_slide(narrative.problem_solution(title="Problem Solution", pairs=[{"problem": "Low conversion", "solution": "Optimize funnel"}]))
```

```json
{"type": "narrative.problem_solution", "title": "Problem Solution", "pairs": [{"problem": "Low conversion", "solution": "Optimize funnel"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `pairs` | `array<object>` | yes | `[]` | Problem-solution pairs |
| `pairs[].problem` | `string` | yes | none | Problem |
| `pairs[].solution` | `string` | yes | none | Solution |

Default style: two-column table with connector arrows. Prefer 3-5 rows.

### narrative.logic_pyramid

Purpose: logic pyramid for conclusion, arguments, evidence, and supporting materials.

```python
deck.add_slide(narrative.logic_pyramid(title="Logic Pyramid", levels=[{"label": "Conclusion"}], side_notes=["Core point"]))
```

```json
{"type": "narrative.logic_pyramid", "title": "Logic Pyramid", "levels": [{"label": "Conclusion", "note": ""}], "side_notes": ["Core point"]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `levels` | `array<object>` | yes | `[]` | Pyramid levels; only first four are rendered |
| `levels[].label` | `string` | yes | none | Level text |
| `levels[].note` | `string` | no | `""` | Currently not rendered |
| `side_notes` | `array<string>` | no | `[]` | Right-side notes |

Default style: blue-purple layered rectangles and right-side annotations. Prefer 3-4 levels.

### narrative.risk_table

Purpose: risk table for risk category, impact, and mitigation.

```python
deck.add_slide(narrative.risk_table(title="Risks", risks=[{"category": "Market", "impact": "High", "suggestion": "Differentiate"}]))
```

```json
{"type": "narrative.risk_table", "title": "Risks", "risks": [{"category": "Market", "impact": "High", "suggestion": "Differentiate"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `risks` | `array<object>` | yes | `[]` | Risk list |
| `risks[].category` | `string` | yes | none | Risk category |
| `risks[].impact` | `string` | yes | none | Impact level |
| `risks[].suggestion` | `string` | yes | none | Mitigation suggestion |

Default style: unified table component. Prefer 3-5 rows.

### narrative.milestone

Purpose: milestone timeline. Currently reuses `TimelineSlide`.

```python
deck.add_slide(narrative.milestone(title="Milestones", items=[{"label": "Implementation Done", "date": "2026.03", "status": "active"}]))
```

```json
{"type": "narrative.milestone", "title": "Milestones", "items": [{"label": "Implementation Done", "date": "2026.03", "description": "Core delivery", "status": "active"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `items` | `array<object>` | yes | `[]` | Same shape as `narrative.timeline.items` |

Default style and cautions are the same as `narrative.timeline`.

### narrative.relation_table

Purpose: action-item relation table for owner, priority, progress, and status.

```python
deck.add_slide(narrative.relation_table(title="Actions", rows=[{"action": "Improve feature", "owner": "Alex", "priority": "High", "due": "2026-03-15", "progress": "70%", "status": "In progress"}]))
```

```json
{"type": "narrative.relation_table", "title": "Actions", "rows": [{"action": "Improve feature", "owner": "Alex", "priority": "High", "due": "2026-03-15", "progress": "70%", "status": "In progress"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `rows[].action` | `string` | yes | none | Action item |
| `rows[].owner` | `string` | yes | none | Owner |
| `rows[].priority` | `string` | yes | none | Priority |
| `rows[].due` | `string` | yes | none | Due date |
| `rows[].progress` | `string` | yes | none | Current progress |
| `rows[].status` | `string` | yes | none | Status |

Default style: wide table. Keep text short because there are many columns.

### narrative.story_structure

Purpose: narrative structure recommendation with background, problem, method, result, and conclusion.

```python
deck.add_slide(narrative.story_structure(title="Story Structure", steps=[{"title": "Background", "description": "State the goal", "icon": "B"}]))
```

```json
{"type": "narrative.story_structure", "title": "Story Structure", "steps": [{"title": "Background", "description": "State the goal", "icon": "B"}]}
```

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `steps` | `array<object>` | yes | `[]` | Narrative steps |
| `steps[].title` | `string` | yes | none | Step title |
| `steps[].description` | `string` | yes | none | Step description |
| `steps[].icon` | `string` | no | `""` | Text icon placeholder |

Default style: right-side vertical card chain. Prefer 4-5 steps.

### Media And Basic Components

`media.icon` supports frontend-style names such as `lucide.sparkles`, `heroicons.bolt`, `remix.rocket-line`, `tabler.file-code`, `ph.hexagon-bold`, and `mdi.message-text-outline`. `ppt_ui/icons/provider.py` normalizes dot syntax to Iconify-compatible IDs, resolves remote SVG through the default `IconifyApiProvider`, and the renderer converts SVG to transparent PNG with `resvg-py` before embedding it in the PPTX.

| Type | Status | Description |
| --- | --- | --- |
| `media.image` | Implemented | Local image insertion with contain/stretch behavior |
| `media.icon` | Implemented | Remote Iconify-compatible icons plus optional local `src` transparent PNG fallback |

Example:

```json
{
  "type": "media.icon",
  "props": {
    "name": "lucide.sparkles",
    "color": "primary",
    "size": 128,
    "stroke_width": 1.8,
    "rotate": 0,
    "flip": "horizontal"
  }
}
```

The default alias map also covers common frontend icon packages such as Font Awesome (`fa.user`, `fa-brands.github`), Bootstrap Icons (`bootstrap.alarm`), Material Symbols (`material.auto-awesome`), Carbon (`carbon.add`), Fluent (`fluent.home-24-regular`), Radix (`radix.check`), Octicons (`octicon.mark-github`), Simple Icons (`simple-icons.openai`), Solar (`solar.star-bold`), MingCute (`mingcute.sparkles-line`), and Hugeicons (`hugeicons.ai-brain-01`).

Custom providers can be registered per deck:

```python
from pathlib import Path
from ppt_ui import Deck, LocalSvgIconProvider, media, layout, page

deck = Deck()
deck.icons.register_alias("company", "brand")
deck.icons.register(LocalSvgIconProvider(Path("assets/icons"), prefix="brand"))
deck.add_page(
    page.standard(
        title="Brand Icons",
        blocks=[media.icon(name="company.logo", layout=layout.grid_item(col=1, span=3, row=1))],
    )
)
```

## Theme System

Current theme entrypoints:

```python
from ppt_ui import get_theme

theme = get_theme("default_blue")
single_file_theme = get_theme("examples/themes/company_blue.json")
directory_theme = get_theme("examples/themes/company_modular")
```

`get_theme()` supports built-in theme names, external single-file JSON themes, external theme directories with `theme.json`, inline theme dictionaries, and direct `Theme` objects. Relative paths passed through `deck_from_json()` are resolved relative to the deck JSON file.

Built-in themes are stored as JSON files under `ppt_ui/themes/`. Python code only registers their names and loads the files through `ThemeLoader`.

### Theme Sources

| Source | Example | Status |
| --- | --- | --- |
| Built-in theme | `"default_blue"` | Implemented |
| Built-in alias | `"default"` | Implemented |
| External single-file JSON | `"./themes/company_blue.json"` | Implemented |
| External directory theme | `"./themes/company_modular"` | Implemented |
| Inline dict | `{ "name": "custom", "extends": "default_blue" }` | Implemented |

### Built-In Themes

| Theme | Primary | Accent | Background | Best for |
| --- | --- | --- | --- | --- |
| `theme.tech_blue` | `#2563EB` | `#7C3AED` | `#FFFFFF` | AI products, technical reports, component-library demos |
| `theme.academic_clean` | `#1E3A8A` | `#2563EB` | `#FFFFFF` | Thesis defenses, papers, experiment analysis |
| `theme.business_navy` | `#0F2A5F` | `#D4AF37` | `#F8FAFC` | Business plans, executive reports, strategy decks |
| `theme.data_dashboard` | `#2563EB` | `#06B6D4` | `#F8FAFC` | Metrics reports, operating weekly reports, dashboards |
| `theme.medical_teal` | `#0F766E` | `#14B8A6` | `#F8FEFF` | Medical AI, OCT, biology, scientific research decks |
| `theme.dark_tech` | `#38BDF8` | `#A855F7` | `#020617` | Launch decks and high-contrast technical demos |
| `theme.claude_warm` | `#8B5E34` | `#D97706` | `#F7F3EA` | Warm narrative reports and thoughtful product docs |

`default`, `default_blue`, `tech_blue`, and `theme.tech_blue` all resolve to the Tech Blue built-in theme.

Directory themes use `theme.json` as the entry file and can reference token/component fragments:

```json
{
  "name": "company_modular",
  "extends": "default_blue",
  "tokens": "./tokens.json",
  "components": [
    "./components/data.json",
    "./components/chart.json"
  ]
}
```

### Theme Fields

| Field | Type | Default/description |
| --- | --- | --- |
| `name` | `string` | `tech_blue` |
| `slide_width` | `float` | `13.333` inch |
| `slide_height` | `float` | `7.5` inch |
| `colors` | `ColorTokens` | Color tokens |
| `fonts` | `FontTokens` | Typography tokens |
| `spacing` | `SpacingTokens` | Spacing tokens |
| `radius_tokens` | `RadiusTokens` | Radius tokens |
| `shadow` | `ShadowTokens` | Shadow offset tokens |
| `component_styles` | `dict[str, ComponentStyle]` | Component styles |
| `component_defaults` | `dict[str, dict]` | Per-component and per-variant default style values |
| `chart_palette` | `list[str]` | Chart color palette consumed by chart-like components |
| `card_shadow` | `bool` | Enables card shadow |

### ColorTokens

| Token | Default | Description |
| --- | --- | --- |
| `background` | `FFFFFF` | Slide background |
| `surface` | `F8FAFC` | Light card surface |
| `surface_white` | `FFFFFF` | White card |
| `primary` | `2563EB` | Primary blue |
| `primary_dark` | `1E3A8A` | Dark blue |
| `primary_soft` | `EFF6FF` | Soft blue |
| `primary_tint` | `DBEAFE` | Blue tint |
| `accent` | `7C3AED` | Purple accent |
| `accent_soft` | `F5F3FF` | Soft purple |
| `accent_tint` | `EDE9FE` | Purple tint |
| `success` | `10B981` | Success |
| `success_soft` | `ECFDF5` | Soft success |
| `warning` | `F59E0B` | Warning |
| `warning_soft` | `FFF7ED` | Soft warning |
| `danger` | `EF4444` | Danger |
| `text_primary` | `0F172A` | Primary text |
| `text_secondary` | `64748B` | Secondary text |
| `text_tertiary` | `94A3B8` | Tertiary text |
| `border` | `E2E8F0` | Border |
| `border_light` | `EEF2F7` | Light border |
| `gray_50` | `F8FAFC` | Neutral |
| `gray_100` | `F1F5F9` | Neutral |
| `gray_200` | `E2E8F0` | Neutral |
| `gray_700` | `334155` | Neutral |
| `shadow_light` | `EEF2FF` | Light shadow |
| `shadow_card` | `E5EAF6` | Card shadow |

### FontTokens

| Token | Default | Description |
| --- | --- | --- |
| `family` | `Microsoft YaHei` | Font family |
| `title_size` | `36` | Cover title |
| `subtitle_size` | `15` | Subtitle |
| `h1_size` | `28` | Slide title |
| `h2_size` | `18` | Module title |
| `body_size` | `11` | Body |
| `caption_size` | `10` | Caption |
| `tiny_size` | `8` | Tiny text |
| `display_size` | `54` | Large numbers |

### Spacing / Radius / Shadow

| Token | Default | Description |
| --- | --- | --- |
| `spacing.base` | `8` | Design base |
| `spacing.page_margin` | `0.55` | Horizontal page margin in inch |
| `spacing.page_y` | `0.45` | Vertical page margin in inch |
| `spacing.title_top` | `0.48` | Title top |
| `spacing.content_top` | `1.55` | Content top |
| `spacing.footer_y` | `7.04` | Footer y |
| `spacing.gutter` | `0.20` | Card gutter |
| `spacing.card_padding` | `0.22` | Card padding |
| `radius_tokens.sm/md/lg` | `0.035/0.055/0.075` | Rounded rectangle adjustment |
| `shadow.card_offset_x/y` | `0.012/0.018` | Card shadow offset |

### Component Styles

Current component style keys:

| Key | Use |
| --- | --- |
| `card.default` | Generic card |
| `metric_card.default` | Metric card |
| `table.comparison` | Comparison table |
| `timeline.status_cards` | Timeline status cards |
| `process_flow.compact_cards` | Process cards |
| `conclusion.hero` | Conclusion hero container |

You can construct a `Theme` in Python and pass it to `Deck(theme=custom_theme)`, or load it from JSON through `ThemeLoader` / `get_theme()`.

## Layout System

SlideForge currently uses inch-based layout with `Box` and `PageBox`. The theme provides slide size and margins. `PageBox.from_theme(theme)` creates the usable page region.

Recommended practice:

- Use `add_slide_title()` first to get the unified content region.
- Use `Box.inset()` for padding.
- Use `split_cols()` and `split_rows()` for grid-like layouts instead of scattering absolute coordinates.
- Complex components may use local coordinates, but should still be derived from `content_box()` and theme spacing.

A full flex/grid layout engine is not implemented yet. Row, Column, Spacer, Padding, and Alignment are planned.

## Renderer

Components do not directly call `python-pptx` because the renderer centralizes style, unit handling, fonts, colors, cards, and tables. It also keeps agents away from low-level shape operations.

Current `PptxRenderer` helpers:

| Helper | Function | Used by |
| --- | --- | --- |
| `background(slide)` | Sets slide background | All pages |
| `rect(slide, box, fill, line=None, rounded=False)` | Draws rectangles and rounded rectangles | Cards, tables, labels |
| `line(slide, x1, y1, x2, y2, color=None, width=1.0)` | Draws connectors | Timelines, charts, flows |
| `circle(slide, box, fill, line=None)` | Draws circles | Icons, nodes |
| `text(slide, box, text, size=None, color=None, bold=False, align="left", valign="top")` | Draws textboxes | All text |
| `bullet_list(slide, box, items, size=None, ...)` | Draws bullet lists | Two-column, SWOT, insights |
| `card(slide, box, fill=None, line=None)` | Alias for `add_card()` | Internal compatibility |
| `pill(slide, box, text, fill=None, color=None)` | Draws pill labels | Cover metadata |
| `accent_bar(slide, x=..., y=..., h=...)` | Alias for `add_accent_bar()` | Title decoration |
| `content_box()` | Returns unified content region | Page layout |
| `add_accent_bar()` | Adds the blue-purple accent bar | Most slides |
| `add_slide_title(title, subtitle="", section=None)` | Adds unified title area and returns content region | Most slides |
| `add_footer(text=...)` | Adds subtle footer | Most slides |
| `add_card(box, fill=None, line=None, shadow=True)` | Adds unified card | Data, layout, narrative components |
| `add_metric_card(...)` | Renders a metric card | `MetricCard` |
| `add_section_label(label, box)` | Renders a small section label | Contents, flow, tables |
| `add_status_timeline_node(...)` | Renders timeline nodes | `TimelineSlide` |
| `add_process_step_card(...)` | Renders process step cards | `ProcessFlowSlide` |
| `add_table(headers, rows)` | Renders a unified table | Comparison, risk, relation tables |

Renderer helpers are internal APIs. They are expected to grow while preserving compatibility where possible.

## Export Screenshots

SlideForge can export each slide in a PPTX as a PNG:

```python
from ppt_ui.export import export_pptx_screenshots

export_pptx_screenshots("examples/demo.pptx", "examples/demo_screenshots")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `pptx_path` | `str | Path` | required | PPTX path |
| `output_dir` | `str | Path` | required | Output directory |
| `width` | `int` | `1920` | Export width |
| `height` | `int` | `1080` | Export height |

Behavior:

- The output directory is overwritten on each export.
- Files are normalized to `slide_01.png`, `slide_02.png`, and so on.
- Export uses Windows PowerPoint COM automation.
- Missing PowerPoint or `pywin32` raises `ScreenshotExportError`.

## Full Examples

### Complete JSON Example

```json
{
  "title": "SlideForge Demo",
  "theme": "default_blue",
  "slides": [
    {
      "type": "slide.title",
      "title": "Reusable PPT UI Component Library",
      "subtitle": "Agent-driven PPT UI Framework",
      "presenter": "SlideForge",
      "date": "2026.05.03"
    },
    {
      "type": "slide.section",
      "number": "01",
      "title": "Layout Components",
      "subtitle": "Build standard reporting pages quickly",
      "keywords": ["Title", "Two Column", "Metric Card", "Table", "Timeline"]
    },
    {
      "type": "layout.two_column",
      "title": "Why Components",
      "left_title": "Agent Friendly",
      "left_items": ["Describe page semantics", "Avoid direct shape operations", "Keep PPTX editable"],
      "right_title": "Engineering Reuse",
      "right_items": ["Unified theme tokens", "Unified layout rules", "Extensible registry"]
    },
    {
      "type": "data.metric_cards",
      "title": "Metric Overview",
      "cards": [
        {"label": "Accuracy", "value": "92.3%", "delta": "+3.1%", "note": "vs. previous", "icon": "AC"},
        {"label": "AUC", "value": "0.948", "delta": "+0.026", "note": "validation", "icon": "AU"}
      ]
    },
    {
      "type": "table.comparison",
      "title": "Plan Comparison",
      "headers": ["Dimension", "Plan A", "Plan B"],
      "rows": [["Cost", "Medium", "Low"], ["Timeline", "Short", "Medium"], ["Recommended", "A", "B"]],
      "conclusion": "Considering completeness, timeline, and cost, prefer Plan A."
    },
    {
      "type": "narrative.timeline",
      "title": "Project Timeline",
      "items": [
        {"label": "Requirements", "date": "2026.05", "description": "Define goals", "status": "done"},
        {"label": "Development", "date": "2026.07", "description": "Build core components", "status": "active"}
      ]
    },
    {
      "type": "narrative.process_flow",
      "title": "Implementation Flow",
      "steps": [
        {"title": "Requirements", "description": "Define goals and scope", "output": "Checklist"},
        {"title": "Design", "description": "Create structured page plan", "output": "DSL Schema"},
        {"title": "Build", "description": "Render components with unified style", "output": "Component library"}
      ]
    },
    {
      "type": "slide.conclusion",
      "points": [
        {"title": "Reuse", "description": "Reduce repeated layout work"},
        {"title": "Theme Consistency", "description": "Use tokens for colors, fonts, and spacing"},
        {"title": "Agent Friendly", "description": "Driven by JSON DSL"}
      ]
    },
    {
      "type": "slide.qa",
      "project": "SlideForge",
      "description": "Discuss component design, theme extension, and agent generation pipelines."
    }
  ]
}
```

### Complete Python Example

```python
from ppt_ui import Deck, data, layout, narrative, slide, table

deck = Deck(title="SlideForge Demo")
deck.add_slide(slide.title(title="Reusable PPT UI Component Library", subtitle="Agent-driven PPT UI Framework"))
deck.add_slide(slide.section(number="01", title="Layout Components", keywords=["Two Column", "Metric Card", "Timeline"]))
deck.add_slide(
    layout.two_column(
        title="Why Components",
        left_title="Agent Friendly",
        left_items=["Describe page semantics", "Avoid low-level shapes"],
        right_title="Engineering Reuse",
        right_items=["Unified theme", "Unified layout"],
    )
)
deck.add_slide(
    data.metric_cards(
        title="Metric Overview",
        cards=[data.metric_card(label="Accuracy", value="92.3%", delta="+3.1%", icon="AC")],
    )
)
deck.add_slide(
    table.comparison(
        title="Comparison",
        headers=["Dimension", "Plan A", "Plan B"],
        rows=[["Cost", "Medium", "Low"]],
        conclusion="Prefer Plan A.",
    )
)
deck.add_slide(
    narrative.timeline(
        title="Project Timeline",
        items=[{"label": "Development", "date": "2026.07", "description": "Build core components", "status": "active"}],
    )
)
deck.add_slide(slide.qa())
deck.render("examples/python_api_demo.pptx")
```

## Agent Usage Guide

Agents should generate JSON DSL, not `python-pptx` code.

Recommended workflow:

1. Analyze the user request and identify whether it is a report, proposal, data deck, or retrospective.
2. Split the deck into pages such as cover, contents, sections, data slides, analysis slides, and conclusion.
3. Choose a namespace type for each slide.
4. Fill required fields and keep content concise.
5. Pass JSON to `deck_from_dict()` or `deck_from_json()` for rendering.

Agent constraints:

- `type` must exist in the registry.
- Do not output `add_textbox`, `add_shape`, or absolute-coordinate code.
- Chart `series[].values` should align with `categories`.
- Table row lengths should align with `headers`.
- Titles, bullets, and table cells should stay short to avoid overflow.
- Fields such as `style`, `layout`, and `hidden` are not active in the current version.

Common errors:

| Error | Result | Fix |
| --- | --- | --- |
| Unknown `type` | `ValueError: Unsupported slide type` | Use an implemented namespace type |
| Missing required fields | Dataclass construction error | Check the component parameter table |
| Chart length mismatch | Missing values or visual misalignment | Align `categories` and `values` |
| Table row/header mismatch | Unstable columns | Match row length to headers |
| Overlong content | Auto-fit text or overflow | Shorten text or split pages |

## Component Extension Guide

To add `chart.scatter`:

1. Add `ScatterChartSlide` and any dataclasses such as `ScatterPoint` in `ppt_ui/components/data.py`.
2. Implement `render(ctx, box)` using `ctx.renderer.add_slide_title()`, `add_card()`, and `Box` layout helpers.
3. Add `scatter(...)` to `ChartNamespace` in `ppt_ui/api.py`.
4. Add a `_scatter_chart_slide()` factory in `ppt_ui/schema/parser.py`.
5. Register it in `build_default_registry()` with `registry.register_slide("chart.scatter", _scatter_chart_slide)`.
6. Add an example to `examples/sample_deck.json`.
7. Add parser and namespace API tests in `tests/test_parser.py`.
8. Document parameters, JSON examples, defaults, and cautions in this Component API section.

For a large component library, keep the family + variant model: `chart.line`, `chart.bar`, and `chart.scatter` can share chart-family theme tokens while using independent renderers.

## FAQ

### Is the generated PPT editable?

Yes. SlideForge uses `python-pptx` to create PowerPoint shapes, textboxes, and charts. The output is an editable `.pptx`.

### Why not let agents write `python-pptx` directly?

Low-level code often causes coordinate drift, inconsistent styling, and repeated layout logic. SlideForge lets agents output semantic JSON while the component library renders consistent pages.

### What happens if a JSON `type` is wrong?

The parser raises `ValueError: Unsupported slide type`. Use an implemented namespace type from this document.

### What if Chinese fonts render incorrectly?

The default font is `Microsoft YaHei`. On systems without that font, create a custom `Theme.fonts.family` in Python or replace fonts in PowerPoint.

### What if chart data is too long?

Reduce categories, split the chart across pages, or use tables/annotations. Automatic sampling and label collision handling are not implemented yet.

### How do I customize the theme?

Construct a `Theme` in Python and pass it to `Deck(theme=theme)`, or load an external single-file JSON / directory theme through `get_theme()` or `ThemeLoader`, for example `get_theme("examples/themes/company_blue.json")` or `get_theme("examples/themes/company_modular")`.

### How do I add a component?

Add a dataclass component, implement `render()`, register it in `ComponentRegistry`, add namespace API, examples, tests, and documentation.

### How do I disable screenshot export?

Run:

```bash
uv run python examples/demo_deck.py --no-screenshots
```

### Does it work on Windows and macOS?

PPTX generation is cross-platform. Screenshot export currently depends on Windows PowerPoint COM. macOS/Linux screenshot export is planned.

### What does PowerPoint COM screenshot export require?

It requires Windows, Microsoft PowerPoint, local COM automation, and `pywin32`.

## Roadmap

- More chart components: scatter, area, combo, waterfall.
- More themes: business gray-blue, academic minimal, dark tech, brand themes.
- Fuller layout engine: Row, Column, Spacer, Padding, Alignment, 12-column grid.
- Automatic text fitting, overflow detection, and page-splitting suggestions.
- SVG/icon rendering with Iconify, Lucide, Heroicons, and other frontend icon libraries.
- `media.image` component and image crop strategies.
- Stronger JSON schema validation and error messages.
- Agent prompt templates and page planners.
- Web preview or screenshot-based visual regression.
- JSON-defined screenshot export, page size, metadata, author, and version.
