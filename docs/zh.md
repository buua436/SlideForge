# SlideForge 用户文档

> Pre-v1 status: 当前代码正在按 [docs/design.md](design.md) 迁移到 `Page + Blocks + Master` 架构。本文档的部分旧 `slide.*` / 单组件成页 API 说明已不是最新实现；当前请以 `docs/design.md`、`examples/sample_deck.json` 和测试为准，稳定后会重新生成正式用户文档。

SlideForge 是一个面向 Agent 的 Python PPT UI 组件库。它用结构化 JSON DSL 或 Python namespace API 描述演示文稿，再通过组件注册中心、解析器和 `python-pptx` 渲染为可编辑的 `.pptx` 文件。用户和 Agent 不需要直接调用 `add_textbox`、`add_shape` 等底层 API，而是选择类似前端 UI 框架的组件：`slide.title`、`data.metric_cards`、`chart.line`、`narrative.timeline` 等。

当前文档基于项目代码扫描整理。标记为“已实现”的 API 已在当前代码中存在；标记为“计划支持”的能力代表架构预留或路线图方向，不应在当前版本中直接使用。

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
- [Renderer](#renderer)
- [Export Screenshots](#export-screenshots)
- [Full Examples](#full-examples)
- [Agent Usage Guide](#agent-usage-guide)
- [Component Extension Guide](#component-extension-guide)
- [FAQ](#faq)
- [Roadmap](#roadmap)

## Introduction

SlideForge 解决的问题是：让 Agent 能稳定生成专业、统一、可编辑的 PPT，而不是直接拼接大量 `python-pptx` shape 代码。它把 PPT 页面抽象成组件树，组件负责布局、主题、字号、卡片、表格、图表和叙事结构，Agent 只需要生成语义化 JSON。

与直接使用 `python-pptx` 的区别：

| 方式 | 关注点 | 结果 |
| --- | --- | --- |
| 直接使用 `python-pptx` | 坐标、shape、textbox、颜色、字号 | 灵活但重复、难维护，Agent 容易生成不一致页面 |
| 使用 SlideForge | 组件类型、内容字段、主题 token、布局区域 | 统一风格、组件复用、输出可编辑 `.pptx` |

适用场景包括答辩汇报、项目方案、数据报告、商业演示、自动化周报、实验结果汇报、运营分析、项目复盘和 Agent 自动生成报告。

## Architecture

SlideForge 当前采用三层到四层的渲染链路：

```text
JSON DSL
  -> Component Registry / Parser
  -> Deck / Slide / Component Tree
  -> PptxRenderer
  -> editable .pptx
```

| 层级 | 职责 | 当前实现 |
| --- | --- | --- |
| JSON DSL | Agent 或用户输入的结构化页面描述。 | `examples/sample_deck.json`、`ppt_ui/schema/deck_schema.py` |
| Component Registry / Parser | 根据 `type` 路由到组件工厂，避免 parser 变成大量 if/else。 | `ppt_ui/core/registry.py`、`ppt_ui/schema/parser.py` |
| Deck / Slide / Component Tree | 内部演示文稿对象，包含主题和 slide 组件。 | `Deck`、`Slide`、`Component` |
| PptxRenderer | 统一封装 `python-pptx`，组件通过 renderer helper 绘制。 | `ppt_ui/renderer/pptx_renderer.py` |
| editable `.pptx` | 最终输出文件，保留 PowerPoint 可编辑对象。 | `Deck.render(path)` |

组件不应该直接暴露 `python-pptx` 细节给 Agent。Agent 的稳定接口是 JSON DSL；Python 用户可以使用 namespace API 组装 deck。

## Installation

### 环境要求

| 项目 | 要求 |
| --- | --- |
| Python | `>=3.10` |
| 包管理 | 推荐 `uv` |
| PPTX 生成 | `python-pptx>=1.0.2` |
| 截图导出 | Windows + Microsoft PowerPoint + `pywin32` |

### 安装依赖

```bash
uv sync --dev
```

如果只需要生成 `.pptx`，核心依赖是 `python-pptx`。如果需要把每页导出为 PNG 截图，Windows 上还需要 `pywin32` 和本机 PowerPoint。

## Quick Start

生成 demo deck：

```bash
uv run python examples/demo_deck.py
```

默认输出：

| 输出 | 路径 |
| --- | --- |
| PPTX | `examples/demo.pptx` |
| 截图目录 | `examples/demo_screenshots/` |
| 合成展示图 | `examples/demo_showcase.png` |
| 各主题 demo 目录 | `examples/theme_demos/<theme_name>/` |

每个主题目录包含：

| 输出 | 路径 |
| --- | --- |
| PPTX | `examples/theme_demos/<theme_name>/demo.pptx` |
| 截图目录 | `examples/theme_demos/<theme_name>/screenshots/` |
| 合成展示图 | `examples/theme_demos/<theme_name>/showcase.png` |

指定输出路径：

```bash
uv run python examples/demo_deck.py --output examples/custom_demo.pptx
```

指定截图目录：

```bash
uv run python examples/demo_deck.py --screenshots-dir examples/custom_screenshots
```

禁用截图导出：

```bash
uv run python examples/demo_deck.py --no-screenshots
```

跳过各主题 demo 目录：

```bash
uv run python examples/demo_deck.py --skip-theme-demos
```

从自定义 JSON 生成 PPTX：

```python
from ppt_ui.schema.parser import deck_from_json

deck = deck_from_json("examples/sample_deck.json")
deck.render("examples/demo.pptx")
```

当前 `examples/demo_deck.py` 固定读取 `examples/sample_deck.json`。命令行 `--source` 参数属于计划支持。

## Directory Structure

| 路径 | 文件职责 | 主要类/函数 | 关系 |
| --- | --- | --- | --- |
| `ppt_ui/core/presentation.py` | Deck 管理。 | `Deck.add_slide()`、`Deck.render()` | 调用 `PptxRenderer` 输出 PPTX |
| `ppt_ui/core/slide.py` | Slide 基类。 | `Slide.render(ctx, box)` | 所有页面级组件继承它 |
| `ppt_ui/core/component.py` | Component 基类和渲染上下文。 | `Component`、`RenderContext` | 块级组件和 slide 共享生命周期 |
| `ppt_ui/core/theme.py` | 主题 token 与主题加载。 | `Theme`、`ThemeLoader`、`ThemeRegistry`、`ColorTokens`、`FontTokens`、`get_theme()` | 被 renderer 和组件读取 |
| `ppt_ui/themes/` | 内置 JSON 主题定义。 | `*.json` 主题文件 | 由 `ThemeLoader` 通过主题 registry 加载 |
| `ppt_ui/core/layout.py` | 布局区域计算。 | `Box`、`PageBox` | 组件用 inch 坐标拆分内容区域 |
| `ppt_ui/core/registry.py` | 组件注册中心。 | `ComponentRegistry` | parser 根据 type 创建 slide |
| `ppt_ui/components/basic.py` | 基础块组件。 | `Title`、`TextBlock`、`Divider`、`Icon` | 目前主要作为内部基础组件和占位能力 |
| `ppt_ui/components/slides.py` | 页面与布局类组件。 | `TitleSlide`、`SectionSlide`、`GridSlide` 等 | 对应 `slide.*` 和 `layout.*` |
| `ppt_ui/components/data.py` | 数据和图表组件。 | `MetricCard`、`LineChartSlide`、`ComparisonTableSlide` 等 | 对应 `data.*`、`chart.*`、`table.*` |
| `ppt_ui/components/narrative.py` | 叙事和分析组件。 | `TimelineSlide`、`ProcessFlowSlide`、`SWOTSlide` 等 | 对应 `narrative.*` |
| `ppt_ui/renderer/pptx_renderer.py` | PPTX 渲染层。 | `PptxRenderer` 与 helper 方法 | 统一封装 `python-pptx` |
| `ppt_ui/schema/deck_schema.py` | JSON TypedDict。 | `DeckDict`、`SlideDict` | 当前是轻量类型提示，不是完整校验器 |
| `ppt_ui/schema/parser.py` | JSON 到 Deck/Slide 的解析。 | `deck_from_json()`、`deck_from_dict()`、`build_default_registry()` | 注册 namespace type 和兼容旧 type |
| `ppt_ui/export/screenshots.py` | PPTX 截图导出。 | `export_pptx_screenshots()` | 使用 PowerPoint COM，运行时覆盖输出目录 |
| `ppt_ui/icons/provider.py` | 前端图标库适配层。 | `IconRegistry`、`IconifyApiProvider`、`IconifyJsonProvider`、`LocalSvgIconProvider` | 解析 Iconify 兼容 SVG 并支持渲染进 PPT |
| `ppt_ui/api.py` | 对外 namespace API。 | `chart`、`data`、`layout`、`narrative`、`slide`、`table` | Python 用户推荐入口 |
| `examples/demo_deck.py` | 示例生成脚本。 | `main()` | 读取 sample JSON，生成 PPTX 和截图 |
| `examples/sample_deck.json` | Agent JSON DSL 样例。 | namespace `type` | demo 数据源 |
| `tests/` | 测试。 | `test_parser.py` | 覆盖 parser、registry、namespace API |

## Core Concepts

### Deck

`Deck` 管理整套演示文稿，包含主题、标题和 slides。调用 `Deck.render(path)` 会创建 `PptxRenderer`，逐页渲染并保存 `.pptx`。

| 属性/方法 | 类型 | 说明 |
| --- | --- | --- |
| `slides` | `list[Slide]` | 页面组件列表 |
| `theme` | `Theme` | 当前主题 |
| `title` | `str` | Deck 标题 |
| `add_slide(slide)` | method | 添加一页 |
| `render(output_path)` | method | 生成 PPTX 并返回路径 |

```python
from ppt_ui import Deck, slide

deck = Deck(title="Quarterly Review")
deck.add_slide(slide.title(title="Quarterly Review", subtitle="Generated by SlideForge"))
deck.render("examples/review.pptx")
```

注意事项：`Deck.render()` 只生成 PPTX，不负责截图。截图由 `ppt_ui.export.export_pptx_screenshots()` 或 `examples/demo_deck.py` 控制。

### Slide

`Slide` 是页面级组件基类。每个 slide 实现：

```python
def render(self, ctx: RenderContext, box: PageBox) -> None:
    ...
```

生命周期：

1. `Deck.render()` 创建 `PptxRenderer`。
2. `PptxRenderer.render_deck()` 创建空白 PowerPoint slide。
3. renderer 创建 `RenderContext(slide, theme, renderer)`。
4. slide 组件在 `PageBox` 区域内绘制内容。

新增 slide 时，继承 `Slide`、定义 dataclass 字段、实现 `render()`，再注册到 `ComponentRegistry`。

### Component

`Component` 是块级组件基类，可被多个 slide wrapper 复用。例如 `MetricCard` 是块级组件，`MetricCardsSlide` 负责把多个 `MetricCard` 排成一页。

```python
@dataclass
class Component:
    def render(self, ctx: RenderContext, box: Box) -> None:
        raise NotImplementedError
```

### RenderContext

| 字段 | 说明 |
| --- | --- |
| `slide` | 当前 `python-pptx` slide 对象 |
| `theme` | 当前 `Theme` |
| `renderer` | 当前 `PptxRenderer` |

组件应通过 `ctx.renderer` 绘制，而不是在业务组件中散落 `python-pptx` 细节。

### Box

`Box` 是布局区域对象，单位是 inch。

| 方法 | 说明 |
| --- | --- |
| `inset(left, top, right=None, bottom=None)` | 生成内边距后的区域 |
| `split_cols(count, gutter=0.0)` | 按列拆分区域 |
| `split_rows(count, gutter=0.0)` | 按行拆分区域 |
| `top(height)` | 获取顶部区域 |
| `bottom(height)` | 获取底部区域 |
| `remaining_below(top_height, gap=0.0)` | 获取顶部区域下方剩余空间 |

### Theme

`Theme` 是设计 token 容器，包含颜色、字体、间距、圆角、阴影、图表色板和组件级 style。默认内置主题是 `theme.tech_blue`。

### ComponentRegistry

`ComponentRegistry` 负责把 `type` 路由到组件工厂。它支持两种形式：

```json
{"type": "chart.line"}
```

也支持 family + variant：

```json
{"type": "chart", "variant": "line"}
```

当前默认 registry 同时保留旧 type 兼容，例如 `title_slide`、`metric_cards`、`comparison_table`。

## JSON DSL Guide

### 顶层结构

当前已实现的顶层字段只有 `title`、`theme`、`slides`。其余字段属于计划支持或由外部脚本处理。

```json
{
  "title": "SlideForge Demo",
  "theme": "default_blue",
  "slides": [
    {
      "type": "slide.title",
      "title": "可复用 PPT UI 组件库",
      "subtitle": "适用于答辩汇报 / 项目方案 / 数据报告 / 商业演示"
    }
  ]
}
```

| 字段 | 类型 | 是否必填 | 默认值 | 当前状态 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `title` | `string` | 否 | `"SlideForge Deck"` | 已实现 | Deck 标题 |
| `theme` | `string/object` | 否 | `default_blue` | 已实现 | 内置主题名、外部 JSON 文件、外部主题目录或 inline theme object |
| `slides` | `array<object>` | 否 | `[]` | 已实现 | 页面列表 |
| `metadata` | `object` | 否 | 无 | 计划支持 | 当前 parser 忽略 |
| `export` | `object` | 否 | 无 | 计划支持 | 当前由 demo 脚本参数控制 |
| `screenshot` | `object` | 否 | 无 | 计划支持 | 当前由 `--screenshots-dir` 和 `--no-screenshots` 控制 |
| `page_size` | `object/string` | 否 | 主题尺寸 | 计划支持 | 当前由 `Theme.slide_width/slide_height` 控制 |
| `language` | `string` | 否 | 无 | 计划支持 | 当前 parser 忽略 |
| `author` | `string` | 否 | 无 | 计划支持 | 当前 parser 忽略 |
| `date` | `string` | 否 | 无 | 计划支持 | 当前 parser 忽略，封面页可使用 `slide.title.date` |
| `version` | `string` | 否 | 无 | 计划支持 | 当前 parser 忽略 |

### Slide 通用字段

不同组件支持的字段不同。当前 parser 直接把字段映射到组件 dataclass，未实现统一的 `props/style/layout` 合并机制。

| 字段 | 类型 | 当前状态 | 说明 |
| --- | --- | --- | --- |
| `type` | `string` | 已实现 | 必须能在 registry 中找到，例如 `chart.line` |
| `variant` | `string` | 已实现 | 可选；用于 `type + variant` 路由，例如 `{"type": "chart", "variant": "line"}` |
| `title` | `string` | 多数组件已实现 | 页面主标题 |
| `subtitle` | `string` | 多数组件已实现 | 页面副标题 |
| `content` | `string/object` | 计划支持 | 当前无统一处理 |
| `items` | `array` | 部分组件已实现 | `layout.contents`、`layout.grid`、`data.progress_bars`、`narrative.timeline` 等使用 |
| `blocks` | `array` | 计划支持 | 当前无通用块级组件树 parser |
| `cards` | `array` | 部分组件已实现 | `data.metric_cards`、`layout.three_info_cards` |
| `data` | `object` | 计划支持 | 当前图表直接使用 `categories/series/segments` 等字段 |
| `style` | `object` | 计划支持 | 当前没有 per-slide style override |
| `layout` | `object` | 计划支持 | 当前没有 per-slide layout override |
| `footer` | `string/object` | 计划支持 | 当前多数 slide 内部调用 `add_footer()` |
| `notes` | `string` | 计划支持 | 当前不写 speaker notes |
| `metadata` | `object` | 计划支持 | 当前 parser 忽略 |
| `hidden` | `boolean` | 计划支持 | 当前不会跳过 slide |
| `page_number` | `string/number` | 计划支持 | 当前仅 `layout.header_footer.page` 可显示页码文本 |

### Namespace Type 规范

推荐 Agent 始终使用 namespace type。

| Namespace | 已实现 | 计划支持 |
| --- | --- | --- |
| `slide` | `slide.title`、`slide.section`、`slide.conclusion`、`slide.qa` | `slide.content` |
| `layout` | `layout.contents`、`layout.two_column`、`layout.grid`、`layout.image_text`、`layout.three_info_cards`、`layout.quote`、`layout.header_footer`、`layout.design_spec` | `layout.cards`、`layout.blank` |
| `data` | `data.metric_card`、`data.metric_cards`、`data.progress_bars`、`data.gantt`、`data.heatmap`、`data.ab_comparison`、`data.highlight_insight`、`data.annotations` | `data.progress` alias |
| `chart` | `chart.line`、`chart.bar`、`chart.pie`、`chart.donut` | `chart.scatter`、`chart.area`、更多图表 |
| `table` | `table.comparison` | `table.basic` |
| `narrative` | `narrative.timeline`、`narrative.process_flow`、`narrative.roadmap`、`narrative.swot`、`narrative.problem_solution`、`narrative.logic_pyramid`、`narrative.risk_table`、`narrative.milestone`、`narrative.relation_table`、`narrative.story_structure` | 更多分析模板 |
| `media` | `media.icon` | `media.image` 增强 |
| `theme` | `theme.tech_blue`、`theme.academic_clean`、`theme.business_navy`、`theme.data_dashboard`、`theme.medical_teal`、`theme.dark_tech`、`theme.claude_warm` | 更多外部主题包 |

## Python API Guide

推荐从 `ppt_ui` 包导入 namespace API：

```python
from ppt_ui import Deck, chart, data, layout, narrative, slide, table

deck = Deck(title="SlideForge Demo")
deck.add_slide(slide.title(title="可复用 PPT UI 组件库", subtitle="Agent-driven PPT UI Framework"))
deck.add_slide(
    data.metric_cards(
        title="核心指标概览",
        cards=[
            data.metric_card(label="准确率", value="92.3%", delta="+3.1%", note="较上期", icon="AC"),
            data.metric_card(label="AUC", value="0.948", delta="+0.026", note="验证集", icon="AU"),
        ],
    )
)
deck.add_slide(
    chart.line(
        title="趋势分析",
        categories=["4/29", "5/6", "5/13"],
        series=[{"name": "指标 A", "values": [320, 540, 580]}],
    )
)
deck.render("examples/api_demo.pptx")
```

JSON 用户入口：

```python
from ppt_ui.schema.parser import deck_from_json

deck = deck_from_json("examples/sample_deck.json")
deck.render("examples/demo.pptx")
```

## Component API

### 组件状态总览

| Type | Python API | 状态 |
| --- | --- | --- |
| `slide.title` | `slide.title(...)` | 已实现 |
| `slide.section` | `slide.section(...)` | 已实现 |
| `slide.content` | 无 | 计划支持 |
| `slide.conclusion` | `slide.conclusion(...)` | 已实现 |
| `slide.qa` | `slide.qa(...)` | 已实现 |
| `layout.two_column` | `layout.two_column(...)` | 已实现 |
| `layout.grid` | `layout.grid(...)` | 已实现 |
| `layout.cards` | 无 | 计划支持 |
| `layout.blank` | 无 | 计划支持 |
| `data.metric_card` | `data.metric_card(...)` | 已实现，JSON 中会包装成单卡 slide |
| `data.metric_cards` | `data.metric_cards(...)` | 已实现 |
| `data.progress` | 无 | 计划支持 |
| `data.progress_bars` | `data.progress_bars(...)` | 已实现 |
| `data.gantt` | `data.gantt(...)` | 已实现 |
| `chart.line` | `chart.line(...)` | 已实现 |
| `chart.bar` | `chart.bar(...)` | 已实现 |
| `chart.pie` | `chart.pie(...)` | 已实现 |
| `chart.donut` | `chart.donut(...)` | 已实现 |
| `table.basic` | 无 | 计划支持 |
| `table.comparison` | `table.comparison(...)` | 已实现 |
| `narrative.timeline` | `narrative.timeline(...)` | 已实现 |
| `narrative.process_flow` | `narrative.process_flow(...)` | 已实现 |
| `narrative.roadmap` | `narrative.roadmap(...)` | 已实现 |
| `narrative.swot` | `narrative.swot(...)` | 已实现 |
| `narrative.problem_solution` | `narrative.problem_solution(...)` | 已实现 |
| `narrative.logic_pyramid` | `narrative.logic_pyramid(...)` | 已实现 |
| `media.image` | 本地图片路径组件 | 已实现 |
| `media.icon` | 远程 Iconify 兼容图标组件 | 已实现 |

### slide.title

功能：生成封面页。适用于报告封面、项目开场、答辩首页。

```python
deck.add_slide(slide.title(title="可复用 PPT UI 组件库", subtitle="适用于数据报告", presenter="SlideForge", date="2026.05.03"))
```

```json
{"type": "slide.title", "title": "可复用 PPT UI 组件库", "subtitle": "适用于数据报告", "presenter": "SlideForge", "date": "2026.05.03", "logo": "YOUR LOGO"}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `type` | `string` | JSON 必填 | 无 | `slide.title` |
| `title` | `string` | 是 | `""` | 主标题 |
| `subtitle` | `string` | 否 | `""` | 副标题 |
| `presenter` | `string` | 否 | `""` | 展示者 |
| `date` | `string` | 否 | `""` | 日期文本 |
| `logo` | `string` | 否 | `"YOUR LOGO"` | 左上角标识文本 |

默认样式：白色背景、左侧蓝紫强调条、大标题、右侧轻量几何装饰、轻页脚。注意标题过长可能压缩显示。

### slide.section

功能：章节过渡页。适用于 deck 中的大章节分割。

```python
deck.add_slide(slide.section(number="01", title="基础布局组件", subtitle="快速搭建页面结构", keywords=["标题页", "双栏", "网格"]))
```

```json
{"type": "slide.section", "number": "01", "title": "基础布局组件", "subtitle": "快速搭建页面结构", "keywords": ["标题页", "双栏", "网格"]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `type` | `string` | JSON 必填 | 无 | `slide.section` |
| `number` | `string` | 否 | `"01"` | 章节编号 |
| `title` | `string` | 是 | `""` | 章节标题 |
| `subtitle` | `string` | 否 | `""` | 章节说明 |
| `keywords` | `array<string>` | 否 | `[]` | 关键词标签 |

默认样式：大编号、章节标题、关键词 pill、轻量进度装饰。建议关键词 3-6 个。

### slide.conclusion

功能：结论与展望页。适用于总结页、项目收束页。

```python
deck.add_slide(slide.conclusion(points=[{"title": "组件复用", "description": "降低重复排版成本"}], closing="携手共进，共创未来！"))
```

```json
{"type": "slide.conclusion", "title": "结论与展望", "points": [{"title": "组件复用", "description": "降低重复排版成本"}], "closing": "携手共进，共创未来！"}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `type` | `string` | JSON 必填 | 无 | `slide.conclusion` |
| `title` | `string` | 否 | `"结论与展望"` | 页面标题 |
| `points` | `array<object>` | 否 | `[]` | 结论卡片 |
| `points[].title` | `string` | 是 | 无 | 卡片标题 |
| `points[].description` | `string` | 是 | 无 | 卡片说明 |
| `closing` | `string` | 否 | 内置文案 | 结束语 |

默认样式：主渐变容器、三列结论卡、强调 closing。建议 `points` 2-3 个。

### slide.qa

功能：Q&A 结束页。适用于答疑、收尾页。

```python
deck.add_slide(slide.qa(project="SlideForge", description="欢迎交流组件设计、主题扩展与 Agent 生成链路"))
```

```json
{"type": "slide.qa", "title": "Q&A", "subtitle": "感谢聆听，期待交流", "project": "SlideForge", "description": "欢迎交流组件设计、主题扩展与 Agent 生成链路"}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `type` | `string` | JSON 必填 | 无 | `slide.qa` |
| `title` | `string` | 否 | `"Q&A"` | 主视觉文字 |
| `subtitle` | `string` | 否 | 内置文案 | 副标题 |
| `project` | `string` | 否 | `"SlideForge"` | 项目名 |
| `description` | `string` | 否 | 内置文案 | 说明文字 |

默认样式：居中大号 Q&A、项目名、说明卡片、轻装饰。建议保持简短。

### layout.contents

功能：目录页。适用于 deck 目录或章节导航。

```python
deck.add_slide(layout.contents(items=[{"number": "01", "title": "基础布局组件"}]))
```

```json
{"type": "layout.contents", "title": "目录", "subtitle": "CONTENTS", "items": [{"number": "01", "title": "基础布局组件"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | `string` | 否 | `"目录"` | 页面标题 |
| `subtitle` | `string` | 否 | `"CONTENTS"` | 副标题 |
| `items` | `array<object>` | 是 | `[]` | 目录项 |
| `items[].number` | `string` | 是 | 无 | 编号 |
| `items[].title` | `string` | 是 | 无 | 目录标题 |

默认样式：居中卡片列表、编号标签。建议 3-6 项。

### layout.two_column

功能：双栏内容页。适用于对比解释、左右结构说明。

```python
deck.add_slide(layout.two_column(title="双栏说明", left_title="为什么需要", left_items=["语义化输入"], right_title="第一阶段能力", right_items=["JSON 到 PPTX"]))
```

```json
{"type": "layout.two_column", "title": "双栏说明", "left_title": "为什么需要", "left_items": ["语义化输入"], "right_title": "第一阶段能力", "right_items": ["JSON 到 PPTX"]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | `string` | 是 | `""` | 页面标题 |
| `left_title` | `string` | 是 | `""` | 左栏标题 |
| `left_items` | `array<string>` | 是 | `[]` | 左栏要点 |
| `right_title` | `string` | 是 | `""` | 右栏标题 |
| `right_items` | `array<string>` | 是 | `[]` | 右栏要点 |

默认样式：两张轻量卡片、编号标签、bullet 列表。建议每栏 3-5 点。

### layout.grid

功能：网格化信息卡。适用于能力矩阵、模块列表、规则说明。

```python
deck.add_slide(layout.grid(title="网格布局", columns=3, items=[{"title": "Title", "description": "统一标题区", "icon": "T"}]))
```

```json
{"type": "layout.grid", "title": "网格布局", "columns": 3, "items": [{"title": "Title", "description": "统一标题区", "icon": "T"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | `string` | 是 | `""` | 页面标题 |
| `subtitle` | `string` | 否 | 内置文案 | 副标题 |
| `columns` | `integer` | 否 | `3` | 列数 |
| `items` | `array<object>` | 是 | `[]` | 网格项 |
| `items[].title` | `string` | 是 | 无 | 卡片标题 |
| `items[].description` | `string` | 否 | `""` | 卡片说明 |
| `items[].icon` | `string` | 否 | `""` | 文本图标占位 |

默认样式：浅色卡片、圆形 icon 占位。注意 `columns` 过大时内容会拥挤。

### layout.image_text

功能：图文混排页。当前是视觉占位，不会加载真实图片。适用于说明型页面。

```python
deck.add_slide(layout.image_text(title="图文混排", image_label="Visual", body="核心观点", bullets=["左文右图"], image_side="right"))
```

```json
{"type": "layout.image_text", "title": "图文混排", "image_label": "Visual", "body": "核心观点", "bullets": ["左文右图"], "image_side": "right"}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | `string` | 是 | `""` | 页面标题 |
| `subtitle` | `string` | 否 | 内置文案 | 副标题 |
| `image_label` | `string` | 否 | `"Image"` | 图片占位文本 |
| `body` | `string` | 否 | `""` | 正文 |
| `bullets` | `array<string>` | 否 | `[]` | 要点 |
| `image_side` | `string` | 否 | `"right"` | `left` 或 `right` |

默认样式：一侧卡片模拟图片容器，一侧正文卡。真实图片插入属于 `media.image` 计划支持。

### layout.three_info_cards

功能：三栏信息卡。适用于三类能力、价值、模块说明。

```python
deck.add_slide(layout.three_info_cards(title="三栏信息卡", cards=[{"title": "产品能力", "description": "提升效率", "icon": "P"}]))
```

```json
{"type": "layout.three_info_cards", "title": "三栏信息卡", "cards": [{"title": "产品能力", "description": "提升效率", "icon": "P"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | `string` | 是 | `""` | 页面标题 |
| `subtitle` | `string` | 否 | 内置文案 | 副标题 |
| `cards` | `array<object>` | 是 | `[]` | 卡片列表 |
| `cards[].title` | `string` | 是 | 无 | 卡片标题 |
| `cards[].description` | `string` | 是 | 无 | 卡片说明 |
| `cards[].icon` | `string` | 否 | `""` | 图标占位文本 |

默认样式：三列浅色卡、圆形 icon 占位。建议 3 张卡。

### layout.quote

功能：引用说明块。适用于观点强调、章节过渡、专家引用。

```python
deck.add_slide(layout.quote(title="引用说明块", quote="技术的价值在于让业务更简单。", source="SlideForge"))
```

```json
{"type": "layout.quote", "title": "引用说明块", "quote": "技术的价值在于让业务更简单。", "source": "SlideForge"}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | `string` | 是 | `""` | 页面标题 |
| `subtitle` | `string` | 否 | 内置文案 | 副标题 |
| `quote` | `string` | 是 | `""` | 引用正文 |
| `source` | `string` | 否 | `""` | 来源 |

默认样式：居中引用卡、强调引号。建议引用不超过两行。

### layout.header_footer

功能：页眉页脚占位规范页。适用于展示模板规则或占位页面。

```python
deck.add_slide(layout.header_footer(title="页眉页脚", section="02", body="页面内容区域", page="/ 12"))
```

```json
{"type": "layout.header_footer", "title": "页眉页脚", "section": "02", "body": "页面内容区域", "source": "数据来源：内部数据", "page": "/ 12"}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | `string` | 是 | `""` | 页面标题 |
| `section` | `string` | 否 | `"01"` | 右上角章节标签 |
| `body` | `string` | 否 | 内置文案 | 内容区占位 |
| `source` | `string` | 否 | 内置文案 | 来源文本 |
| `page` | `string` | 否 | `"/ 12"` | 页码文本 |
| `subtitle` | `string` | 否 | 内置文案 | 副标题 |

默认样式：标题区、内容框、来源和页码。当前不是自动页码。

### layout.design_spec

功能：设计规范展示页。适用于展示 token、组件规范、设计系统规则。

```python
deck.add_slide(layout.design_spec(specs=["标题", "正文", "强调色", "留白", "圆角", "阴影"]))
```

```json
{"type": "layout.design_spec", "title": "设计规范", "specs": ["标题", "正文", "强调色", "留白", "圆角", "阴影"]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | `string` | 否 | `"设计规范"` | 页面标题 |
| `subtitle` | `string` | 否 | 内置文案 | 副标题 |
| `specs` | `array<string>` | 是 | `[]` | 规范条目 |

默认样式：2x3 规范网格。建议 4-6 项。

### data.metric_card

功能：单张指标卡。Python API 返回块级 `MetricCard`；JSON 中 `data.metric_card` 会被 parser 包装成包含一张卡的 `MetricCardsSlide`。

```python
card = data.metric_card(label="准确率", value="92.3%", delta="+3.1%", note="较上期", icon="AC")
```

```json
{"type": "data.metric_card", "title": "单指标", "label": "准确率", "value": "92.3%", "delta": "+3.1%", "note": "较上期", "icon": "AC"}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `label` | `string` | 是 | 无 | 指标名称 |
| `value` | `string` | 是 | 无 | 主数值 |
| `delta` | `string` | 否 | `""` | 变化值；以 `+` 开头显示成功色，否则警示色 |
| `note` | `string` | 否 | `"较上期"` | 对比说明 |
| `icon` | `string` | 否 | `""` | 文本图标占位 |

默认样式：轻量圆角卡片、右上 icon、主数值和 delta。注意 JSON 写法需要 `title` 才能形成完整 slide 标题。

### data.metric_cards

功能：指标卡组。适用于实验结果摘要、运营指标概览、商业复盘、周报总览。

```python
deck.add_slide(data.metric_cards(title="核心指标概览", cards=[data.metric_card(label="AUC", value="0.948")]))
```

```json
{"type": "data.metric_cards", "title": "核心指标概览", "subtitle": "适合数据报告", "scenarios": "实验结果摘要 / 运营指标概览", "cards": [{"label": "准确率", "value": "92.3%", "delta": "+3.1%", "note": "较上期", "icon": "AC"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | `string` | 是 | `""` | 页面标题 |
| `subtitle` | `string` | 否 | `""` | 副标题 |
| `scenarios` | `string` | 否 | 内置场景文案 | 下方说明 |
| `cards` | `array<object>` | 是 | `[]` | 指标卡 |
| `cards[].label` | `string` | 是 | 无 | 指标名称 |
| `cards[].value` | `string` | 是 | 无 | 主数值 |
| `cards[].delta` | `string` | 否 | `""` | 变化值 |
| `cards[].note` | `string` | 否 | `"较上期"` | 对比说明 |
| `cards[].icon` | `string` | 否 | `""` | 图标占位 |

默认样式：横向指标卡 + 说明区域。建议 2-4 张卡。

### data.progress_bars

功能：进度条组。适用于项目进度、完成率、阶段健康度。

```python
deck.add_slide(data.progress_bars(title="项目推进进度", items=[{"label": "开发实现", "value": 0.6, "color": "7C3AED"}]))
```

```json
{"type": "data.progress_bars", "title": "项目推进进度", "items": [{"label": "开发实现", "value": 0.6, "color": "7C3AED"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | `string` | 是 | `""` | 页面标题 |
| `subtitle` | `string` | 否 | 内置文案 | 副标题 |
| `items` | `array<object>` | 是 | `[]` | 进度项 |
| `items[].label` | `string` | 是 | 无 | 名称 |
| `items[].value` | `number` | 是 | 无 | 0-1 之间，渲染时会裁剪 |
| `items[].color` | `string` | 否 | 主题主色 | HEX 颜色 |

默认样式：卡片容器、浅色轨道、彩色进度。`data.progress` 是计划支持别名。

### data.gantt

功能：甘特图。适用于排期、交付节奏、任务计划。

```python
deck.add_slide(data.gantt(title="项目计划", periods=["5月", "6月"], tasks=[{"label": "设计", "start": 0, "end": 1}]))
```

```json
{"type": "data.gantt", "title": "项目计划", "periods": ["5月", "6月"], "tasks": [{"label": "设计", "start": 0, "end": 1, "color": "2563EB"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `periods` | `array<string>` | 是 | `[]` | 时间列 |
| `tasks` | `array<object>` | 是 | `[]` | 任务 |
| `tasks[].label` | `string` | 是 | 无 | 任务名 |
| `tasks[].start` | `integer` | 是 | 无 | 起始列索引 |
| `tasks[].end` | `integer` | 是 | 无 | 结束列索引 |
| `tasks[].color` | `string` | 否 | 自动颜色 | HEX 颜色 |

默认样式：轻量表格背景和彩色时间条。注意 `start/end` 是列索引，不是日期解析。

### data.heatmap

功能：热力矩阵。适用于功能使用、群体行为、场景热度。

```python
deck.add_slide(data.heatmap(title="使用热力", row_labels=["新客"], col_labels=["功能A"], values=[[68]]))
```

```json
{"type": "data.heatmap", "title": "使用热力", "row_labels": ["新客"], "col_labels": ["功能A"], "values": [[68]]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `row_labels` | `array<string>` | 是 | `[]` | 行标签 |
| `col_labels` | `array<string>` | 是 | `[]` | 列标签 |
| `values` | `array<array<number>>` | 是 | `[]` | 数值矩阵 |

默认样式：根据数值映射浅灰、浅蓝、主蓝。注意矩阵行列不匹配时缺失值按 0 处理。

### data.ab_comparison

功能：A/B 实验结果对比。适用于实验汇报和版本差异说明。

```python
deck.add_slide(data.ab_comparison(title="实验结果", headers=["指标", "A", "B"], rows=[["CTR", "4.1%", "4.8%"]], note="B 更优"))
```

```json
{"type": "data.ab_comparison", "title": "实验结果", "headers": ["指标", "A", "B"], "rows": [["CTR", "4.1%", "4.8%"]], "note": "B 更优"}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `headers` | `array<string>` | 是 | `[]` | 表头 |
| `rows` | `array<array<string>>` | 是 | `[]` | 表格行 |
| `note` | `string` | 否 | `""` | 下方结论说明 |

默认样式：调用统一 `add_table()`，note 使用成功色提示。注意每行列数最好与表头一致。

### data.highlight_insight

功能：高亮结论框。适用于突出关键洞察、原因和下一步。

```python
deck.add_slide(data.highlight_insight(title="核心结论", summary="转化率提升 24%", bullets=["版本 B 更优"], next_step="继续优化链路"))
```

```json
{"type": "data.highlight_insight", "title": "核心结论", "summary": "转化率提升 24%", "bullets": ["版本 B 更优"], "next_step": "继续优化链路"}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `summary` | `string` | 是 | `""` | 主结论 |
| `bullets` | `array<string>` | 否 | `[]` | 支撑要点 |
| `next_step` | `string` | 否 | `""` | 下一步 |

默认样式：主色浅背景卡、bullet 列表、底部 next step。建议 summary 不超过两行。

### data.annotations

功能：数据注释列表。适用于异常说明、关键事件、背景补充。

```python
deck.add_slide(data.annotations(title="数据注释", annotations=["5/13 活动上线"], note="已去除异常值"))
```

```json
{"type": "data.annotations", "title": "数据注释", "annotations": ["5/13 活动上线"], "note": "已去除异常值"}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `annotations` | `array<string>` | 是 | `[]` | 注释列表 |
| `note` | `string` | 否 | `""` | 底部备注 |

默认样式：编号标签 + 注释行。建议 2-5 条。

### chart.line

功能：折线图。适用于趋势、实验曲线、阶段性变化。

```python
deck.add_slide(chart.line(title="趋势分析", categories=["4/29", "5/6"], series=[{"name": "指标 A", "values": [320, 540]}]))
```

```json
{"type": "chart.line", "title": "趋势分析", "categories": ["4/29", "5/6"], "series": [{"name": "指标 A", "values": [320, 540], "color": "2563EB"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `categories` | `array<string>` | 是 | `[]` | X 轴分类 |
| `series` | `array<object>` | 是 | `[]` | 数据系列 |
| `series[].name` | `string` | 是 | 无 | 系列名 |
| `series[].values` | `array<number>` | 是 | 无 | 数值 |
| `series[].color` | `string` | 否 | 自动颜色 | HEX 颜色 |
| `subtitle` | `string` | 否 | 内置文案 | 副标题 |

默认样式：自绘折线和图例。注意 series 长度与 categories 最好一致。

### chart.bar

功能：柱状图。适用于分类对比、排行、版本差异。

```python
deck.add_slide(chart.bar(title="渠道转化", categories=["APP"], series=[{"name": "转化数", "values": [680]}]))
```

```json
{"type": "chart.bar", "title": "渠道转化", "categories": ["APP"], "series": [{"name": "转化数", "values": [680]}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `categories` | `array<string>` | 是 | `[]` | X 轴分类 |
| `series` | `array<object>` | 是 | `[]` | 数据系列 |
| `series[].name` | `string` | 是 | 无 | 系列名 |
| `series[].values` | `array<number>` | 是 | 无 | 数值 |
| `series[].color` | `string` | 否 | 自动颜色 | HEX 颜色 |

默认样式：自绘分组柱和网格线。缺失 series value 会按 0 渲染。

### chart.pie

功能：饼图。适用于占比、来源分布、结构组成。

```python
deck.add_slide(chart.pie(title="渠道占比", segments=[{"label": "产品 A", "value": 42}]))
```

```json
{"type": "chart.pie", "title": "渠道占比", "segments": [{"label": "产品 A", "value": 42, "color": "2563EB"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `segments` | `array<object>` | 是 | `[]` | 扇区 |
| `segments[].label` | `string` | 是 | 无 | 名称 |
| `segments[].value` | `number` | 是 | 无 | 数值 |
| `segments[].color` | `string` | 否 | 自动颜色 | HEX 颜色 |

默认样式：使用 `python-pptx` 图表对象，右侧图例显示百分比。输出可编辑。

### chart.donut

功能：环形图。适用于占比和总量突出展示。

```python
deck.add_slide(chart.donut(title="流量来源", center_label="总计", center_value="56,780", segments=[{"label": "自然搜索", "value": 38.6}]))
```

```json
{"type": "chart.donut", "title": "流量来源", "center_label": "总计", "center_value": "56,780", "segments": [{"label": "自然搜索", "value": 38.6}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `segments` | `array<object>` | 是 | `[]` | 环形图扇区 |
| `segments[].label` | `string` | 是 | 无 | 名称 |
| `segments[].value` | `number` | 是 | 无 | 数值 |
| `segments[].color` | `string` | 否 | 自动颜色 | HEX 颜色 |
| `center_label` | `string` | 否 | `"总计"` | 中心标签 |
| `center_value` | `string` | 否 | `""` | 中心数值 |

默认样式：可编辑 doughnut chart + 中心文本 + 右侧百分比列表。

### table.comparison

功能：方案对比表。适用于多方案、多维度比较和推荐结论。

```python
deck.add_slide(table.comparison(title="对比分析", headers=["维度", "方案 A", "方案 B"], rows=[["成本", "中", "低"]], conclusion="优先推荐方案 A。"))
```

```json
{"type": "table.comparison", "title": "对比分析", "headers": ["维度", "方案 A", "方案 B"], "rows": [["成本", "中", "低"]], "conclusion": "优先推荐方案 A。"}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `headers` | `array<string>` | 是 | `[]` | 表头 |
| `rows` | `array<array<string>>` | 是 | `[]` | 表格行 |
| `conclusion` | `string` | 否 | 内置推荐文案 | 表格下方结论 |

默认样式：浅边框卡片、蓝色表头、轻分隔线、最后短文本可渲染为推荐标签。

### narrative.timeline

功能：状态时间轴。适用于项目阶段、研发计划、交付节奏。

```python
deck.add_slide(narrative.timeline(title="项目时间轴", items=[{"label": "需求调研", "date": "2026.05", "description": "明确范围", "status": "done"}]))
```

```json
{"type": "narrative.timeline", "title": "项目时间轴", "items": [{"label": "需求调研", "date": "2026.05", "description": "明确范围", "status": "done"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `items` | `array<object>` | 是 | `[]` | 时间轴节点 |
| `items[].label` | `string` | 是 | 无 | 阶段名 |
| `items[].date` | `string` | 否 | `""` | 时间 |
| `items[].description` | `string` | 否 | `""` | 简短说明 |
| `items[].status` | `string` | 否 | `"normal"` | `done`、`active` 或其他 |

默认样式：`done` 蓝色实心、`active` 紫色高亮、普通节点灰色。建议 4-6 个节点。

### narrative.process_flow

功能：流程图。适用于实施流程、工作流、生成链路。

```python
deck.add_slide(narrative.process_flow(title="实施流程", steps=[{"title": "需求分析", "description": "明确目标", "output": "需求清单"}]))
```

```json
{"type": "narrative.process_flow", "title": "实施流程", "steps": [{"title": "需求分析", "description": "明确目标", "output": "需求清单"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `steps` | `array<object>` | 是 | `[]` | 流程步骤 |
| `steps[].title` | `string` | 是 | 无 | 阶段名称 |
| `steps[].description` | `string` | 否 | `""` | 一行说明 |
| `steps[].output` | `string` | 否 | `""` | 产出物 |

默认样式：横向流程卡 + 轻箭头 + 下方链路说明。建议 4-5 步。

### narrative.roadmap

功能：路线图。适用于季度计划、能力建设节奏。

```python
deck.add_slide(narrative.roadmap(title="路线图", periods=["Q1", "Q2"], rows=[{"label": "产品能力", "start": 0, "end": 2}]))
```

```json
{"type": "narrative.roadmap", "title": "路线图", "periods": ["Q1", "Q2"], "rows": [{"label": "产品能力", "start": 0, "end": 2, "color": "2563EB"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `periods` | `array<string>` | 是 | `[]` | 阶段列 |
| `rows` | `array<object>` | 是 | `[]` | 路线条 |
| `rows[].label` | `string` | 是 | 无 | 行名称 |
| `rows[].start` | `integer` | 是 | 无 | 起始列索引 |
| `rows[].end` | `integer` | 是 | 无 | 结束列索引 |
| `rows[].color` | `string` | 否 | 自动颜色 | HEX 颜色 |

默认样式：时间头、横向路线条。注意索引范围应与 `periods` 长度匹配。

### narrative.swot

功能：SWOT 四象限。适用于战略分析、方案评估、复盘讨论。

```python
deck.add_slide(narrative.swot(title="SWOT", quadrants=[{"title": "优势", "subtitle": "Strengths", "items": ["组件丰富"]}]))
```

```json
{"type": "narrative.swot", "title": "SWOT", "quadrants": [{"title": "优势", "subtitle": "Strengths", "items": ["组件丰富"]}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `quadrants` | `array<object>` | 是 | `[]` | 象限，建议 4 个 |
| `quadrants[].title` | `string` | 是 | 无 | 象限标题 |
| `quadrants[].subtitle` | `string` | 否 | `""` | 副标题 |
| `quadrants[].items` | `array<string>` | 否 | `[]` | 要点 |

默认样式：2x2 浅色卡片 + 中心 SWOT 圆标。

### narrative.problem_solution

功能：问题到对策映射。适用于诊断和行动建议。

```python
deck.add_slide(narrative.problem_solution(title="问题-对策", pairs=[{"problem": "转化率低", "solution": "优化路径"}]))
```

```json
{"type": "narrative.problem_solution", "title": "问题-对策", "pairs": [{"problem": "转化率低", "solution": "优化路径"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `pairs` | `array<object>` | 是 | `[]` | 问题-对策列表 |
| `pairs[].problem` | `string` | 是 | 无 | 问题 |
| `pairs[].solution` | `string` | 是 | 无 | 对策 |

默认样式：左右两列表格、箭头连接。建议 3-5 行。

### narrative.logic_pyramid

功能：逻辑金字塔。适用于结论、论点、论据和支撑材料表达。

```python
deck.add_slide(narrative.logic_pyramid(title="逻辑金字塔", levels=[{"label": "结论"}], side_notes=["核心观点"]))
```

```json
{"type": "narrative.logic_pyramid", "title": "逻辑金字塔", "levels": [{"label": "结论", "note": ""}], "side_notes": ["核心观点"]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `levels` | `array<object>` | 是 | `[]` | 金字塔层级，最多渲染前 4 层 |
| `levels[].label` | `string` | 是 | 无 | 层级文本 |
| `levels[].note` | `string` | 否 | `""` | 当前渲染未使用 |
| `side_notes` | `array<string>` | 否 | `[]` | 右侧注释 |

默认样式：蓝紫梯形感矩形层级和右侧说明。建议 3-4 层。

### narrative.risk_table

功能：风险提示表。适用于风险识别、影响程度和应对建议。

```python
deck.add_slide(narrative.risk_table(title="风险提示", risks=[{"category": "市场风险", "impact": "高", "suggestion": "强化差异化"}]))
```

```json
{"type": "narrative.risk_table", "title": "风险提示", "risks": [{"category": "市场风险", "impact": "高", "suggestion": "强化差异化"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `risks` | `array<object>` | 是 | `[]` | 风险列表 |
| `risks[].category` | `string` | 是 | 无 | 风险类别 |
| `risks[].impact` | `string` | 是 | 无 | 影响程度 |
| `risks[].suggestion` | `string` | 是 | 无 | 建议 |

默认样式：统一表格组件。建议 3-5 行。

### narrative.milestone

功能：里程碑时间轴。当前复用 `TimelineSlide` 渲染。

```python
deck.add_slide(narrative.milestone(title="里程碑", items=[{"label": "开发完成", "date": "2026.03", "status": "active"}]))
```

```json
{"type": "narrative.milestone", "title": "里程碑", "items": [{"label": "开发完成", "date": "2026.03", "description": "核心交付", "status": "active"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `items` | `array<object>` | 是 | `[]` | 同 `narrative.timeline.items` |

默认样式和注意事项同 `narrative.timeline`。

### narrative.relation_table

功能：行动项关系表。适用于负责人、优先级、进度和状态管理。

```python
deck.add_slide(narrative.relation_table(title="行动项", rows=[{"action": "优化功能", "owner": "张三", "priority": "高", "due": "2026-03-15", "progress": "70%", "status": "进行中"}]))
```

```json
{"type": "narrative.relation_table", "title": "行动项", "rows": [{"action": "优化功能", "owner": "张三", "priority": "高", "due": "2026-03-15", "progress": "70%", "status": "进行中"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `rows[].action` | `string` | 是 | 无 | 行动项 |
| `rows[].owner` | `string` | 是 | 无 | 负责人 |
| `rows[].priority` | `string` | 是 | 无 | 优先级 |
| `rows[].due` | `string` | 是 | 无 | 截止时间 |
| `rows[].progress` | `string` | 是 | 无 | 当前进度 |
| `rows[].status` | `string` | 是 | 无 | 状态 |

默认样式：宽表格。列较多，建议文本短。

### narrative.story_structure

功能：叙事结构建议。适用于背景、问题、方法、结果、结论的纵向结构。

```python
deck.add_slide(narrative.story_structure(title="叙事结构", steps=[{"title": "背景", "description": "阐述目标", "icon": "B"}]))
```

```json
{"type": "narrative.story_structure", "title": "叙事结构", "steps": [{"title": "背景", "description": "阐述目标", "icon": "B"}]}
```

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `steps` | `array<object>` | 是 | `[]` | 叙事步骤 |
| `steps[].title` | `string` | 是 | 无 | 步骤标题 |
| `steps[].description` | `string` | 是 | 无 | 步骤说明 |
| `steps[].icon` | `string` | 否 | `""` | 文本图标占位 |

默认样式：右侧纵向卡片链。建议 4-5 步。

### media 与基础组件

`media.icon` 当前支持 `lucide.sparkles`、`heroicons.bolt`、`remix.rocket-line`、`tabler.file-code`、`fa.user`、`bootstrap.chat-left-text` 等前端式命名。`ppt_ui/icons/provider.py` 会把点号语法规范化为 Iconify 兼容 ID，通过默认 `IconifyApiProvider` 获取远程 SVG，并由渲染层使用 `resvg-py` 转为透明 PNG 后插入 PPTX。

| Type | 当前状态 | 说明 |
| --- | --- | --- |
| `media.image` | 已实现 | 本地图片插入，支持 contain/stretch 行为 |
| `media.icon` | 已实现 | 远程 Iconify 兼容图库、本地 `src` 透明 PNG、离线文字 fallback |

示例：

```json
{
  "type": "media.icon",
  "props": {
    "name": "lucide.sparkles",
    "color": "primary",
    "size": 128,
    "stroke_width": 1.8
  }
}
```

默认别名表覆盖常见前端图库，例如 Font Awesome（`fa.user`、`fa-brands.github`）、Bootstrap Icons（`bootstrap.alarm`）、Material Symbols（`material.auto-awesome`）、Carbon、Fluent、Radix、Octicons、Simple Icons、Solar、MingCute、Hugeicons 等。也可以在每个 `Deck` 上注册自定义 provider：

```python
from pathlib import Path
from ppt_ui import Deck, LocalSvgIconProvider, media, layout, page

deck = Deck()
deck.icons.register_alias("company", "brand")
deck.icons.register(LocalSvgIconProvider(Path("assets/icons"), prefix="brand"))
deck.add_page(page.standard(title="Brand Icons", blocks=[media.icon(name="company.logo", layout=layout.grid_item(col=1, span=3, row=1))]))
```

## Theme System

当前主题入口：

```python
from ppt_ui import get_theme

theme = get_theme("default_blue")
single_file_theme = get_theme("examples/themes/company_blue.json")
directory_theme = get_theme("examples/themes/company_modular")
```

`get_theme()` 支持内置主题名、外部单文件 JSON 主题、带 `theme.json` 的外部主题目录、inline theme dict，以及直接传入 `Theme` 对象。通过 `deck_from_json()` 加载 deck 时，相对主题路径会按 deck JSON 所在目录解析。

内置主题存放在 `ppt_ui/themes/` 下的 JSON 文件中。Python 代码只注册主题名并通过 `ThemeLoader` 加载这些文件。

### Theme 来源

| 来源 | 示例 | 状态 |
| --- | --- | --- |
| 内置主题 | `"default_blue"` | 已实现 |
| 内置别名 | `"default"` | 已实现 |
| 外部单文件 JSON | `"./themes/company_blue.json"` | 已实现 |
| 外部目录主题 | `"./themes/company_modular"` | 已实现 |
| Inline dict | `{ "name": "custom", "extends": "default_blue" }` | 已实现 |

### 内置主题

| 主题 | 主色 | 强调色 | 背景 | 适合场景 |
| --- | --- | --- | --- | --- |
| `theme.tech_blue` | `#2563EB` | `#7C3AED` | `#FFFFFF` | AI 产品、技术方案、组件库 demo |
| `theme.academic_clean` | `#1E3A8A` | `#2563EB` | `#FFFFFF` | 论文答辩、学术报告、实验分析 |
| `theme.business_navy` | `#0F2A5F` | `#D4AF37` | `#F8FAFC` | 商业计划、企业汇报、战略页 |
| `theme.data_dashboard` | `#2563EB` | `#06B6D4` | `#F8FAFC` | 数据报告、运营周报、指标看板 |
| `theme.medical_teal` | `#0F766E` | `#14B8A6` | `#F8FEFF` | 医疗 AI、OCT、生物医学、科研 deck |
| `theme.dark_tech` | `#38BDF8` | `#A855F7` | `#020617` | 发布会、深色技术演示 |
| `theme.claude_warm` | `#8B5E34` | `#D97706` | `#F7F3EA` | 温暖叙事报告、产品文档、思考型汇报 |

`default`、`default_blue`、`tech_blue` 和 `theme.tech_blue` 都会解析到 Tech Blue 内置主题。

目录主题使用 `theme.json` 作为入口，并可以引用 token / component 片段：

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

### Theme 字段

| 字段 | 类型 | 默认值/说明 |
| --- | --- | --- |
| `name` | `string` | `tech_blue` |
| `slide_width` | `float` | `13.333` inch |
| `slide_height` | `float` | `7.5` inch |
| `colors` | `ColorTokens` | 颜色 token |
| `fonts` | `FontTokens` | 字体 token |
| `spacing` | `SpacingTokens` | 间距 token |
| `radius_tokens` | `RadiusTokens` | 圆角 token |
| `shadow` | `ShadowTokens` | 阴影偏移 token |
| `component_styles` | `dict[str, ComponentStyle]` | 组件样式 |
| `component_defaults` | `dict[str, dict]` | 组件与 variant 的默认样式值 |
| `chart_palette` | `list[str]` | 图表类组件使用的主题色板 |
| `card_shadow` | `bool` | 是否启用卡片阴影 |

### ColorTokens

| Token | 默认值 | 说明 |
| --- | --- | --- |
| `background` | `FFFFFF` | 页面背景 |
| `surface` | `F8FAFC` | 浅卡片背景 |
| `surface_white` | `FFFFFF` | 白色卡片 |
| `primary` | `2563EB` | 主蓝 |
| `primary_dark` | `1E3A8A` | 深蓝 |
| `primary_soft` | `EFF6FF` | 浅蓝 |
| `primary_tint` | `DBEAFE` | 蓝色 tint |
| `accent` | `7C3AED` | 紫色强调 |
| `accent_soft` | `F5F3FF` | 浅紫 |
| `accent_tint` | `EDE9FE` | 紫色 tint |
| `success` | `10B981` | 成功色 |
| `success_soft` | `ECFDF5` | 浅成功色 |
| `warning` | `F59E0B` | 警示色 |
| `warning_soft` | `FFF7ED` | 浅警示色 |
| `danger` | `EF4444` | 危险色 |
| `text_primary` | `0F172A` | 主文本 |
| `text_secondary` | `64748B` | 次级文本 |
| `text_tertiary` | `94A3B8` | 辅助文本 |
| `border` | `E2E8F0` | 边框 |
| `border_light` | `EEF2F7` | 浅边框 |
| `gray_50` | `F8FAFC` | 中性色 |
| `gray_100` | `F1F5F9` | 中性色 |
| `gray_200` | `E2E8F0` | 中性色 |
| `gray_700` | `334155` | 中性色 |
| `shadow_light` | `EEF2FF` | 浅阴影 |
| `shadow_card` | `E5EAF6` | 卡片阴影 |

### FontTokens

| Token | 默认值 | 说明 |
| --- | --- | --- |
| `family` | `Microsoft YaHei` | 字体 |
| `title_size` | `36` | 封面标题 |
| `subtitle_size` | `15` | 副标题 |
| `h1_size` | `28` | 页面标题 |
| `h2_size` | `18` | 模块标题 |
| `body_size` | `11` | 正文 |
| `caption_size` | `10` | 辅助文本 |
| `tiny_size` | `8` | 极小文本 |
| `display_size` | `54` | 大数字 |

### Spacing / Radius / Shadow

| Token | 默认值 | 说明 |
| --- | --- | --- |
| `spacing.base` | `8` | 设计基准值 |
| `spacing.page_margin` | `0.55` | 左右页边距 inch |
| `spacing.page_y` | `0.45` | 上下页边距 inch |
| `spacing.title_top` | `0.48` | 标题顶部 |
| `spacing.content_top` | `1.55` | 内容区顶部 |
| `spacing.footer_y` | `7.04` | 页脚 y |
| `spacing.gutter` | `0.20` | 卡片间距 |
| `spacing.card_padding` | `0.22` | 卡片内边距 |
| `radius_tokens.sm/md/lg` | `0.035/0.055/0.075` | 圆角调整值 |
| `shadow.card_offset_x/y` | `0.012/0.018` | 卡片阴影偏移 |

### Component Styles

当前已有组件样式 key：

| Key | 用途 |
| --- | --- |
| `card.default` | 通用卡片 |
| `metric_card.default` | 指标卡 |
| `table.comparison` | 对比表 |
| `timeline.status_cards` | 时间轴状态卡 |
| `process_flow.compact_cards` | 流程卡 |
| `conclusion.hero` | 结论页主容器 |

新增主题可在 Python 中构造 `Theme` 并传给 `Deck(theme=custom_theme)`。命名主题注册和从 JSON 指定自定义主题文件属于计划支持。

## Layout System

SlideForge 当前布局系统以 inch 为单位，核心是 `Box` 和 `PageBox`。主题提供页面尺寸和边距，`PageBox.from_theme(theme)` 会生成可用页面区域。

推荐实践：

- 先用 `add_slide_title()` 得到统一内容区。
- 使用 `Box.inset()` 做内边距。
- 使用 `split_cols()` 和 `split_rows()` 做网格，而不是到处写绝对坐标。
- 复杂组件内部可以保留少量局部坐标，但应尽量基于 `content_box()` 和 theme spacing。

当前没有完整 flex/grid layout engine；Row、Column、Spacer、Padding、Alignment 属于计划支持方向。

## Renderer

组件不直接调用 `python-pptx` 的原因是：统一样式、统一单位、集中处理字体/颜色/卡片/表格，并减少 Agent 接触底层 shape 的机会。

`PptxRenderer` 当前 helper：

| Helper | 功能 | 常用组件 |
| --- | --- | --- |
| `background(slide)` | 设置背景色 | 所有页面 |
| `rect(slide, box, fill, line=None, rounded=False)` | 绘制矩形/圆角矩形 | 卡片、表格、标签 |
| `line(slide, x1, y1, x2, y2, color=None, width=1.0)` | 绘制连接线 | 时间轴、图表、流程 |
| `circle(slide, box, fill, line=None)` | 绘制圆形 | icon 占位、节点 |
| `text(slide, box, text, size=None, color=None, bold=False, align="left", valign="top")` | 文本框 | 所有文本 |
| `bullet_list(slide, box, items, size=None, ...)` | bullet 列表 | 双栏、SWOT、洞察 |
| `card(slide, box, fill=None, line=None)` | `add_card()` 简写 | 内部兼容 |
| `pill(slide, box, text, fill=None, color=None)` | pill 标签 | 封面元信息 |
| `accent_bar(slide, x=..., y=..., h=...)` | `add_accent_bar()` 简写 | 标题装饰 |
| `content_box()` | 返回统一内容区 | 页面布局 |
| `add_accent_bar()` | 左上蓝紫强调条 | 大多数 slide |
| `add_slide_title(title, subtitle="", section=None)` | 统一标题区并返回内容区 | 大多数 slide |
| `add_footer(text=...)` | 轻量页脚 | 大多数 slide |
| `add_card(box, fill=None, line=None, shadow=True)` | 统一卡片 | 数据、布局、叙事组件 |
| `add_metric_card(...)` | 指标卡渲染 | `MetricCard` |
| `add_section_label(label, box)` | 小编号标签 | 目录、流程、表格 |
| `add_status_timeline_node(...)` | 状态时间轴节点 | `TimelineSlide` |
| `add_process_step_card(...)` | 流程步骤卡 | `ProcessFlowSlide` |
| `add_table(headers, rows)` | 统一表格 | 对比表、风险表、关系表 |

注意：renderer helper 是内部 API，未来可能增强但应保持兼容。

## Export Screenshots

SlideForge 可以把生成的 PPTX 每页导出为 PNG：

```python
from ppt_ui.export import export_pptx_screenshots

export_pptx_screenshots("examples/demo.pptx", "examples/demo_screenshots")
```

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `pptx_path` | `str | Path` | 必填 | PPTX 路径 |
| `output_dir` | `str | Path` | 必填 | 输出目录 |
| `width` | `int` | `1920` | 导出宽度 |
| `height` | `int` | `1080` | 导出高度 |

行为：

- 每次导出会覆盖整个截图目录。
- 输出文件会规范化为 `slide_01.png`、`slide_02.png`。
- 依赖 Windows PowerPoint COM 自动化。
- 没有 PowerPoint 或 `pywin32` 时会抛出 `ScreenshotExportError`。

## Full Examples

### 完整 JSON 示例

```json
{
  "title": "SlideForge Demo",
  "theme": "default_blue",
  "slides": [
    {
      "type": "slide.title",
      "title": "可复用 PPT UI 组件库",
      "subtitle": "Agent-driven PPT UI Framework",
      "presenter": "SlideForge",
      "date": "2026.05.03"
    },
    {
      "type": "slide.section",
      "number": "01",
      "title": "基础布局组件",
      "subtitle": "快速搭建标准汇报页面结构",
      "keywords": ["标题页", "双栏布局", "指标卡", "表格", "时间轴"]
    },
    {
      "type": "layout.two_column",
      "title": "为什么需要组件库",
      "left_title": "Agent 友好",
      "left_items": ["只需描述页面语义", "避免直接操作 shape", "输出保持可编辑"],
      "right_title": "工程可复用",
      "right_items": ["统一主题 token", "统一布局规则", "可扩展 registry"]
    },
    {
      "type": "data.metric_cards",
      "title": "核心指标概览",
      "cards": [
        {"label": "准确率", "value": "92.3%", "delta": "+3.1%", "note": "较上期", "icon": "AC"},
        {"label": "AUC", "value": "0.948", "delta": "+0.026", "note": "验证集", "icon": "AU"}
      ]
    },
    {
      "type": "table.comparison",
      "title": "方案对比分析",
      "headers": ["维度", "方案 A", "方案 B"],
      "rows": [["成本", "中", "低"], ["周期", "短", "中"], ["推荐", "A", "B"]],
      "conclusion": "综合功能完整性、实施周期与成本，优先推荐方案 A。"
    },
    {
      "type": "narrative.timeline",
      "title": "项目时间轴",
      "items": [
        {"label": "需求分析", "date": "2026.05", "description": "明确目标", "status": "done"},
        {"label": "开发测试", "date": "2026.07", "description": "完成核心组件", "status": "active"}
      ]
    },
    {
      "type": "narrative.process_flow",
      "title": "项目实施流程",
      "steps": [
        {"title": "需求分析", "description": "明确目标与范围", "output": "需求清单"},
        {"title": "方案设计", "description": "输出结构化页面方案", "output": "DSL Schema"},
        {"title": "开发实现", "description": "组件渲染与样式统一", "output": "组件库"}
      ]
    },
    {
      "type": "slide.conclusion",
      "points": [
        {"title": "组件复用", "description": "降低重复排版成本"},
        {"title": "主题统一", "description": "通过 token 保证一致性"},
        {"title": "Agent 友好", "description": "由 JSON DSL 驱动"}
      ]
    },
    {
      "type": "slide.qa",
      "project": "SlideForge",
      "description": "欢迎交流组件设计、主题扩展与 Agent 生成链路"
    }
  ]
}
```

### 完整 Python 示例

```python
from ppt_ui import Deck, data, layout, narrative, slide, table

deck = Deck(title="SlideForge Demo")
deck.add_slide(slide.title(title="可复用 PPT UI 组件库", subtitle="Agent-driven PPT UI Framework"))
deck.add_slide(slide.section(number="01", title="基础布局组件", keywords=["双栏", "指标卡", "时间轴"]))
deck.add_slide(
    layout.two_column(
        title="为什么需要组件库",
        left_title="Agent 友好",
        left_items=["描述页面语义", "避免底层 shape"],
        right_title="工程可复用",
        right_items=["统一主题", "统一布局"],
    )
)
deck.add_slide(
    data.metric_cards(
        title="核心指标概览",
        cards=[data.metric_card(label="准确率", value="92.3%", delta="+3.1%", icon="AC")],
    )
)
deck.add_slide(
    table.comparison(
        title="方案对比",
        headers=["维度", "方案 A", "方案 B"],
        rows=[["成本", "中", "低"]],
        conclusion="优先推荐方案 A。",
    )
)
deck.add_slide(
    narrative.timeline(
        title="项目时间轴",
        items=[{"label": "开发测试", "date": "2026.07", "description": "完成核心组件", "status": "active"}],
    )
)
deck.add_slide(slide.qa())
deck.render("examples/python_api_demo.pptx")
```

## Agent Usage Guide

Agent 应该生成 JSON DSL，而不是生成 `python-pptx` 代码。

推荐流程：

1. 分析用户需求，判断是汇报、方案、数据报告还是复盘。
2. 拆分页面结构，例如封面、目录、章节、数据页、分析页、总结页。
3. 为每页选择 namespace type。
4. 填写该组件的必填字段，控制内容长度。
5. 把 JSON 交给 `deck_from_dict()` 或 `deck_from_json()` 渲染。

Agent 约束：

- `type` 必须来自 registry。
- 不要输出 `add_textbox`、`add_shape`、绝对坐标。
- 图表 `series[].values` 长度应尽量匹配 `categories`。
- 表格每行列数应匹配 `headers`。
- 标题、bullet、表格单元格文字要短，避免溢出。
- 未实现字段如 `style`、`layout`、`hidden` 不应依赖当前版本生效。

常见错误：

| 错误 | 结果 | 修复 |
| --- | --- | --- |
| `type` 不存在 | `ValueError: Unsupported slide type` | 使用已实现 namespace type |
| 必填字段缺失 | dataclass 构造报错 | 查组件参数表 |
| chart 数据长度不一致 | 缺失值或视觉错位 | 对齐 `categories` 和 `values` |
| table 行列不匹配 | 列宽不稳定 | 每行列数等于 headers |
| 内容过长 | 文本缩小或溢出 | 缩短文本，拆成多页 |

## Component Extension Guide

以新增 `chart.scatter` 为例：

1. 在 `ppt_ui/components/data.py` 新增 `ScatterChartSlide` 和必要的 dataclass，例如 `ScatterPoint`。
2. 实现 `render(ctx, box)`，优先使用 `ctx.renderer.add_slide_title()`、`add_card()`、`Box` 布局。
3. 在 `ppt_ui/api.py` 的 `ChartNamespace` 增加 `scatter(...)` 工厂。
4. 在 `ppt_ui/schema/parser.py` 中新增 `_scatter_chart_slide()` 工厂。
5. 在 `build_default_registry()` 注册 `registry.register_slide("chart.scatter", _scatter_chart_slide)`。
6. 在 `examples/sample_deck.json` 增加示例。
7. 在 `tests/test_parser.py` 增加 parser 和 namespace API 测试。
8. 在文档的 Component API 中补充参数表、JSON 示例、注意事项。

建议为大型组件库保留 family + variant 思路：`chart.line`、`chart.bar`、`chart.scatter` 共用 chart family 的主题 token，但各自拥有独立渲染表达。

## FAQ

### 生成的 PPT 可以编辑吗？

可以。SlideForge 底层使用 `python-pptx` 创建 PowerPoint shape、textbox 和 chart，输出是可编辑 `.pptx`。

### 为什么不用 Agent 直接写 python-pptx？

直接写底层 API 容易造成坐标混乱、样式不一致、重复代码多。SlideForge 让 Agent 输出语义化 JSON，由组件库统一渲染。

### JSON type 写错怎么办？

parser 会抛出 `ValueError: Unsupported slide type`。请使用本文档中的已实现 namespace type。

### 中文字体显示异常怎么办？

当前默认字体是 `Microsoft YaHei`。在没有该字体的系统上，可以在 Python 中自定义 `Theme.fonts.family`，或在 PowerPoint 中替换字体。

### 图表数据太长怎么办？

减少分类数量、拆成多页，或改用表格/注释组件。当前还没有自动抽样和文本避让。

### 如何自定义主题？

可以在 Python 中构造 `Theme` 并传给 `Deck(theme=theme)`，也可以通过 `get_theme()` / `ThemeLoader` 加载外部单文件 JSON 或目录主题，例如 `get_theme("examples/themes/company_blue.json")`、`get_theme("examples/themes/company_modular")`。

### 如何新增组件？

新增 dataclass 组件、实现 `render()`、注册到 `ComponentRegistry`、补充 namespace API、示例和测试。

### 如何关闭截图导出？

运行：

```bash
uv run python examples/demo_deck.py --no-screenshots
```

### Windows / macOS 是否都支持？

PPTX 生成跨平台；截图导出当前依赖 Windows PowerPoint COM。macOS/Linux 截图导出属于计划支持。

### PowerPoint COM 截图导出依赖什么？

依赖 Windows、Microsoft PowerPoint、本地 COM 自动化和 `pywin32`。

## Roadmap

- 更多 chart 组件：scatter、area、combo、waterfall。
- 更多主题：商务灰蓝、学术简洁、深色科技、品牌主题。
- 更完整 layout engine：Row、Column、Spacer、Padding、Alignment、12 栏栅格。
- 自动文本缩放、溢出检测和分页建议。
- SVG/icon 渲染：把 Iconify、Lucide、Heroicons 等前端图标库接入 PPT。
- `media.image` 图片组件和图片裁切策略。
- 更强 JSON schema 校验和错误提示。
- Agent prompt templates 和页面规划器。
- Web preview 或截图对比回归。
- 从 JSON 指定截图导出、page size、metadata、author、version。
