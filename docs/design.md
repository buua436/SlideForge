# SlideForge Architecture Design

Status: Draft for pre-v1 implementation

Audience: maintainers, contributors, and agents that generate SlideForge JSON DSL

This document defines the target architecture for SlideForge before the first public release. Because the project has not shipped v1 yet, this design intentionally does not preserve the old "one component equals one slide" model. The new design treats pages, layouts, masters, and components as separate concepts.

## 1. Design Goals

SlideForge is an agent-oriented PPT UI framework. Its core job is to turn structured semantic input into a consistent, editable PowerPoint deck.

The framework should support:

- One slide containing multiple independent components.
- Components that only render their own content inside a provided layout box.
- Page-level configuration for common PPT elements such as title, subtitle, footer, logo, page number, and notes.
- Multiple registered masters within one deck.
- Per-page choice to use a master, override a master, or skip master rendering.
- A layout system that keeps agents away from raw PowerPoint coordinates whenever possible.
- A style cascade that makes theme, master, page, layout, component, and block overrides predictable.
- A parser pipeline that validates and normalizes JSON before rendering.
- Structured diagnostics instead of raw Python exceptions where possible.
- Future growth to many component families, variants, themes, masters, and media providers.

## 2. Non-Goals For The First Architecture Pass

The following are intentionally not required in the first implementation pass:

- Backward compatibility with the current demo DSL.
- Full CSS-like layout.
- Full auto-pagination.
- Full visual regression infrastructure.
- Complete SVG-to-PPT vector conversion.
- Web preview.
- Automatic design-quality scoring.

The architecture should leave room for these features, but the first implementation should stay small.

## 3. Core Principle

The most important rule:

```text
Slide/Page owns page chrome.
Layout owns space allocation.
Component owns content rendering.
Master owns shared deck-level page rules.
Theme owns visual tokens.
```

Components must not render page titles, page numbers, global footers, logos, or deck-wide decorations. A component receives a `Box` and renders only inside that box.

## 4. Layered Model

Target hierarchy:

```text
Deck
  -> ThemeRegistry / Theme
  -> MasterRegistry / default_master
  -> PageRegistry
  -> LayoutRegistry
  -> ComponentRegistry
  -> Pages
      -> Page
          -> PageLayout
          -> PageChrome overrides
          -> Blocks
              -> ComponentInstance
                  -> Component
```

Responsibilities:

| Layer | Responsibility |
| --- | --- |
| `Deck` | Owns metadata, theme, registries, default master, pages, render entrypoint. |
| `Theme` | Owns colors, typography, spacing, radius, shadow, and component style tokens. |
| `SlideMaster` | Owns shared page chrome and default page layouts for a family of pages. |
| `PageLayout` | Defines the page skeleton: content area, title area, grid, zones, and default block placement strategy. |
| `Page` | A single slide instance with title, subtitle, master selection, layout selection, chrome overrides, blocks, and notes. |
| `Block` / `ComponentInstance` | A component occurrence on a page, with `type`, `variant`, `props`, `layout`, `style`, and metadata. |
| `Component` | Reusable renderer for a content unit such as chart, metric card, table, timeline, or image. |
| `Renderer` | Low-level drawing abstraction over `python-pptx`. |

## 5. Object Model

### 5.1 Deck

`Deck` is the root object.

Suggested fields:

```python
@dataclass
class Deck:
    title: str = "Untitled Deck"
    theme: Theme = field(default_factory=Theme)
    masters: MasterRegistry = field(default_factory=MasterRegistry)
    default_master: str = "default"
    pages: list[Page] = field(default_factory=list)
    metadata: DeckMetadata = field(default_factory=DeckMetadata)
```

Responsibilities:

- Resolve the active theme.
- Resolve the default master.
- Store pages in order.
- Provide `render(output_path)`.
- Pass page index and total page count to the renderer.

`Deck` should not render individual blocks itself. It delegates to `PptxRenderer`, `Page`, `SlideMaster`, `PageLayout`, and `Component`.

### 5.2 Theme

`Theme` is a token container. It decides visual style, not page structure.

Token groups:

| Group | Examples |
| --- | --- |
| Colors | `primary`, `accent`, `surface`, `border`, `text_primary`, `success`, `warning` |
| Typography | `font_family`, `title_size`, `body_size`, `caption_size` |
| Spacing | `page_margin`, `content_top`, `gutter`, `card_padding` |
| Radius | `radius_sm`, `radius_md`, `radius_lg` |
| Shadow | `shadow_light`, `shadow_card`, offsets |
| Component styles | `chart.line.default`, `table.comparison.compact`, `metric_card.default` |

Theme should not decide whether a footer appears. That belongs to the master/page chrome layer.

### 5.2.1 Theme Loading

Theme loading is now intentionally storage-agnostic. A deck can select:

| Source | Example | Status |
| --- | --- | --- |
| Built-in theme name | `"default_blue"` | Implemented |
| Built-in alias | `"default"` | Implemented |
| External single-file JSON | `"./themes/company_blue.json"` | Implemented |
| External theme directory | `"./themes/company_modular"` | Implemented |
| Inline JSON object | `{ "name": "custom", "extends": "default_blue", "tokens": {} }` | Implemented |

Directory themes use `theme.json` as the entry file:

```text
themes/company_modular/
  theme.json
  tokens.json
  components/
    data.json
    chart.json
```

