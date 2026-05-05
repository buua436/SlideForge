# SlideForge 用户文档

SlideForge 是一个面向 Agent 的 Python PPT UI 组件库。它用结构化 JSON DSL 或 Python namespace API 描述页面、布局和组件，再通过 `python-pptx` 生成可编辑的 `.pptx` 文件。Agent 不需要直接调用 `add_textbox`、`add_shape` 等底层 API，只需要选择组件 type、填写内容数据、选择主题和布局。

当前实现已经迁移到 `Deck -> Page -> Block -> Component` 架构：一页 `Page` 可以包含多个独立 `Block`，每个 `Block` 对应一个可复用组件。页面标题、页脚、页码、母版和公共装饰由 Page/Master 管理，组件只负责在分配到的 `Box` 中渲染自己的内容。

## 目录

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
- [Full Examples](#full-examples)
- [Agent Usage Guide](#agent-usage-guide)
- [Component Extension Guide](#component-extension-guide)
- [FAQ](#faq)
- [Roadmap](#roadmap)

## Introduction

SlideForge 解决的是“让 Agent 生成专业、统一、可编辑 PPT”的问题。直接让 Agent 写 `python-pptx` shape 代码会带来大量重复坐标、样式不一致、组件无法复用、后续改主题困难等问题。SlideForge 把 PPT 生成拆成更接近前端 UI 框架的模型：Agent 输出 JSON，组件库负责解析、布局、主题合并和渲染。

适用场景包括答辩汇报、项目方案、数据报告、商业演示、自动化周报、实验结果汇报、产品方法论和技术方案 deck。生成结果是普通 `.pptx`，文本、形状、表格、图表和图片尽量保持可编辑。

## Architecture

当前渲染链路如下：

```text
JSON DSL / Python API
  -> Component Registry / Parser
  -> Deck / Page / Block Tree
  -> Theme / Master / Layout resolution
  -> PptxRenderer
  -> editable .pptx
```

| 层 | 职责 |
| --- | --- |
| JSON DSL / Python API | 用户或 Agent 的结构化输入，描述页面、组件、props、layout、style。 |
| Component Registry / Parser | 校验页面和组件 type，把 JSON 转成 `Deck`、`Page`、`Block`。 |
| Deck / Page / Block Tree | 内部文档模型。Deck 管整套 PPT，Page 管一页 PPT，Block 是页面内的组件实例。 |
| Theme / Master / Layout | 主题提供默认视觉 token，母版提供标题/页脚/页码等 chrome，布局把 block 映射到 `Box`。 |
| PptxRenderer | 集中调用 `python-pptx`，提供统一的文本、卡片、图表、图标和图片渲染 helper。 |
| editable .pptx | 最终 PowerPoint 文件，可继续手动编辑。 |

## Installation

环境要求：

| 项 | 要求 |
| --- | --- |
| Python | 3.10+，当前测试环境为 3.11 |
| 包管理 | 推荐 `uv` |
| PPTX 渲染 | `python-pptx` |
| 截图导出 | Windows PowerPoint COM + `pywin32`，没有 PowerPoint 时会报 `ScreenshotExportError` |
| 远程 icon | 默认走 Iconify API，需要网络；本地 SVG provider 不需要网络 |

常用命令：

```bash
uv sync
uv run pytest
uv run python examples/demo_deck.py
```

## Quick Start

从 JSON 生成 demo：

```bash
uv run python examples/demo_deck.py
```

默认输出：

```text
examples/demo.pptx
examples/demo_screenshots/
examples/demo_showcase.png
examples/theme_demos/<theme>/demo.pptx
examples/theme_demos/<theme>/screenshots/
examples/theme_demos/<theme>/showcase.png
```

常用参数：

| 参数 | 说明 |
| --- | --- |
| `--output examples/demo.pptx` | 指定主 demo 输出路径。 |
| `--screenshots-dir examples/demo_screenshots` | 指定主 demo 截图目录，每次生成会覆盖。 |
| `--showcase examples/demo_showcase.png` | 指定拼图展示图输出路径。 |
| `--theme-demos-dir examples/theme_demos` | 指定所有内置主题 demo 输出目录。 |
| `--skip-theme-demos` | 只生成主 demo，不生成每个主题的 demo。 |
| `--no-screenshots` | 只生成 PPTX，不导出截图和 showcase。 |

从任意 JSON 文件加载：

```python
from ppt_ui import deck_from_json

deck = deck_from_json("examples/sample_deck.json")
deck.render("examples/demo.pptx")
```

## Directory Structure

| 路径 | 说明 |
| --- | --- |
| `ppt_ui/core/presentation.py` | `Deck`，管理主题、页面、母版、组件注册表和图标注册表。 |
| `ppt_ui/core/page.py` | `Page` 和 `Block`，当前 DSL 的核心数据结构。 |
| `ppt_ui/core/component.py` | `RenderContext` 和组件协议。 |
| `ppt_ui/core/theme.py` | Theme dataclass、ThemeLoader、ThemeRegistry、内置主题注册。 |
| `ppt_ui/core/layout.py` | `Box`、`PageLayout`、内置页面布局和 block box 解析。 |
| `ppt_ui/core/master.py` | `SlideMaster`、`MasterRegistry`、默认母版。 |
| `ppt_ui/core/registry.py` | `ComponentRegistry`，负责 type 到组件 factory 的路由。 |
| `ppt_ui/components/blocks.py` | 当前主要块级组件实现。 |
| `ppt_ui/components/registry.py` | 默认组件注册表。 |
| `ppt_ui/renderer/pptx_renderer.py` | 基于 `python-pptx` 的统一渲染层。 |
| `ppt_ui/schema/parser.py` | JSON 解析、校验和 `Deck` 构建。 |
| `ppt_ui/export/screenshots.py` | PowerPoint COM 截图导出。 |
| `ppt_ui/export/contact_sheet.py` | 多页截图拼图展示图。 |
| `ppt_ui/icons/provider.py` | Iconify、本地 SVG、URL template 等 icon provider。 |
| `ppt_ui/themes/*.json` | 内置主题 JSON。 |
| `examples/demo_deck.py` | demo 生成入口。 |
| `examples/sample_deck.json` | 当前 JSON DSL 样例。 |
| `tests/` | parser、theme、icon 测试。 |

## Core Concepts

### Deck

`Deck` 管理整套演示文稿。

| 属性/方法 | 说明 |
| --- | --- |
| `pages` | `Page` 列表。 |
| `theme` | 已解析的 `Theme` 对象。 |
| `default_master` | 默认母版名，默认 `tech_blue`。 |
| `masters` | `MasterRegistry`。 |
| `components` | `ComponentRegistry`。 |
| `icons` | `IconRegistry`。 |
| `add_page(page)` | 添加页面。 |
| `render(path)` | 生成 PPTX。 |

### Page

`Page` 是一页 PPT。它负责页面级语义和公共元素，不负责具体组件内容。

| 字段 | 说明 |
| --- | --- |
| `type` | 当前支持 `page.cover`、`page.standard`、`page.section`、`page.blank`、`page.closing`、`page.qa`。 |
| `layout` | 布局名或 inline layout spec。 |
| `master` | 当前页使用的母版名。 |
| `use_master` | 是否使用母版。 |
| `chrome` | 页脚、页码、logo、accent bar、section 等页面元素配置。 |
| `title` / `subtitle` | 页面标题区内容。 |
| `blocks` | 页面内组件实例。 |
| `hidden` | 隐藏页不会渲染。 |

### Block

`Block` 是页面内的一个组件实例。

| 字段 | 说明 |
| --- | --- |
| `id` | 可选稳定标识。 |
| `type` | 组件 type，例如 `chart.line`。 |
| `variant` | 组件变体，默认 `default`。主题会用它查找默认样式。 |
| `props` | 组件内容数据。 |
| `layout` | block 在页面内容区的位置。 |
| `style` | 当前 block 的局部样式覆盖。 |
| `visible` | 是否渲染。 |
| `metadata` | 扩展元数据。 |

### Component

组件只负责自己 box 内部的内容渲染。它不应该画页面标题、页脚、页码、logo 或全局背景。当前默认组件都在 `ppt_ui/components/blocks.py` 中实现，并通过 `build_default_component_registry()` 注册。

### RenderContext

`RenderContext` 在组件渲染时传入，包含：

| 字段 | 说明 |
| --- | --- |
| `slide` | 当前 `python-pptx` slide 对象。 |
| `theme` | 当前主题。 |
| `renderer` | `PptxRenderer` helper。 |
| `style` | 主题默认样式和 block style 合并后的结果。 |

### Box

`Box` 使用 inch 作为单位，包含 `x`、`y`、`w`、`h`。常用方法包括 `inset()`、`split_cols()`、`split_rows()`、`top()`、`bottom()`、`remaining_below()`。

### ComponentRegistry

`ComponentRegistry` 避免 parser 出现大量 if/else。当前注册的组件 type 来自 `ppt_ui/components/registry.py`，未知 type 会在 strict 模式下抛出诊断错误。

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

| 字段 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `schema_version` | `string` | 否 | `0.2` | 非 `0.2` 会产生 warning。 |
| `title` | `string` | 否 | `SlideForge Deck` | Deck 标题。 |
| `theme` | `string/object` | 否 | `default_blue` | 内置主题名、外部主题路径、目录主题或 inline theme dict。 |
| `default_master` | `string` | 否 | `tech_blue` | 默认母版名。 |
| `metadata` | `object` | 否 | `{}` | Deck 元数据。 |
| `masters` | `object` | 否 | 默认注册 `default`、`tech_blue`、`blank` | 自定义母版配置。 |
| `pages` | `array` | 是 | 无 | 页面数组。 |

当前 DSL 不读取顶层 `export`、`screenshot`、`page_size`、`language`、`author`、`date`、`version`。这些字段可以放在 `metadata` 中，或由外部脚本处理。

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

| 字段 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `type` | `string` | 否 | `page.standard` | 页面 type。 |
| `layout` | `string/object` | 否 | 从 page type 推导 | 内置布局或 inline layout spec。 |
| `master` | `string` | 否 | `default_master` | 当前页母版。 |
| `use_master` | `boolean` | 否 | `true` | `page.blank` Python helper 默认 `false`。 |
| `master_overrides` | `object` | 否 | `{}` | 页面级母版覆盖。 |
| `chrome` | `object` | 否 | `{}` | 控制标题、页脚、页码、logo、accent bar 等。 |
| `title` | `string` | 否 | `""` | 页标题。 |
| `subtitle` | `string` | 否 | `""` | 页副标题。 |
| `blocks` | `array` | 否 | `[]` | 当前页组件列表。 |
| `notes` | `string` | 否 | `""` | 当前保存在模型中，尚未写入 speaker notes。 |
| `hidden` | `boolean` | 否 | `false` | 隐藏页不渲染。 |
| `metadata` | `object` | 否 | `{}` | 页面元数据，例如 section number。 |

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

| 字段 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `id` | `string` | 否 | `None` | 稳定标识。 |
| `type` | `string` | 是 | 无 | 组件 type。 |
| `variant` | `string` | 否 | `default` | 主题默认样式变体。 |
| `props` | `object` | 否 | `{}` | 组件内容数据。 |
| `layout` | `object` | 否 | 当前内容区绝对 box | block 布局。 |
| `style` | `object` | 否 | `{}` | 局部视觉覆盖，优先级高于主题默认值。 |
| `visible` | `boolean` | 否 | `true` | 是否渲染。 |
| `metadata` | `object` | 否 | `{}` | 扩展数据。 |

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

当前 Python namespace：

| Namespace | 主要方法 |
| --- | --- |
| `page` / `slide` | `cover()`、`standard()`、`section()`、`blank()`、`closing()`、`qa()`。`slide` 是 `page` 的别名。 |
| `layout` | `grid()`、`absolute()`、`grid_item()`、`box()`。 |
| `block` | `component()`，用于自定义 type。 |
| `basic` | `text()`。 |
| `data` | `metric_card()` helper、`metric_cards()`、`progress()`。 |
| `chart` | `line()`、`bar()`、`pie()`、`donut()`。 |
| `table` | `comparison()`。 |
| `narrative` | `timeline()`、`process_flow()`、`roadmap()`。 |
| `media` | `icon()`、`image()`。 |
| `master` | `tech_blue()`、`blank()`。 |
| `theme` | `tech_blue()`、`glassmorphism()`、`claude()`、`glitch_art()`、`paper_cut()`、`neon_cyberpunk()`、`apple()`、`google()`。 |

## Component API

### Implemented Types

| Type | Python API | 说明 |
| --- | --- | --- |
| `basic.text` | `basic.text(...)` | 文本或 bullet 列表。 |
| `data.metric_cards` | `data.metric_cards(...)` | 一组指标卡。 |
| `data.progress` | `data.progress(...)` | 进度条列表。 |
| `chart.line` | `chart.line(...)` | 可编辑 shape 折线图。 |
| `chart.bar` | `chart.bar(...)` | 可编辑 shape 柱状图。 |
| `chart.pie` | `chart.pie(...)` | 原生 PowerPoint 饼图。 |
| `chart.donut` | `chart.donut(...)` | 原生 PowerPoint 环形图。 |
| `table.comparison` | `table.comparison(...)` | 对比表。 |
| `table.basic` | `block.component("table.basic", ...)` | 当前复用对比表组件实现。 |
| `narrative.timeline` | `narrative.timeline(...)` | 状态时间轴。 |
| `narrative.process_flow` | `narrative.process_flow(...)` | 流程步骤卡。 |
| `narrative.roadmap` | `narrative.roadmap(...)` | 路线图条形列表。 |
| `media.icon` | `media.icon(...)` | Iconify、URL、本地 SVG 或 fallback icon 卡。 |
| `media.image` | `media.image(...)` | 图片块。 |

`data.metric_card` 是 Python helper，用于生成 `data.metric_cards.cards[]` 中的单张卡数据；它不是独立 JSON component type。

### Common Component Props

| Type | Props |
| --- | --- |
| `basic.text` | `text`、`bullets`、`size`、`color`、`bold`、`align`、`valign`。 |
| `data.metric_cards` | `cards[]`，每项支持 `label`、`value`、`delta`、`compare`/`note`、`icon`。 |
| `data.progress` | `items[]`，每项支持 `label`、`value`。 |
| `chart.line` / `chart.bar` | `categories[]`、`series[]`，series 项支持 `name`、`values[]`、可选 `color`。 |
| `chart.pie` / `chart.donut` | `labels[]` 或 `categories[]`，`values[]` 或 `data[]`。 |
| `table.comparison` / `table.basic` | `headers[]`、`rows[][]`、`conclusion`。 |
| `narrative.timeline` | `items[]`，每项常用 `title`、`date`、`description`、`status`。 |
| `narrative.process_flow` | `steps[]` 或 `items[]`，每项常用 `title`、`description`、`output`。 |
| `narrative.roadmap` | `items[]`，每项常用 `label`、`value`、`status`。 |
| `media.icon` | `name`、`label`、`source`、`description`、`src`、`color`、`size`、`width`、`height`、`rotate`、`flip`、`stroke_width`/`strokeWidth`、`opacity`。 |
| `media.image` | `src`、`fit`，`fit` 支持 `contain` 或 `cover`。 |

## Theme System

内置主题全部是 JSON 文件，位于 `ppt_ui/themes/`。Python 代码只注册主题名并通过 `ThemeLoader` 加载文件。

当前内置主题：

| Theme | Primary | Accent | Background | Font | 风格 |
| --- | --- | --- | --- | --- | --- |
| `theme.tech_blue` | `#2563EB` | `#7C3AED` | `#FFFFFF` | `Microsoft YaHei` | 默认蓝紫科技风。 |
| `theme.glassmorphism` | `#6366F1` | `#A855F7` | `#E8EEFF` | `Segoe UI` | 玻璃拟态、渐变背景、轻透明卡片。 |
| `theme.claude` | `#B8651B` | `#B8651B` | `#F2ECE2` | `Noto Serif SC` | 暖色纸张、衬线字体、克制线条、方法论表达。 |
| `theme.glitch_art` | `#00FFFF` | `#FF00FF` | `#0A0A0A` | `Consolas` | 深色扫描线、霓虹对比、实验视觉。 |
| `theme.paper_cut` | `#2C3E50` | `#E74C3C` | `#F0F0F0` | `Georgia` | 剪纸层叠、强阴影、插画感。 |
| `theme.neon_cyberpunk` | `#00FF41` | `#00D4FF` | `#0B0E1A` | `Consolas` | 深色网格、霓虹边框、HUD 风格。 |
| `theme.apple` | `#0071E3` | `#FF375F` | `#F5F5F7` | `SF Pro Display` | 极简、浅灰背景、大圆角、弱边框。 |
| `theme.google` | `#1A73E8` | `#EA4335` | `#E8F0FE` | `Google Sans` | Google Material 风格、多色 palette。 |

兼容别名：`default`、`default_blue`、`theme.default_blue`、`tech_blue` 和 `theme.tech_blue` 都会解析到 Tech Blue。

### Theme Sources

| 来源 | 示例 | 状态 |
| --- | --- | --- |
| 内置主题 | `"theme.claude"` | 已实现 |
| 内置别名 | `"default"` | 已实现 |
| 外部单文件 JSON | `"./themes/company_blue.json"` | 已实现 |
| 外部目录主题 | `"./themes/company_modular"` | 已实现，目录下读取 `theme.json` |
| Inline dict | `{ "name": "custom", "extends": "theme.tech_blue" }` | 已实现 |
| 直接 `Theme` 对象 | `Deck(theme=my_theme)` | 已实现 |

### Theme JSON Fields

主题支持扁平字段和分组字段。扁平字段如 `primary`、`font_family`、`page_margin` 会映射到对应 token；也可以写成 `tokens.colors.primary`、`tokens.fonts.family`。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `string` | 主题名。 |
| `extends` | `string/path` | 继承内置主题、外部文件或目录主题。 |
| `metadata` | `object` | `display_name`、`suitable_for`、`visual_features` 等说明性数据。 |
| `slide_width` / `slide_height` | `float` | 页面尺寸，单位 inch。 |
| `tokens` | `object/string/list` | token 片段，可 inline 或引用外部 JSON。 |
| `colors` | `object` | 颜色 token。 |
| `fonts` | `object` | 字体和字号 token。 |
| `spacing` | `object` | 间距 token。 |
| `radius` / `radius_tokens` | `object` | 圆角 token。 |
| `shadow` | `object` | 阴影 token，支持 fallback offset 和 native shadow blur。 |
| `chart_palette` | `list[str]` | 图表色板。 |
| `card_shadow` | `boolean` | 是否启用卡片阴影。 |
| `gradient` | `object` | 背景渐变，支持 `stops[]` 和 `angle`。 |
| `background_pattern` | `string` | 当前 renderer 支持 `scanlines`、`grid`。 |
| `decorations` | `object` | 主题装饰 token，例如 `accent_bar_width`、`footer_line_width`、`footer_line_lengths`、`card_radius`、`card_top_border`。 |
| `components` | `object/string/list` | 组件默认 style，可用于 `component_default_style()`。 |
| `component_styles` | `object/string/list` | 组件样式 token，会转成 `ComponentStyle`。 |

### Token Fields

| Token Group | 字段 |
| --- | --- |
| `ColorTokens` | `background`、`surface`、`surface_alt`、`surface_white`、`primary`、`primary_dark`、`primary_soft`、`primary_tint`、`accent`、`accent_soft`、`accent_tint`、`secondary`、`success`、`success_soft`、`warning`、`warning_soft`、`danger`、`text_primary`、`text_secondary`、`text_tertiary`、`border`、`border_light`、`gray_50`、`gray_100`、`gray_200`、`gray_700`、`shadow_light`、`shadow_card`。 |
| `FontTokens` | `family`、`title_font`、`mono_font`、`latin_font`、`caption_font`、`title_size`、`subtitle_size`、`h1_size`、`h2_size`、`body_size`、`caption_size`、`tiny_size`、`display_size`。 |
| `SpacingTokens` | `base`、`xs`、`sm`、`md`、`lg`、`xl`、`page_margin`、`page_x`、`page_y`、`title_top`、`content_top`、`footer_y`、`gutter`、`card_padding`。 |
| `RadiusTokens` | `sm`、`md`、`lg`。 |
| `ShadowTokens` | `light_offset_x`、`light_offset_y`、`card_offset_x`、`card_offset_y`、`blur_radius`、`distance`、`opacity`、`direction`。 |

### Component Style Priority

渲染时样式合并顺序：

```text
Theme generated defaults
  < theme.components / theme.component_styles
  < block.style
```

组件读取的是 `ctx.style`，因此 Agent 通常只需要提供内容数据，不需要重复写颜色、字号、边框和阴影。

## Layout System

页面布局由 `PageLayout` 定义，block layout 再映射到具体 `Box`。

| 模式 | 示例 | 说明 |
| --- | --- | --- |
| `grid` | `{"mode": "grid", "col": 1, "span": 4, "row": 1, "row_span": 2}` | 相对于页面 `content_box` 的网格布局。 |
| `absolute` | `{"mode": "absolute", "x": 1, "y": 2, "w": 4, "h": 1}` | inch 绝对定位。 |
| `zone` | `{"mode": "zone", "zone": "content"}` | 预留区域模式，当前内置 zones 较少。 |

内置页面布局：`cover`、`section`、`standard`、`blank`、`full_bleed`、`closing`、`qa`。inline layout spec 支持 `{"type": "layout.grid", "columns": 12, "rows": 6, "gap": 0.2}`。

## Masters And Chrome

当前默认母版：`default`、`tech_blue`、`blank`。

母版控制页面 chrome：

| Chrome | 说明 |
| --- | --- |
| `accent_bar` | 左上角强调条，宽度可由主题 `decorations.accent_bar_width` 控制。 |
| `footer` | 页脚文本和轻量线条。 |
| `page_number` | 页码格式，例如 `{current} / {total}`。 |
| `logo` | 文本 logo。 |
| `title` / `subtitle` | 是否显示页面标题区。 |
| `section` | section label。 |

示例：

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

组件不直接调用 `python-pptx`，而是使用 `PptxRenderer` helper。这样可以统一单位、颜色、字体、主题默认值、卡片、图表和 icon 处理。

当前重要 helper：

| Helper | 说明 |
| --- | --- |
| `background(slide)` | 主题背景，支持纯色、渐变和轻量 pattern。 |
| `rect(...)` | 矩形/圆角矩形，支持透明度、线宽、虚线。 |
| `line(...)` | 连接线、坐标轴、图表辅助线。 |
| `circle(...)` | 圆形节点和占位符，支持透明度。 |
| `text(...)` | 文本框，支持字体、对齐、垂直对齐、line spacing。 |
| `bullet_list(...)` | bullet 列表。 |
| `picture(...)` | 图片渲染，支持 `contain` / `cover`。 |
| `icon_picture(...)` | SVG icon 转透明 PNG 后插入 PPT。 |
| `add_card(...)` | 统一卡片，支持 fallback shadow 和 native shadow。 |
| `add_metric_card(...)` | 指标卡。 |
| `add_status_timeline_node(...)` | 状态时间轴节点。 |
| `add_process_step_card(...)` | 流程步骤卡。 |
| `add_table(...)` | 表格。 |

## Export Screenshots

```python
from ppt_ui.export import export_pptx_screenshots

export_pptx_screenshots("examples/demo.pptx", "examples/demo_screenshots")
```

行为：

| 项 | 说明 |
| --- | --- |
| 覆盖输出 | 每次导出会覆盖整个截图目录。 |
| 命名 | 输出 `slide_01.png`、`slide_02.png` 等。 |
| 依赖 | Windows PowerPoint COM。没有 PowerPoint 或 COM 不可用时会抛出 `ScreenshotExportError`。 |
| showcase | `build_demo_showcase()` 可以把截图拼成一张展示图。 |

## Icons

`media.icon` 默认使用 Iconify API，支持前端式点号写法和 Iconify 冒号写法：

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

常用 alias：`lucide`、`heroicons`、`remix`/`ri`、`tabler`、`ph`、`mdi`、`material`、`fa`、`bootstrap`/`bi`、`carbon`、`fluent`、`radix`、`octicon`、`simple-icons`、`solar`、`mingcute`、`hugeicons`、`iconamoon`。

扩展本地 SVG：

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

单文件主题：

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

目录主题：

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

Agent 推荐流程：

1. 分析用户目标和内容类型。
2. 拆分页面结构，选择 `page.cover`、`page.standard`、`page.section`、`page.qa` 等页面。
3. 为每页选择多个 block，例如 `data.metric_cards`、`chart.line`、`table.comparison`。
4. 使用 `layout.grid` 或 block `layout.mode=grid` 分配区域。
5. 只填写内容 props，避免反复写颜色和字号。
6. 选择主题，例如 `theme.claude` 或 `theme.tech_blue`。
7. 交给 `deck_from_json()` 和 `Deck.render()` 生成 PPTX。

常见错误：

| 错误 | 结果 |
| --- | --- |
| `type` 不存在 | strict parser 抛出 `UNKNOWN_COMPONENT_TYPE`。 |
| `pages` 缺失 | parser 抛出 `MISSING_PAGES`。 |
| `chart.line.series[].values` 长度和 `categories` 不一致 | 产生 warning，仍保存在 `deck.diagnostics`。 |
| `table.rows[]` 长度和 `headers` 不一致 | 产生 warning。 |
| 内容过长 | 可能触发 PowerPoint 自动缩放或视觉溢出，需要减少文本或拆页。 |

## Component Extension Guide

新增 `chart.scatter` 的典型步骤：

1. 在 `ppt_ui/components/blocks.py` 新增组件类，提供 `from_props()` 和 `render(ctx, box)`。
2. 在 `ppt_ui/components/registry.py` 注册 `registry.register("chart.scatter", ScatterChartComponent.from_props)`。
3. 如需校验，在 `ppt_ui/schema/parser.py` 增加 props 校验。
4. 在主题 JSON 的 `components` 或 `component_styles` 中加入 `chart.scatter.default`。
5. 在 `ppt_ui/api.py` 的 `ChartNamespace` 增加 Python helper。
6. 在 `examples/sample_deck.json` 增加示例。
7. 在 `tests/` 增加 parser 或渲染相关测试。
8. 更新本文档的组件表和 props 表。

## FAQ

### 生成的 PPT 可以编辑吗？

可以。文本、shape、表格、原生图表和图片都写入普通 `.pptx`。部分复杂 icon 会先转成透明 PNG，因此 icon 图片本身不是矢量 shape。

### 为什么不用 Agent 直接写 python-pptx？

直接写底层 shape 会让样式、坐标和布局逻辑散落在每个 Agent 输出中。SlideForge 让 Agent 输出 DSL，组件库统一处理主题、布局和可复用组件。

### 中文字体显示异常怎么办？

主题中的 `font_family`、`title_font_family` 等需要使用本机已安装字体。跨平台 deck 建议选择常见字体或在使用环境中安装对应字体。

### 如何关闭截图导出？

运行 `uv run python examples/demo_deck.py --no-screenshots`。

### 如何只生成主 demo？

运行 `uv run python examples/demo_deck.py --skip-theme-demos`。

### PowerPoint COM 截图导出依赖什么？

依赖 Windows、已安装 PowerPoint 和可用的 COM 自动化环境。没有这些依赖时 PPTX 仍可生成，只是截图导出失败。

## Roadmap

- 更多 chart：scatter、area、radar、waterfall。
- 更完整 layout engine：Row、Column、Spacer、Padding、Alignment。
- 自动文本缩放和溢出诊断。
- 更强 JSON Schema 校验。
- 更多主题包和主题市场。
- SVG/icon 的更多本地缓存和离线能力。
- Agent prompt templates。
- Web preview。
