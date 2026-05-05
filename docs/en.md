# SlideForge User Documentation

SlideForge is a Python PPT UI component library for agent-generated presentations. It accepts structured JSON DSL or a Python namespace API, resolves themes and layouts, and renders editable `.pptx` files through `python-pptx`. Agents do not need to call low-level APIs such as `add_textbox` or `add_shape`; they choose page types, component types, props, layouts, and themes.

The current implementation uses a `Deck -> Page -> Block -> Component` model. A `Page` can contain many independent `Block` instances. Page titles, footers, page numbers, masters, and shared chrome belong to Page/Master. Components only render their own content inside the `Box` assigned by the layout system.

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
- [Masters And Chrome](#masters-and-chrome)
- [Renderer](#renderer)
- [Export Screenshots](#export-screenshots)
- [Icons](#icons)
- [Full Examples](#full-examples)
- [Agent Usage Guide](#agent-usage-guide)
- [Component Extension Guide](#component-extension-guide)
- [FAQ](#faq)
- [Roadmap](#roadmap)

## Introduction

SlideForge solves the problem of making agents generate professional, consistent, editable PowerPoint decks. Asking an agent to write raw `python-pptx` shape code creates repeated coordinates, inconsistent style decisions, poor reuse, and difficult theme changes. SlideForge moves that work into a reusable component system.

Typical use cases include thesis defenses, project proposals, data reports, business presentations, automated weekly reports, experiment summaries, product methodology decks, and technical solution decks.

## Architecture

```text
JSON DSL / Python API
  -> Component Registry / Parser
  -> Deck / Page / Block Tree
  -> Theme / Master / Layout resolution
  -> PptxRenderer
  -> editable .pptx
```

| Layer | Responsibility |
| --- | --- |
| JSON DSL / Python API | Structured user or agent input: pages, blocks, props, layout, and style. |
| Component Registry / Parser | Validates page/component types and converts JSON into `Deck`, `Page`, and `Block` objects. |
| Deck / Page / Block Tree | Internal document model. Deck owns the whole presentation, Page owns one slide, Block is one component instance. |
| Theme / Master / Layout | Theme supplies visual defaults, Master supplies common PPT chrome, Layout maps blocks to concrete `Box` regions. |
| PptxRenderer | Centralized `python-pptx` rendering helpers for text, cards, charts, icons, and images. |
| editable .pptx | Final PowerPoint file that can be edited manually. |

## Installation

| Item | Requirement |
| --- | --- |
| Python | 3.10+, currently tested on 3.11 |
| Package manager | `uv` is recommended |
| PPTX rendering | `python-pptx` |
| Screenshot export | Windows PowerPoint COM plus `pywin32` |
| Remote icons | Iconify API requires network access; local SVG providers work offline |

Common commands:

```bash
uv sync
uv run pytest
uv run python examples/demo_deck.py
```

## Quick Start

Generate the demo deck:

```bash
uv run python examples/demo_deck.py
```

Default outputs:

```text
examples/demo.pptx
examples/demo_screenshots/
examples/demo_showcase.png
examples/theme_demos/<theme>/demo.pptx
examples/theme_demos/<theme>/screenshots/
examples/theme_demos/<theme>/showcase.png
```

CLI options:

| Option | Description |
| --- | --- |
| `--output examples/demo.pptx` | Main demo output path. |
| `--screenshots-dir examples/demo_screenshots` | Main demo screenshot directory. It is overwritten on each run. |
| `--showcase examples/demo_showcase.png` | Combined showcase image path. |
| `--theme-demos-dir examples/theme_demos` | Output directory for per-theme demo assets. |
| `--skip-theme-demos` | Generate only the main demo. |
| `--no-screenshots` | Generate PPTX only. |

Load a JSON deck manually:

```python
from ppt_ui import deck_from_json

deck = deck_from_json("examples/sample_deck.json")
deck.render("examples/demo.pptx")
```

## Directory Structure

| Path | Purpose |
| --- | --- |
| `ppt_ui/core/presentation.py` | `Deck`, which owns theme, pages, masters, component registry, and icon registry. |
| `ppt_ui/core/page.py` | `Page` and `Block`, the current DSL core model. |
| `ppt_ui/core/component.py` | `RenderContext` and the component protocol. |
| `ppt_ui/core/theme.py` | Theme dataclasses, `ThemeLoader`, `ThemeRegistry`, and built-in theme registration. |
| `ppt_ui/core/layout.py` | `Box`, `PageLayout`, built-in layouts, and block box resolution. |
| `ppt_ui/core/master.py` | `SlideMaster`, `MasterRegistry`, and default masters. |
| `ppt_ui/core/registry.py` | `ComponentRegistry`, mapping type names to factories. |
| `ppt_ui/components/blocks.py` | Current block component implementations. |
| `ppt_ui/components/registry.py` | Default component registration. |
| `ppt_ui/renderer/pptx_renderer.py` | Unified renderer built on `python-pptx`. |
| `ppt_ui/schema/parser.py` | JSON parsing, validation, and `Deck` construction. |
| `ppt_ui/export/screenshots.py` | PowerPoint COM screenshot export. |
| `ppt_ui/export/contact_sheet.py` | Combined screenshot showcase generation. |
| `ppt_ui/icons/provider.py` | Iconify, local SVG, and URL-template icon providers. |
| `ppt_ui/themes/*.json` | Built-in theme JSON files. |
| `examples/demo_deck.py` | Demo generation entry point. |
| `examples/sample_deck.json` | Current JSON DSL example. |
| `tests/` | Parser, theme, and icon tests. |

## Core Concepts

### Deck

`Deck` manages the whole presentation.

| Attribute/Method | Description |
| --- | --- |
| `pages` | List of `Page` objects. |
| `theme` | Parsed `Theme` object. |
| `default_master` | Default master name, currently `tech_blue`. |
| `masters` | `MasterRegistry`. |
| `components` | `ComponentRegistry`. |
| `icons` | `IconRegistry`. |
| `add_page(page)` | Adds a page. |
| `render(path)` | Writes a PPTX file. |

### Page

`Page` represents one PPT slide. It owns page-level semantics and common chrome, not component internals.

| Field | Description |
| --- | --- |
| `type` | Supported values: `page.cover`, `page.standard`, `page.section`, `page.blank`, `page.closing`, `page.qa`. |
| `layout` | Layout name or inline layout spec. |
| `master` | Master name for this page. |
| `use_master` | Whether to use a master. |
| `chrome` | Page chrome configuration for title, footer, page number, logo, accent bar, and section label. |
| `title` / `subtitle` | Page title content. |
| `blocks` | Component instances on the page. |
| `hidden` | Hidden pages are not rendered. |

### Block

`Block` is one component instance placed on a page.

| Field | Description |
| --- | --- |
| `id` | Optional stable identifier. |
| `type` | Component type, such as `chart.line`. |
| `variant` | Component variant, defaulting to `default`. |
| `props` | Component content data. |
| `layout` | Position inside the page content region. |
| `style` | Local style override. |
| `visible` | Whether to render the block. |
| `metadata` | Extension metadata. |

### Component

Components render only inside their assigned `Box`. They should not render page titles, global footers, page numbers, logos, or global backgrounds. Current default components live in `ppt_ui/components/blocks.py` and are registered through `build_default_component_registry()`.

### RenderContext

`RenderContext` contains:

| Field | Description |
| --- | --- |
| `slide` | The current `python-pptx` slide object. |
| `theme` | Current theme. |
| `renderer` | `PptxRenderer` helper object. |
| `style` | Merged theme defaults and block-level style overrides. |

### Box

`Box` uses inch units and contains `x`, `y`, `w`, and `h`. Helpers include `inset()`, `split_cols()`, `split_rows()`, `top()`, `bottom()`, and `remaining_below()`.

### ComponentRegistry

`ComponentRegistry` prevents the parser from becoming a large if/else block. Unknown component types produce diagnostics and raise errors in strict mode.

## JSON DSL Guide

### Top-Level Fields

```json
{
  "schema_version": "0.2",
  "title": "SlideForge Component Library Demo",
  "theme": "theme.tech_blue",
  "default_master": "tech_blue",
  "metadata": {},
  "masters": {},
  "pages": []
}
```

| Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `schema_version` | `string` | No | `0.2` | Non-`0.2` versions produce a warning. |
| `title` | `string` | No | `SlideForge Deck` | Deck title. |
| `theme` | `string/object` | No | `default_blue` | Built-in theme name, external theme path, theme directory, or inline theme dict. |
| `default_master` | `string` | No | `tech_blue` | Default master name. |
| `metadata` | `object` | No | `{}` | Deck metadata. |
| `masters` | `object` | No | Built-ins `default`, `tech_blue`, `blank` | Custom master configuration. |
| `pages` | `array` | Yes | None | Page list. |

The parser currently does not consume top-level `export`, `screenshot`, `page_size`, `language`, `author`, `date`, or `version`. Put those values in `metadata` or handle them in an external workflow.

### Page Fields

```json
{
  "type": "page.standard",
  "layout": "standard",
  "title": "Metrics And Trend",
  "subtitle": "Multiple independent components rendered on one page",
  "master": "tech_blue",
  "use_master": true,
  "chrome": {},
  "blocks": []
}
```

| Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `type` | `string` | No | `page.standard` | Page type. |
| `layout` | `string/object` | No | Derived from page type | Built-in layout or inline layout spec. |
| `master` | `string` | No | `default_master` | Page master. |
| `use_master` | `boolean` | No | `true` | Whether this page uses a master. |
| `master_overrides` | `object` | No | `{}` | Page-level master overrides. |
| `chrome` | `object` | No | `{}` | Page chrome controls. |
| `title` | `string` | No | `""` | Page title. |
| `subtitle` | `string` | No | `""` | Page subtitle. |
| `blocks` | `array` | No | `[]` | Component blocks. |
| `notes` | `string` | No | `""` | Stored in the model; not written as speaker notes yet. |
| `hidden` | `boolean` | No | `false` | Hidden pages are skipped during rendering. |
| `metadata` | `object` | No | `{}` | Page metadata. |

### Block Fields

```json
{
  "id": "trend",
  "type": "chart.line",
  "variant": "default",
  "layout": {"mode": "grid", "col": 5, "span": 8, "row": 1, "row_span": 2},
  "style": {"line_width": 1.6},
  "props": {
    "categories": ["4/29", "5/6", "5/13"],
    "series": [{"name": "Score", "values": [23, 36, 48]}]
  }
}
```

| Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `string` | No | `None` | Stable identifier. |
| `type` | `string` | Yes | None | Component type. |
| `variant` | `string` | No | `default` | Theme default variant. |
| `props` | `object` | No | `{}` | Component data. |
| `layout` | `object` | No | Absolute content box | Block layout. |
| `style` | `object` | No | `{}` | Local visual overrides. |
| `visible` | `boolean` | No | `true` | Whether to render this block. |
| `metadata` | `object` | No | `{}` | Extension metadata. |

## Python API Guide

```python
from ppt_ui import Deck, chart, data, layout, page, table, theme

deck = Deck(title="API Demo", theme=theme.tech_blue())
deck.add_page(
    page.standard(
        title="Metrics And Trend",
        subtitle="Multiple blocks on one page",
        blocks=[
            data.metric_cards(
                cards=[
                    data.metric_card(label="Accuracy", value="92.3%", delta="+3.1%", compare="vs previous", icon="AC"),
                    data.metric_card(label="AUC", value="0.948", delta="+0.026", compare="validation", icon="AU")
                ],
                layout=layout.grid_item(col=1, span=4, row=1, row_span=2),
            ),
            chart.line(
                categories=["4/29", "5/6", "5/13"],
                series=[{"name": "Coverage", "values": [23, 36, 48]}],
                layout=layout.grid_item(col=5, span=8, row=1, row_span=2),
            ),
            table.comparison(
                headers=["Dimension", "A", "B"],
                rows=[["Cost", "Low", "Medium"], ["Cycle", "4w", "6w"]],
                conclusion="Recommend A for the MVP.",
                layout=layout.grid_item(col=1, span=12, row=3, row_span=2),
            ),
        ],
    )
)
deck.render("examples/api_demo.pptx")
```

Current namespaces:

| Namespace | Methods |
| --- | --- |
| `page` / `slide` | `cover()`, `standard()`, `section()`, `blank()`, `closing()`, `qa()`. `slide` is an alias of `page`. |
| `layout` | `grid()`, `absolute()`, `grid_item()`, `box()`. |
| `block` | `component()` for custom component types. |
| `basic` | `text()`. |
| `data` | `metric_card()` helper, `metric_cards()`, `progress()`. |
| `chart` | `line()`, `bar()`, `pie()`, `donut()`. |
| `table` | `comparison()`. |
| `narrative` | `timeline()`, `process_flow()`, `roadmap()`. |
| `media` | `icon()`, `image()`. |
| `master` | `tech_blue()`, `blank()`. |
| `theme` | `tech_blue()`, `glassmorphism()`, `claude()`, `glitch_art()`, `paper_cut()`, `neon_cyberpunk()`, `apple()`, `google()`. |

## Component API

### Implemented Types

| Type | Python API | Description |
| --- | --- | --- |
| `basic.text` | `basic.text(...)` | Text or bullet list. |
| `data.metric_cards` | `data.metric_cards(...)` | Metric cards. |
| `data.progress` | `data.progress(...)` | Progress bar list. |
| `chart.line` | `chart.line(...)` | Editable shape-based line chart. |
| `chart.bar` | `chart.bar(...)` | Editable shape-based bar chart. |
| `chart.pie` | `chart.pie(...)` | Native PowerPoint pie chart. |
| `chart.donut` | `chart.donut(...)` | Native PowerPoint doughnut chart. |
| `table.comparison` | `table.comparison(...)` | Comparison table. |
| `table.basic` | `block.component("table.basic", ...)` | Currently reuses the comparison table implementation. |
| `narrative.timeline` | `narrative.timeline(...)` | Status timeline. |
| `narrative.process_flow` | `narrative.process_flow(...)` | Process step cards. |
| `narrative.roadmap` | `narrative.roadmap(...)` | Roadmap bar list. |
| `media.icon` | `media.icon(...)` | Iconify, URL, local SVG, or fallback icon card. |
| `media.image` | `media.image(...)` | Image block. |

`data.metric_card` is a Python helper that returns one item for `data.metric_cards.cards[]`; it is not a standalone JSON component type.

### Common Component Props

| Type | Props |
| --- | --- |
| `basic.text` | `text`, `bullets`, `size`, `color`, `bold`, `align`, `valign`. |
| `data.metric_cards` | `cards[]`; each item supports `label`, `value`, `delta`, `compare`/`note`, `icon`. |
| `data.progress` | `items[]`; each item supports `label`, `value`. |
| `chart.line` / `chart.bar` | `categories[]`, `series[]`; each series supports `name`, `values[]`, optional `color`. |
| `chart.pie` / `chart.donut` | `labels[]` or `categories[]`, `values[]` or `data[]`. |
| `table.comparison` / `table.basic` | `headers[]`, `rows[][]`, `conclusion`. |
| `narrative.timeline` | `items[]`; common fields are `title`, `date`, `description`, `status`. |
| `narrative.process_flow` | `steps[]` or `items[]`; common fields are `title`, `description`, `output`. |
| `narrative.roadmap` | `items[]`; common fields are `label`, `value`, `status`. |
| `media.icon` | `name`, `label`, `source`, `description`, `src`, `color`, `size`, `width`, `height`, `rotate`, `flip`, `stroke_width`/`strokeWidth`, `opacity`. |
| `media.image` | `src`, `fit`; `fit` supports `contain` or `cover`. |

## Theme System

Built-in themes are JSON files under `ppt_ui/themes/`. Python code only registers stable names and loads those files through `ThemeLoader`.

Current built-in themes:

| Theme | Primary | Accent | Background | Font | Style |
| --- | --- | --- | --- | --- | --- |
| `theme.tech_blue` | `#2563EB` | `#7C3AED` | `#FFFFFF` | `Microsoft YaHei` | Default blue-purple technical style. |
| `theme.glassmorphism` | `#6366F1` | `#A855F7` | `#E8EEFF` | `Segoe UI` | Glassmorphism, gradient background, translucent cards. |
| `theme.claude` | `#B8651B` | `#B8651B` | `#F2ECE2` | `Noto Serif SC` | Warm paper, serif typography, restrained lines. |
| `theme.glitch_art` | `#00FFFF` | `#FF00FF` | `#0A0A0A` | `Consolas` | Dark scanlines, neon contrast, experimental look. |
| `theme.paper_cut` | `#2C3E50` | `#E74C3C` | `#F0F0F0` | `Georgia` | Paper-cut layers, strong shadows, illustrative feel. |
| `theme.neon_cyberpunk` | `#00FF41` | `#00D4FF` | `#0B0E1A` | `Consolas` | Dark grid, neon borders, HUD-like cards. |
| `theme.apple` | `#0071E3` | `#FF375F` | `#F5F5F7` | `SF Pro Display` | Minimal, light gray background, large radius. |
| `theme.google` | `#1A73E8` | `#EA4335` | `#E8F0FE` | `Google Sans` | Google Material-like color system. |

Compatibility aliases: `default`, `default_blue`, `theme.default_blue`, `tech_blue`, and `theme.tech_blue` all resolve to Tech Blue.

### Theme Sources

| Source | Example | Status |
| --- | --- | --- |
| Built-in theme | `"theme.claude"` | Implemented |
| Built-in alias | `"default"` | Implemented |
| External single-file JSON | `"./themes/company_blue.json"` | Implemented |
| External directory theme | `"./themes/company_modular"` | Implemented, reads `theme.json` |
| Inline dict | `{ "name": "custom", "extends": "theme.tech_blue" }` | Implemented |
| Direct `Theme` object | `Deck(theme=my_theme)` | Implemented |

### Theme JSON Fields

Themes support both flat fields and grouped fields. Flat fields such as `primary`, `font_family`, and `page_margin` are mapped into token groups. Grouped fields such as `tokens.colors.primary` also work.

| Field | Type | Description |
| --- | --- | --- |
| `name` | `string` | Theme name. |
| `extends` | `string/path` | Parent built-in theme, external file, or directory theme. |
| `metadata` | `object` | Descriptive metadata such as `display_name`, `suitable_for`, `visual_features`. |
| `slide_width` / `slide_height` | `float` | Page size in inches. |
| `tokens` | `object/string/list` | Token fragments, inline or external JSON. |
| `colors` | `object` | Color tokens. |
| `fonts` | `object` | Font and type scale tokens. |
| `spacing` | `object` | Spacing tokens. |
| `radius` / `radius_tokens` | `object` | Radius tokens. |
| `shadow` | `object` | Shadow tokens, including fallback offset and native shadow blur. |
| `chart_palette` | `list[str]` | Chart palette. |
| `card_shadow` | `boolean` | Enables card shadow. |
| `gradient` | `object` | Background gradient with `stops[]` and `angle`. |
| `background_pattern` | `string` | Renderer currently supports `scanlines` and `grid`. |
| `decorations` | `object` | Theme decoration tokens such as `accent_bar_width`, `footer_line_width`, `footer_line_lengths`, `card_radius`, `card_top_border`. |
| `components` | `object/string/list` | Component default styles for `component_default_style()`. |
| `component_styles` | `object/string/list` | Component style tokens converted into `ComponentStyle`. |

### Token Fields

| Token Group | Fields |
| --- | --- |
| `ColorTokens` | `background`, `surface`, `surface_alt`, `surface_white`, `primary`, `primary_dark`, `primary_soft`, `primary_tint`, `accent`, `accent_soft`, `accent_tint`, `secondary`, `success`, `success_soft`, `warning`, `warning_soft`, `danger`, `text_primary`, `text_secondary`, `text_tertiary`, `border`, `border_light`, `gray_50`, `gray_100`, `gray_200`, `gray_700`, `shadow_light`, `shadow_card`. |
| `FontTokens` | `family`, `title_font`, `mono_font`, `latin_font`, `caption_font`, `title_size`, `subtitle_size`, `h1_size`, `h2_size`, `body_size`, `caption_size`, `tiny_size`, `display_size`. |
| `SpacingTokens` | `base`, `xs`, `sm`, `md`, `lg`, `xl`, `page_margin`, `page_x`, `page_y`, `title_top`, `content_top`, `footer_y`, `gutter`, `card_padding`. |
| `RadiusTokens` | `sm`, `md`, `lg`. |
| `ShadowTokens` | `light_offset_x`, `light_offset_y`, `card_offset_x`, `card_offset_y`, `blur_radius`, `distance`, `opacity`, `direction`. |

### Style Priority

```text
Theme generated defaults
  < theme.components / theme.component_styles
  < block.style
```

Components read merged values from `ctx.style`, so agents normally provide content props and let the theme decide color, type scale, border, radius, shadow, and chart palette.

## Layout System

| Mode | Example | Description |
| --- | --- | --- |
| `grid` | `{"mode": "grid", "col": 1, "span": 4, "row": 1, "row_span": 2}` | Grid placement relative to the page `content_box`. |
| `absolute` | `{"mode": "absolute", "x": 1, "y": 2, "w": 4, "h": 1}` | Absolute inch coordinates. |
| `zone` | `{"mode": "zone", "zone": "content"}` | Reserved zone placement; built-in zones are currently limited. |

Built-in page layouts are `cover`, `section`, `standard`, `blank`, `full_bleed`, `closing`, and `qa`. Inline layout specs support `{"type": "layout.grid", "columns": 12, "rows": 6, "gap": 0.2}`.

## Masters And Chrome

Current built-in masters are `default`, `tech_blue`, and `blank`.

| Chrome | Description |
| --- | --- |
| `accent_bar` | Top-left accent bar; width can be controlled by `decorations.accent_bar_width`. |
| `footer` | Footer text and a lightweight footer line. |
| `page_number` | Page number format such as `{current} / {total}`. |
| `logo` | Text logo. |
| `title` / `subtitle` | Page title visibility. |
| `section` | Section label. |

```json
{
  "masters": {
    "tech_blue": {
      "type": "master.tech_blue",
      "chrome": {
        "footer": {"visible": true, "text": "SlideForge"},
        "page_number": {"visible": true, "format": "{current} / {total}"},
        "accent_bar": {"visible": true}
      }
    }
  }
}
```

## Renderer

Components use `PptxRenderer` helpers instead of calling `python-pptx` directly. This keeps units, colors, fonts, theme defaults, cards, charts, icons, and images centralized.

| Helper | Description |
| --- | --- |
| `background(slide)` | Theme background with solid fill, gradient, and light patterns. |
| `rect(...)` | Rectangle/rounded rectangle with opacity, line width, and dash style. |
| `line(...)` | Lines for connectors, axes, and chart guides. |
| `circle(...)` | Circle nodes and placeholders with optional opacity. |
| `text(...)` | Text box with font, alignment, vertical alignment, and line spacing. |
| `bullet_list(...)` | Bullet list. |
| `picture(...)` | Image rendering with `contain` / `cover`. |
| `icon_picture(...)` | SVG icon rendered as transparent PNG and inserted into PPTX. |
| `add_card(...)` | Unified card with fallback shadow and native shadow support. |
| `add_metric_card(...)` | Metric card. |
| `add_status_timeline_node(...)` | Timeline node. |
| `add_process_step_card(...)` | Process step card. |
| `add_table(...)` | Table renderer. |

## Export Screenshots

```python
from ppt_ui.export import export_pptx_screenshots

export_pptx_screenshots("examples/demo.pptx", "examples/demo_screenshots")
```

| Behavior | Description |
| --- | --- |
| Overwrite | The output screenshot directory is overwritten on each run. |
| Naming | Files are named `slide_01.png`, `slide_02.png`, and so on. |
| Dependency | Requires Windows PowerPoint COM. Without PowerPoint or COM access, `ScreenshotExportError` is raised. |
| Showcase | `build_demo_showcase()` combines screenshots into one gallery image. |

## Icons

`media.icon` uses the Iconify API by default. It supports frontend dot style and Iconify colon style:

```json
{
  "type": "media.icon",
  "props": {
    "name": "lucide.sparkles",
    "color": "primary",
    "size": 96,
    "stroke_width": 1.8
  }
}
```

Common aliases include `lucide`, `heroicons`, `remix`/`ri`, `tabler`, `ph`, `mdi`, `material`, `fa`, `bootstrap`/`bi`, `carbon`, `fluent`, `radix`, `octicon`, `simple-icons`, `solar`, `mingcute`, `hugeicons`, and `iconamoon`.

Local SVG extension:

```python
from pathlib import Path
from ppt_ui import Deck, LocalSvgIconProvider

deck = Deck()
deck.icons.register(LocalSvgIconProvider(Path("assets/icons"), prefix="brand"))
deck.icons.register_alias("company", "brand")
```

## Full Examples

### JSON

```json
{
  "schema_version": "0.2",
  "title": "Mini Deck",
  "theme": "theme.claude",
  "default_master": "tech_blue",
  "pages": [
    {
      "type": "page.standard",
      "title": "Metrics And Trend",
      "subtitle": "Multiple independent blocks on one page",
      "blocks": [
        {
          "type": "data.metric_cards",
          "layout": {"mode": "grid", "col": 1, "span": 4, "row": 1, "row_span": 2},
          "props": {
            "cards": [
              {"label": "Accuracy", "value": "92.3%", "delta": "+3.1%", "compare": "vs previous", "icon": "AC"},
              {"label": "AUC", "value": "0.948", "delta": "+0.026", "compare": "validation", "icon": "AU"}
            ]
          }
        },
        {
          "type": "chart.line",
          "layout": {"mode": "grid", "col": 5, "span": 8, "row": 1, "row_span": 2},
          "props": {
            "categories": ["4/29", "5/6", "5/13"],
            "series": [{"name": "Coverage", "values": [23, 36, 48]}]
          }
        }
      ]
    }
  ]
}
```

### External Theme

Single-file theme:

```json
{
  "name": "company_blue",
  "extends": "theme.tech_blue",
  "primary": "#0052CC",
  "accent": "#6554C0",
  "font_family": "Aptos",
  "chart_palette": ["#0052CC", "#6554C0", "#36B37E"]
}
```

Directory theme:

```text
themes/company_modular/
  theme.json
  tokens.json
  components/
    data.json
    chart.json
```

```json
{
  "name": "company_modular",
  "extends": "theme.tech_blue",
  "tokens": "./tokens.json",
  "components": ["./components/data.json", "./components/chart.json"]
}
```

## Agent Usage Guide

Recommended agent workflow:

1. Understand the user's goal and content type.
2. Split the presentation into pages such as `page.cover`, `page.standard`, `page.section`, and `page.qa`.
3. Choose multiple blocks per page, such as `data.metric_cards`, `chart.line`, and `table.comparison`.
4. Use grid layouts or absolute boxes to allocate space.
5. Fill content props and avoid repeating visual details.
6. Pick a theme such as `theme.claude` or `theme.tech_blue`.
7. Pass JSON to `deck_from_json()` and render the deck.

Common errors:

| Error | Result |
| --- | --- |
| Unknown `type` | Strict parser raises `UNKNOWN_COMPONENT_TYPE`. |
| Missing `pages` | Parser raises `MISSING_PAGES`. |
| `chart.line.series[].values` length differs from `categories` | Warning is stored in `deck.diagnostics`. |
| Table row length differs from headers | Warning is stored in `deck.diagnostics`. |
| Content is too long | PowerPoint may auto-fit text or the visual may overflow; shorten or split the content. |

## Component Extension Guide

Steps to add `chart.scatter`:

1. Add a component class in `ppt_ui/components/blocks.py` with `from_props()` and `render(ctx, box)`.
2. Register it in `ppt_ui/components/registry.py` with `registry.register("chart.scatter", ScatterChartComponent.from_props)`.
3. Add parser validation in `ppt_ui/schema/parser.py` if needed.
4. Add `chart.scatter.default` to theme JSON `components` or `component_styles`.
5. Add a Python helper in `ChartNamespace` in `ppt_ui/api.py`.
6. Add an example to `examples/sample_deck.json`.
7. Add tests under `tests/`.
8. Update this documentation.

## FAQ

### Are generated PPT files editable?

Yes. Text, shapes, tables, native charts, and pictures are written into a regular `.pptx`. Complex icons are rendered as transparent PNGs before insertion, so the icon image itself is not an editable vector shape.

### Why not let agents write python-pptx directly?

Low-level shape code scatters style, coordinates, and layout decisions across every agent output. SlideForge keeps those decisions in themes, layouts, masters, and reusable components.

### What if Chinese fonts render incorrectly?

Theme font names such as `font_family` and `title_font_family` must exist on the machine opening/rendering the deck. Use common fonts or install the required font family.

### How do I disable screenshot export?

Run `uv run python examples/demo_deck.py --no-screenshots`.

### How do I generate only the main demo?

Run `uv run python examples/demo_deck.py --skip-theme-demos`.

### What does screenshot export depend on?

It depends on Windows, installed PowerPoint, and a working COM automation environment. PPTX generation still works without those dependencies.

## Roadmap

- More charts: scatter, area, radar, waterfall.
- A fuller layout engine: Row, Column, Spacer, Padding, Alignment.
- Automatic text fitting and overflow diagnostics.
- Stronger JSON Schema validation.
- More theme packages and a theme marketplace.
- Better SVG/icon caching and offline support.
- Agent prompt templates.
- Web preview.