`theme.json` can reference other JSON fragments relative to itself:

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

The resolved object is always a `Theme`. Components do not know whether the theme came from an internal name, a file, a directory, or an inline object.

Token references are supported inside component defaults:

```json
{
  "data.metric_cards": {
    "default": {
      "fill": "{colors.surface_white}",
      "border": "{colors.border}",
      "accent": "{colors.primary}"
    }
  }
}
```

Implemented loader objects:

| Object | Purpose |
| --- | --- |
| `ThemeLoader` | Loads a theme from name, path, directory, inline dict, or `Theme`. |
| `ThemeRegistry` | Registers built-in themes and optional named theme paths. |
| `get_theme()` | Convenience wrapper around `ThemeLoader`. |

Current built-in themes:

Built-in theme definitions are JSON files under `ppt_ui/themes/`. The Python registry only maps stable names such as `theme.tech_blue` to those files.

| Theme | Intent |
| --- | --- |
| `theme.tech_blue` | Default blue-purple technical deck. |
| `theme.academic_clean` | Formal thesis, paper, and experiment-report style. |
| `theme.business_navy` | Navy and restrained gold business presentation style. |
| `theme.data_dashboard` | Metric-heavy report and dashboard style with richer chart palette. |
| `theme.medical_teal` | Clean teal style for medical, biological, and scientific decks. |
| `theme.dark_tech` | Dark launch/demo style with cyan-purple accents. |
| `theme.claude_warm` | Warm paper-like narrative style. |

### 5.3 MasterRegistry

`MasterRegistry` stores named masters.

```python
@dataclass
class MasterRegistry:
    masters: dict[str, SlideMaster] = field(default_factory=dict)

    def register(self, name: str, master: SlideMaster) -> None: ...
    def get(self, name: str) -> SlideMaster: ...
```

Rules:

- A deck can register multiple masters.
- A deck has one `default_master`.
- A page can choose a master by name.
- A page can disable master rendering with `use_master: false`.
- A page can override master settings locally.

### 5.4 SlideMaster

`SlideMaster` defines shared page chrome and default page layouts.

```python
@dataclass
class SlideMaster:
    name: str
    chrome: PageChromeConfig
    layouts: dict[str, PageLayout]
    background: BackgroundConfig | None = None

    def resolve_layout(self, layout_name: str) -> PageLayout: ...
    def render_background(self, ctx: RenderContext, page: Page) -> None: ...
    def render_chrome(self, ctx: RenderContext, page: Page, page_index: int, total_pages: int) -> None: ...
```

Master owns:

- Background defaults.
- Accent bar defaults.
- Logo defaults.
- Footer defaults.
- Page number defaults.
- Header defaults.
- Default title placement.
- Registered page layouts.

Master does not own business content.

### 5.5 PageLayout

`PageLayout` defines a page skeleton.

Examples:

- `cover`
- `standard`
- `section`
- `blank`
- `closing`
- `qa`
- `dashboard`
- `full_bleed`

Suggested fields:

```python
@dataclass
class PageLayout:
    name: str
    page_box: BoxSpec | None = None
    title_box: BoxSpec | None = None
    subtitle_box: BoxSpec | None = None
    content_box: BoxSpec | None = None
    grid: GridSpec | None = None
    zones: dict[str, BoxSpec] = field(default_factory=dict)
```

Responsibilities:

- Resolve the title area.
- Resolve the content area.
- Provide named zones if needed.
- Provide grid configuration for block placement.

`PageLayout` should not render charts, tables, or other business components.

### 5.6 Page

`Page` is a single slide instance.

```python
@dataclass
class Page:
    type: str = "page.standard"
    layout: str | LayoutSpec = "standard"
    master: str | None = None
    use_master: bool = True
    master_overrides: MasterOverride = field(default_factory=MasterOverride)
    chrome: PageChromeOverride = field(default_factory=PageChromeOverride)
    title: str = ""
    subtitle: str = ""
    blocks: list[Block] = field(default_factory=list)
    notes: str = ""
    hidden: bool = False
    metadata: dict[str, object] = field(default_factory=dict)
```

Page owns:

- Page title and subtitle.
- Master selection.
- Master override.
- Page chrome override.
- Layout selection.
- Block list.
- Notes and metadata.

Page does not implement component-specific logic.

### 5.7 PageChrome

`PageChrome` is the common PPT UI around content.

Chrome elements:

| Element | Examples |
| --- | --- |
| Title | title text, subtitle, title position |
| Header | section label, report name |
| Footer | brand text, disclaimer, data source |
| Page number | `{current} / {total}` |
| Logo | text logo or future image logo |
| Accent | left accent bar, corner line, light decorative marks |
| Background | color, gradient, image, or light pattern |

Suggested config:

```python
@dataclass
class PageChromeConfig:
    title: TitleChromeConfig = field(default_factory=TitleChromeConfig)
    logo: LogoConfig = field(default_factory=LogoConfig)
    footer: FooterConfig = field(default_factory=FooterConfig)
    page_number: PageNumberConfig = field(default_factory=PageNumberConfig)
    accent_bar: AccentBarConfig = field(default_factory=AccentBarConfig)
```

Visibility should be explicit:

```json
{
  "footer": {"visible": true, "text": "SlideForge"},
  "page_number": {"visible": true, "format": "{current} / {total}"},
  "accent_bar": {"visible": true}
}
```

### 5.8 Block / ComponentInstance

`Block` is one instance of a component on a page.

```python
@dataclass
class Block:
    type: str
    props: dict[str, object] = field(default_factory=dict)
    layout: BlockLayout = field(default_factory=BlockLayout)
    style: dict[str, object] = field(default_factory=dict)
    id: str | None = None
    visible: bool = True
    metadata: dict[str, object] = field(default_factory=dict)
```

Why `Block` matters:

- One page can contain multiple components.
- The same component type can appear multiple times.
- Each instance can have its own layout, style, id, and visibility.
- Diagnostics can refer to `block.id`.

### 5.9 Component

`Component` is a pure content renderer.

```python
class Component(Protocol):
    type: str

    def measure(self, ctx: MeasureContext, props: dict[str, object]) -> SizeHint: ...
    def render(self, ctx: RenderContext, box: Box, props: dict[str, object], style: ComponentStyle) -> None: ...
```

MVP can keep a simpler interface:

```python
def render(self, ctx: RenderContext, box: Box) -> None:
    ...
```

But the conceptual contract should already be:

- Component does not render page title.
- Component does not render page footer.
- Component does not decide global layout.
- Component can provide size hints.
- Component can emit diagnostics.

## 6. JSON DSL v0.2

The new DSL should be page-first and block-based.

### 6.1 Top-Level Deck

```json
{
  "schema_version": "0.2",
  "title": "SlideForge Demo",
  "theme": "default_blue",
  "default_master": "tech_blue",
  "masters": {
    "tech_blue": {
      "type": "master.tech_blue",
      "chrome": {
        "footer": {
          "visible": true,
          "text": "SlideForge · Agent-driven PPT UI Framework"
        },
        "page_number": {
          "visible": true,
          "format": "{current} / {total}"
        },
        "accent_bar": {
          "visible": true
        }
      }
    },
    "blank": {
      "type": "master.blank",
      "chrome": {
        "footer": {"visible": false},
        "page_number": {"visible": false},
        "accent_bar": {"visible": false}
      }
    }
  },
  "pages": []
}
```

Top-level fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `schema_version` | `string` | Yes | DSL version, first target is `0.2`. |
| `title` | `string` | No | Deck title. |
| `theme` | `string/object` | No | Theme name or future inline theme object. |
| `default_master` | `string` | No | Master used when a page does not specify one. |
| `masters` | `object` | No | Named master definitions. |
| `pages` | `array<object>` | Yes | Page list. |
| `metadata` | `object` | No | Author, date, language, version, etc. |
| `export` | `object` | No | Future output options. |

Use `pages`, not `slides`, in the target DSL. The rendered output is still PowerPoint slides, but the internal concept is page-oriented.

### 6.2 Page Object

```json
{
  "type": "page.standard",
  "layout": "standard",
  "master": "tech_blue",
  "use_master": true,
  "title": "核心指标与趋势分析",
  "subtitle": "用于展示实验结果和业务趋势",
  "chrome": {
    "page_number": {"visible": true},
    "footer": {"visible": true}
  },
  "blocks": []
}
```

Page fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `type` | `string` | Yes | Page type, such as `page.standard`, `page.cover`, `page.blank`. |
| `layout` | `string/object` | No | Layout name or inline layout spec. |
| `master` | `string` | No | Master name. If absent, use deck `default_master`. |
| `use_master` | `boolean` | No | If `false`, skip master background and chrome. |
| `master_overrides` | `object` | No | Overrides to the selected master. |
| `chrome` | `object` | No | Page-level chrome overrides. |
| `title` | `string` | No | Page title. |
| `subtitle` | `string` | No | Page subtitle. |
| `blocks` | `array<object>` | No | Components on this page. |
| `notes` | `string` | No | Speaker notes, planned. |
| `hidden` | `boolean` | No | Skip page when rendering if true. |
| `metadata` | `object` | No | Page metadata. |

`master_overrides` and `chrome` need a clear relationship:

- `master_overrides` changes master-derived defaults before rendering.
- `chrome` is a convenient page-level override for common page chrome.
- Parser may normalize both into one effective chrome config.

### 6.3 Block Object

```json
{
  "id": "main_trend",
  "type": "chart.line",
  "layout": {
    "mode": "grid",
    "col": 5,
    "span": 8,
    "row": 1,
    "row_span": 2
  },
  "props": {
    "categories": ["4/29", "5/6", "5/13"],
    "series": [
      {"name": "指标 A", "values": [320, 540, 580]}
    ]
  },
  "style": {
    "variant": "default"
  },
  "visible": true
}
```

Block fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `string` | No | Stable block id for diagnostics and references. |
| `type` | `string` | Yes | Component type, such as `chart.line`. |
| `layout` | `object` | No | Layout placement. |
| `props` | `object` | No | Component-specific data. |
| `style` | `object` | No | Instance-level style overrides. |
| `visible` | `boolean` | No | Whether to render the block. |
| `metadata` | `object` | No | Extra metadata for agents or tooling. |

All component-specific fields must live under `props`.

Good:

```json
{
  "type": "chart.line",
  "props": {
    "categories": [],
    "series": []
  }
}
```

Avoid:

```json
{
  "type": "chart.line",
  "categories": [],
  "series": []
}
```

## 7. Master Design

### 7.1 Multiple Masters

A deck can register multiple masters:

```json
{
  "default_master": "tech_blue",
  "masters": {
    "tech_blue": {},
    "business": {},
    "blank": {}
  }
}
```

Use cases:

- Standard report pages use `tech_blue`.
- Full-image pages use `blank`.
- Appendix pages use a lighter master.
- A deck can mix business and technical sections.

### 7.2 Page Master Resolution

Resolution algorithm:

```text
if page.use_master is false:
    effective_master = None
else if page.master is set:
    effective_master = master_registry[page.master]
else:
    effective_master = master_registry[deck.default_master]
```

Then:

```text
effective_chrome =
    merge(master.chrome, page.master_overrides.chrome, page.chrome)
```

Rules:

- `use_master: false` disables master background and master chrome.
- Page can still define local `chrome` even when `use_master: false`.
- `master_overrides` must not mutate the registered master.
- Overrides are page-local.

### 7.3 Master vs Theme vs Layout

| Concept | Owns | Does not own |
| --- | --- | --- |
| `Theme` | Visual tokens. | Whether footer appears. |
| `Master` | Shared page chrome and default layouts. | Business content. |
| `PageLayout` | Page skeleton and layout regions. | Colors and typography tokens. |
| `Page` | Page instance data and overrides. | Global token definitions. |
| `Component` | Content rendering inside a box. | Page title, footer, page number. |

### 7.4 Required Built-In Masters

First implementation should include:

| Master | Purpose |
| --- | --- |
| `default` | Safe generic master. |
| `tech_blue` | Modern blue-purple technical presentation. |
| `blank` | No chrome, no footer, no page number. |

Additional masters can be added later:

- `business_report`
- `thesis_defense`
- `academic`
- `dark_tech`
- `brand_custom`

## 8. Page Types And Page Layouts

### 8.1 Built-In Page Types

First implementation:

| Page type | Purpose |
| --- | --- |
| `page.cover` | Cover page. |
| `page.standard` | Most content pages. |
| `page.section` | Chapter divider. |
| `page.blank` | Fully controlled page, often no master. |
| `page.closing` | Conclusion page. |
| `page.qa` | Q&A page. |

Future page types:

- `page.dashboard`
- `page.full_bleed`
- `page.appendix`
- `page.comparison`
- `page.report`

### 8.2 PageLayout Contract

Every page layout should provide:

| Region | Purpose |
| --- | --- |
| `page_box` | Full safe region. |
| `title_box` | Title text region. |
| `subtitle_box` | Subtitle text region. |
| `content_box` | Main block layout region. |
| `footer_box` | Optional footer region. |
| `page_number_box` | Optional page number region. |

Layouts may also provide named zones:

```json
{
  "layout": {
    "type": "layout.zones",
    "zones": {
      "left": {"x": 0.55, "y": 1.55, "w": 5.9, "h": 4.8},
      "right": {"x": 6.75, "y": 1.55, "w": 5.9, "h": 4.8}
    }
  }
}
```

## 9. Layout System

### 9.1 Coordinate Units

All physical coordinates use inches.

Rationale:

- `python-pptx` works naturally with inches.
- PowerPoint slide sizes are commonly described in inches.
- It avoids pixel/DPI ambiguity.

### 9.2 Layout Modes

MVP should support two modes:

| Mode | Use case |
| --- | --- |
| `absolute` | Precise placement. |
| `grid` | Agent-friendly placement inside a page content grid. |

Future modes:

- `row`
- `column`
- `stack`
- `flow`
- `fit`
- `zone`

### 9.3 Absolute Layout

```json
{
  "layout": {
    "mode": "absolute",
    "x": 0.8,
    "y": 1.6,
    "w": 5.2,
    "h": 2.4
  }
}
```

Fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `mode` | `string` | No | `absolute`. |
| `x` | `number` | Yes | Left position in inches. |
| `y` | `number` | Yes | Top position in inches. |
| `w` | `number` | Yes | Width in inches. |
| `h` | `number` | Yes | Height in inches. |

### 9.4 Grid Layout

```json
{
  "layout": {
    "mode": "grid",
    "col": 1,
    "span": 4,
    "row": 1,
    "row_span": 2
  }
}
```

Grid is resolved inside the page layout's `content_box`.

Recommended default:

```json
{
  "columns": 12,
  "rows": 6,
  "gap": 0.2
}
```

Fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `mode` | `string` | No | `grid`. |
| `col` | `integer` | Yes | 1-based column start. |
| `span` | `integer` | Yes | Number of columns. |
| `row` | `integer` | No | 1-based row start. |
| `row_span` | `integer` | No | Number of rows. |
| `zone` | `string` | No | Optional named zone. |

Rules:

- `col` is 1-based for agent readability.
- `span` must be positive.
- If row is omitted, layout manager may auto-place only in future versions.
- MVP should require explicit row for predictable output.

### 9.5 Layout Diagnostics

Layout manager should emit diagnostics for:

- Block outside content box.
- Grid span exceeds column count.
- Row span exceeds row count.
- Overlapping blocks.
- Missing layout where required.
- Component rendered below its minimum size.

## 10. Component Model

### 10.1 Component Families And Variants

Component types use namespace form:

```text
family.variant
```

Examples:

- `chart.line`
- `chart.bar`
- `chart.pie`
- `chart.donut`
- `data.metric_cards`
- `table.comparison`
- `narrative.timeline`
- `media.image`

The registry should treat family and variant as first-class concepts.

```python
registry.register("chart.line", LineChartComponent)
registry.register("chart.bar", BarChartComponent)
```

Future equivalent:

```python
registry.register_family("chart")
registry.register_variant("chart", "line", LineChartComponent)
```

### 10.2 Component Props

Every component defines its own props schema.

Example:

```json
{
  "type": "data.metric_cards",
  "props": {
    "cards": [
      {
        "label": "Accuracy",
        "value": "92.3%",
        "delta": "+3.1%",
        "compare": "vs previous",
        "status": "positive",
        "icon": "target"
      }
    ]
  }
}
```

Components should not read page-level fields such as `title` or `footer`.

### 10.3 Component Size Hints

Each component should be able to describe recommended sizing.

```python
@dataclass
class SizeHint:
    min_w: float
    min_h: float
    preferred_w: float
    preferred_h: float
    max_w: float | None = None
    max_h: float | None = None
    aspect_ratio: float | None = None
```

MVP can keep these as metadata and diagnostics only.

Examples:

| Component | Minimum | Preferred |
| --- | --- | --- |
| `data.metric_card` | 1.6 x 0.9 | 2.4 x 1.2 |
| `data.metric_cards` | 4.0 x 1.2 | 8.0 x 1.5 |
| `chart.line` | 4.0 x 2.4 | 7.0 x 3.8 |
| `table.comparison` | 5.0 x 2.6 | 8.5 x 4.0 |
| `narrative.timeline` | 6.0 x 2.2 | 10.5 x 3.2 |

### 10.4 Component Output Contract

A component may output:

- Shapes.
- Text.
- Charts.
- Images.
- Diagnostics.

A component must not:

- Add a new slide.
- Change deck theme.
- Mutate master registry.
- Render page-level chrome.
- Depend on global absolute coordinates except through the provided `Box`.

## 11. Style Cascade

SlideForge needs predictable style resolution.

Recommended priority from low to high:

```text
Theme base tokens
< Theme component family style
< Theme component variant style
< Master defaults
< PageLayout defaults
< Page chrome/style overrides
< Block component style
< Block inline style
```

Alternative order question:

- Master and PageLayout might need to override theme component styles for a particular deck type.
- Component variants might need to override master defaults for the component itself.

Recommended practical rule:

```text
Global tokens come from Theme.
Page chrome defaults come from Master.
Layout defaults come from PageLayout.
Component defaults come from Theme component styles.
Instance overrides come from Block.style.
```

Effective style for a block:

```text
effective_component_style =
    merge(
        theme.component_style(family),
        theme.component_style(family.variant),
        page_layout.component_defaults.get(type),
        page.component_style_overrides.get(type),
        block.style
    )
```

Effective page chrome:

```text
effective_chrome =
    merge(
        master.chrome,
        page_layout.chrome_defaults,
        page.master_overrides.chrome,
        page.chrome
    )
```

Merge rules:

- Objects merge recursively.
- Scalars replace previous values.
- `null` may mean "unset" only if explicitly supported.
- Unknown style keys should emit warnings, not fail hard in MVP.

## 12. Render Lifecycle

Target render sequence for each page:

```text
1. Skip page if hidden.
2. Create a blank PowerPoint slide.
3. Resolve theme.
4. Resolve selected master.
5. Resolve page layout.
6. Resolve effective page chrome.
7. Render background.
8. Render master/page chrome behind content if configured.
9. Compute content box and layout grid.
10. Resolve each block to a concrete Box.
11. Validate block sizes and overlaps.
12. Resolve component props and effective style.
13. Render components.
14. Render foreground chrome if needed.
15. Attach notes if supported.
16. Collect diagnostics.
```

Chrome layering:

| Layer | Examples |
| --- | --- |
| Background | background fill, large decorative shapes |
| Back chrome | accent bar, logo watermark, section background |
| Content | blocks/components |
| Foreground chrome | page number, footer, small labels |

Most chrome can be rendered before content. Page number and footer may be rendered after content to stay visible.

## 13. Parser Pipeline

Parser should not directly jump from raw JSON to rendering. It should produce a normalized internal model.

```text
raw JSON
-> parse JSON
-> validate top-level schema
-> normalize DSL v0.2
-> resolve registries
-> validate page/master/layout/component references
-> build Deck/Page/Block tree
-> render
```

No legacy compatibility is required before v1.

### 13.1 Validation Phases

| Phase | Purpose |
| --- | --- |
| Syntax validation | JSON parse errors. |
| Schema validation | Required fields, field types. |
| Registry validation | Unknown master/page/layout/component type. |
| Layout validation | Invalid grid or absolute boxes. |
| Component props validation | Missing required component props. |
| Render validation | Runtime constraints such as text overflow or chart length mismatch. |

### 13.2 Pydantic vs Dataclass

Recommended:

- Use dataclasses for internal runtime objects.
- Use Pydantic or TypedDict-like schemas for JSON validation.

Reason:

- Internal objects should stay lightweight and easy to instantiate.
- JSON validation needs strong errors for agents.

## 14. Diagnostics System

Diagnostics should be structured.

```python
@dataclass
class Diagnostic:
    level: Literal["error", "warning", "info"]
    code: str
    message: str
    path: str
    suggestion: str | None = None
```

Examples:

```json
{
  "level": "error",
  "code": "UNKNOWN_COMPONENT_TYPE",
  "message": "Unsupported component type: chart.scatter",
  "path": "$.pages[2].blocks[0].type",
  "suggestion": "Use one of: chart.line, chart.bar, chart.pie, chart.donut"
}
```

Recommended diagnostic codes:

| Code | Level | Meaning |
| --- | --- | --- |
| `UNKNOWN_COMPONENT_TYPE` | error | Component type is not registered. |
| `UNKNOWN_PAGE_TYPE` | error | Page type is not registered. |
| `UNKNOWN_MASTER` | error | Page references a missing master. |
| `INVALID_LAYOUT` | error | Layout spec is invalid. |
| `BLOCK_OVERLAP` | warning | Two blocks overlap. |
| `TEXT_OVERFLOW_RISK` | warning | Text may overflow its box. |
| `CHART_SERIES_LENGTH_MISMATCH` | warning | Chart series length does not match categories. |
| `TABLE_ROW_LENGTH_MISMATCH` | warning | Table row length does not match headers. |
| `COMPONENT_TOO_SMALL` | warning | Box is smaller than component size hint. |
| `UNKNOWN_STYLE_KEY` | warning | Style key is not recognized. |

Render can fail on errors and continue with warnings.

## 15. Text Overflow Strategy

Text overflow is one of the highest-risk issues in PPT generation.

Supported strategies:

| Strategy | Behavior |
| --- | --- |
| `shrink` | Reduce font size to fit. |
| `wrap` | Wrap text within box. |
| `truncate` | Truncate and add ellipsis. |
| `clip` | Let PowerPoint clip; not recommended. |
| `error` | Emit diagnostic and fail. |
| `suggest_split` | Emit suggestion to split page; future. |

Default MVP strategy:

```json
{
  "text_overflow": "shrink"
}
```

Recommended hierarchy:

- Titles: `shrink`.
- Captions: `truncate`.
- Table cells: `shrink` or `truncate`.
- Body text: `wrap` then `shrink`.
- Agent mode: warning diagnostics when shrink exceeds threshold.

## 16. Asset, Icon, And Media Pipeline

### 16.1 Asset Registry

Future asset model:

```python
@dataclass
class AssetRegistry:
    roots: list[Path]
    icon_registry: IconRegistry
    image_cache: ImageCache
```

Supported asset types:

| Type | Examples |
| --- | --- |
| `media.image` | Local path, future URL, generated image. |
| `media.icon` | Iconify, Lucide, Heroicons, Remix Icon, local SVG. |
| `media.logo` | Brand logo. |
| `media.svg` | Raw SVG or file path. |

### 16.2 Icon Provider

The icon layer should be separate from business components.

```json
{
  "type": "media.icon",
  "props": {
    "name": "lucide.target",
    "color": "primary",
    "size": 128,
    "stroke_width": 1.8,
    "rotate": 0,
    "flip": "horizontal"
  }
}
```

Renderer options:

| Option | Pros | Cons |
| --- | --- | --- |
| Render SVG to PNG | Reliable in PowerPoint. | Not editable vector. |
| Convert SVG to DrawingML | Editable vector. | More complex. |
| Use text/icon font | Simple. | Font dependency. |

Current MVP behavior:

- `media.icon` accepts frontend-style names such as `lucide.sparkles`, `heroicons.bolt`, `remix.rocket-line`, `tabler.file-code`, `ph.hexagon-bold`, and `mdi.message-text-outline`.
- The default provider normalizes dot syntax to Iconify IDs, fetches SVG from the Iconify API, and renders it to transparent PNG with `resvg-py`.
- Icon props can control `color`, `size`, `width`, `height`, `rotate`, `flip`, `stroke_width`, and `opacity`.
- `props.src` remains supported for local transparent PNG assets when a team wants to ship brand-owned icons.
- If remote resolution or rendering fails, the component falls back to centered text initials from `label` or `name`.
- The renderer keeps icon visuals stable while leaving surrounding cards, text, layout, and charts editable.

Extensibility model:

- `Deck.icons` owns an `IconRegistry`, so each deck can register its own providers and aliases.
- `IconRegistry.register(provider)` adds a new SVG source adapter.
- `IconRegistry.register_alias("company", "brand")` lets DSL authors use `company.logo` while the provider receives `brand:logo`.
- Built-in aliases cover common frontend libraries such as Lucide, Heroicons, Remix Icon, Tabler, Font Awesome, Bootstrap Icons, Material Symbols, MDI, Phosphor, Carbon, Fluent, Radix, Octicons, Simple Icons, Solar, MingCute, and Hugeicons.

```python
from pathlib import Path

from ppt_ui import Deck, LocalSvgIconProvider, media, layout, page

deck = Deck()
deck.icons.register_alias("company", "brand")
deck.icons.register(LocalSvgIconProvider(Path("assets/icons"), prefix="brand"))
deck.add_page(
    page.standard(
        title="Brand Icons",
        blocks=[
            media.icon(
                name="company.logo",
                color="primary",
                layout=layout.grid_item(col=1, span=3, row=1),
            )
        ],
    )
)
```

Recommended MVP:

- Resolve SVG through providers.
- Convert to PNG for insertion.
- Keep vector conversion as future work.

### 16.3 Image Component

`media.image` should support:

```json
{
  "type": "media.image",
  "props": {
    "src": "assets/chart.png",
    "fit": "cover",
    "radius": "md",
    "alt": "Dashboard screenshot"
  }
}
```

Fit modes:

- `contain`
- `cover`
- `stretch`
- `crop`

## 17. Registry Design

Current project has one `ComponentRegistry` for slide factories. Target architecture should split registries.

| Registry | Registers |
| --- | --- |
| `ThemeRegistry` | Named themes. |
| `MasterRegistry` | Named masters. |
| `PageRegistry` | Page types. |
| `LayoutRegistry` | Layout algorithms. |
| `ComponentRegistry` | Component families and variants. |
| `AssetRegistry` | Icons, images, fonts, media assets. |

Suggested APIs:

```python
component_registry.register("chart.line", LineChartComponent)
page_registry.register("page.standard", StandardPage)
layout_registry.register("layout.grid", GridLayout)
master_registry.register("tech_blue", TechBlueMaster)
theme_registry.register("default_blue", DefaultBlueTheme)
```

Unknown type handling should produce diagnostics, not unstructured exceptions.

## 18. Component Families For The First Version

First target components:

| Family | Components |
| --- | --- |
| `slide/page` | `page.cover`, `page.standard`, `page.section`, `page.blank`, `page.closing`, `page.qa` |
| `basic` | `basic.title`, `basic.text`, `basic.divider`, `basic.shape` |
| `layout` | `layout.grid`, `layout.two_column`, `layout.row`, `layout.column` |
| `data` | `data.metric_card`, `data.metric_cards`, `data.progress_bars`, `data.gantt`, `data.heatmap` |
| `chart` | `chart.line`, `chart.bar`, `chart.pie`, `chart.donut` |
| `table` | `table.basic`, `table.comparison` |
| `narrative` | `narrative.timeline`, `narrative.process_flow`, `narrative.roadmap`, `narrative.swot`, `narrative.problem_solution`, `narrative.logic_pyramid` |
| `media` | `media.image`, `media.icon` |

Note: `slide.*` as old page-level names should be replaced by `page.*` in the target DSL. The package can still expose `slide` in Python as an alias later if desired, but the architecture should use `Page`.

## 19. Example DSL

### 19.1 Standard Page With Multiple Components

```json
{
  "schema_version": "0.2",
  "title": "SlideForge Demo",
  "theme": "default_blue",
  "default_master": "tech_blue",
  "masters": {
    "tech_blue": {
      "type": "master.tech_blue",
      "chrome": {
        "footer": {
          "visible": true,
          "text": "SlideForge · Agent-driven PPT UI Framework"
        },
        "page_number": {
          "visible": true,
          "format": "{current} / {total}"
        },
        "accent_bar": {"visible": true}
      }
    }
  },
  "pages": [
    {
      "type": "page.standard",
      "layout": {
        "type": "layout.grid",
        "columns": 12,
        "rows": 6,
        "gap": 0.2
      },
      "title": "核心指标与趋势分析",
      "subtitle": "用于展示实验结果和业务趋势",
      "blocks": [
        {
          "id": "metrics",
          "type": "data.metric_cards",
          "layout": {"mode": "grid", "col": 1, "span": 4, "row": 1, "row_span": 2},
          "props": {
            "cards": [
              {"label": "Accuracy", "value": "92.3%", "delta": "+3.1%"},
              {"label": "AUC", "value": "0.948", "delta": "+0.026"}
            ]
          }
        },
        {
          "id": "trend",
          "type": "chart.line",
          "layout": {"mode": "grid", "col": 5, "span": 8, "row": 1, "row_span": 4},
          "props": {
            "categories": ["4/29", "5/6", "5/13"],
            "series": [
              {"name": "Metric A", "values": [320, 540, 580]}
            ]
          }
        },
        {
          "id": "note",
          "type": "basic.text",
          "layout": {"mode": "grid", "col": 1, "span": 12, "row": 6, "row_span": 1},
          "props": {
            "text": "结论：核心指标稳定上升，建议继续扩大实验流量。"
          }
        }
      ]
    }
  ]
}
```

### 19.2 Page That Disables Master

```json
{
  "type": "page.blank",
  "use_master": false,
  "layout": {
    "type": "layout.absolute"
  },
  "blocks": [
    {
      "type": "media.image",
      "layout": {"mode": "absolute", "x": 0, "y": 0, "w": 13.333, "h": 7.5},
      "props": {
        "src": "assets/fullscreen.png",
        "fit": "cover"
      }
    }
  ]
}
```

### 19.3 Page That Overrides Master Chrome

```json
{
  "type": "page.section",
  "master": "tech_blue",
  "master_overrides": {
    "chrome": {
      "footer": {"visible": false},
      "page_number": {"visible": false}
    }
  },
  "title": "数据展示组件",
  "subtitle": "适用于指标汇报、实验结果、运营分析、商业复盘"
}
```

## 20. Python API Direction

Target Python API should mirror JSON concepts.

```python
from ppt_ui import Deck, block, chart, data, layout, master, page

deck = Deck(
    title="SlideForge Demo",
    theme="default_blue",
    default_master="tech_blue",
)

deck.masters.register("tech_blue", master.tech_blue())

deck.add_page(
    page.standard(
        title="核心指标与趋势分析",
        subtitle="用于展示实验结果和业务趋势",
        layout=layout.grid(columns=12, rows=6),
        blocks=[
            block.component(
                "data.metric_cards",
                layout=layout.grid_item(col=1, span=4, row=1, row_span=2),
                props={
                    "cards": [
                        {"label": "Accuracy", "value": "92.3%", "delta": "+3.1%"}
                    ]
                },
            ),
            chart.line(
                layout=layout.grid_item(col=5, span=8, row=1, row_span=4),
                categories=["4/29", "5/6", "5/13"],
                series=[{"name": "Metric A", "values": [320, 540, 580]}],
            ),
        ],
    )
)

deck.render("examples/demo.pptx")
```

Convenience factories such as `chart.line(...)` should return `Block` or `ComponentInstance`, not a full slide.

Page factories such as `page.standard(...)` should return a `Page`.

## 21. Migration Plan Before v1

Because the project is not released, we can replace the existing architecture without maintaining legacy behavior.

Recommended implementation order:

1. Add new core objects: `Page`, `Block`, `SlideMaster`, `PageLayout`, registries.
2. Add DSL v0.2 parser that reads `pages` and `blocks`.
3. Convert existing renderer helpers to support page chrome and block rendering.
4. Convert existing content logic from `*Slide` classes into pure components.
5. Rebuild demo deck with page/block DSL.
6. Update docs to treat `page.*` as primary.
7. Add tests for parser, layout resolution, master resolution, and component rendering smoke checks.
8. Remove or rename old `*Slide` wrappers if they create conceptual confusion.

### 21.1 Suggested Refactor Mapping

| Current class | Target role |
| --- | --- |
| `TitleSlide` | `page.cover` implementation or `CoverPage` |
| `SectionSlide` | `page.section` implementation |
| `ConclusionSlide` | `page.closing` implementation |
| `QASlide` | `page.qa` implementation |
| `MetricCard` | Keep as component |
| `MetricCardsSlide` | Convert to `data.metric_cards` component |
| `LineChartSlide` | Convert to page wrapper only if needed; main logic becomes `chart.line` component |
| `LineChartBlock` | Keep/rename as `LineChartComponent` |
| `ComparisonTableSlide` | Convert to `table.comparison` component |
| `TimelineSlide` | Convert to `narrative.timeline` component |
| `ProcessFlowSlide` | Convert to `narrative.process_flow` component |
| `GridSlide` | Replace with `page.standard + layout.grid + blocks` |

## 22. Testing Strategy

Testing should cover structure, parser behavior, layout behavior, and visual output.

### 22.1 Unit Tests

Required:

- Parse valid DSL v0.2.
- Reject missing required fields.
- Resolve default master.
- Resolve page-specific master.
- Respect `use_master: false`.
- Resolve grid block boxes.
- Detect invalid grid spans.
- Detect block overlap.
- Resolve component styles.
- Validate chart series length.
- Validate table rows.

### 22.2 Render Smoke Tests

Generate small PPTX files containing:

- One standard page with multiple blocks.
- One blank page without master.
- One page with master override.
- One chart page.
- One table page.
- One narrative page.

### 22.3 Visual Regression

Future:

- Export screenshots.
- Compare against baseline images.
- Allow small pixel tolerance.
- Store golden screenshots for demo deck.

## 23. Open Questions

These should be decided before major implementation:

1. Should the public DSL use `pages` only, or support `slides` as an alias before v1?
2. Should `chrome` and `master_overrides.chrome` both exist, or should we only expose `chrome` on pages?
3. Should component factories return `Block` directly, or return pure component props that are wrapped by `block.component()`?
4. Should `layout.two_column` be a page layout, a layout algorithm, or a component that arranges children?
5. Should charts use native PowerPoint charts where possible, custom editable shapes, or a mix?
6. Should SVG icons be rasterized for v1 or delayed entirely?
7. Should diagnostics be returned from `parse()` and `render()`, or stored on `Deck`?

## 24. Recommended Decisions

To keep implementation coherent, the recommended decisions are:

1. Use `pages` as the primary top-level field.
2. Use `page.*` for page types.
3. Use `blocks[]` for all content components.
4. Require component-specific data under `props`.
5. Let component namespace factories return `Block`.
6. Let page namespace factories return `Page`.
7. Keep `layout.grid` and `layout.absolute` as MVP layout modes.
8. Support multiple masters and per-page `use_master`.
9. Use `chrome` as the public page override field; internally normalize `master_overrides` into effective chrome.
10. Use native PowerPoint charts for pie/donut where useful, but allow custom editable shape charts for line/bar.
11. Rasterize SVG icons for MVP if icon rendering is implemented.
12. Make diagnostics a first-class parse/render output.

## 25. First Implementation Milestone

The first code milestone should prove the architecture with a small demo:

- One deck.
- One theme.
- Two masters: `tech_blue` and `blank`.
- Three page types: `page.cover`, `page.standard`, `page.section`.
- Two layout modes: `grid`, `absolute`.
- Five components: `basic.text`, `data.metric_cards`, `chart.line`, `table.comparison`, `narrative.timeline`.
- One page with multiple components.
- One page disabling master.
- One page overriding page number/footer.
- Screenshot export still works through the existing export module.

This milestone should replace the conceptual foundation first. More visual components can be added after the page/block/master model is stable.
