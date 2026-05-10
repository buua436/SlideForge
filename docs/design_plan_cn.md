# SlideForge 设计与实施总计划

状态：pre-v1 统一设计与计划文档  
语言：中文  
来源：合并旧版 `design.md`、`design_v2.md`、`design_v2_cn.md`、`design_gap_plan.md`、`v2_implementation_plan.md`、`v2_next_plan_cn.md`  
维护规则：后续所有设计决策、需求计划、模块任务、完成状态都以本文档为准。

## 目录

- 项目目标
- 核心定位
- 架构总览
- 状态说明
- 已完成能力总表
- 未完成能力总表
- 模块化需求与计划
- 组件任务模板
- JSON DSL 分层策略
- Theme 与样式策略
- 质量与验收标准
- 下一步执行顺序
- 暂缓事项

## 1. 项目目标

SlideForge 的目标是成为一套面向 Agent 的 Python PPT UI 组件框架。它不是 `python-pptx` 的薄封装，也不是一组固定 PPT 模板，而是类似前端 UI 框架一样，通过结构化 JSON DSL 或 Python namespace API 组合页面、布局、组件、主题和基础图形，最终生成可编辑的 `.pptx`。

SlideForge 需要同时满足两个方向：

| 方向 | 目标 | 用户体验 |
| --- | --- | --- |
| 低门槛 | 不懂排版、不写坐标，也能生成美观、统一、可编辑的 PPT | Agent 只填 JSON，开发者只调用少量 namespace API |
| 高上限 | 高级用户可以控制布局、主题、slot、primitive、组件实现和渲染策略 | 可以做完全不同风格的主题、复杂图表、模型结构图、论文答辩和商业 deck |

这两个目标不能互相牺牲。低门槛依赖强默认值，高上限依赖可组合架构。

## 2. 核心定位

### 2.1 SlideForge 是什么

SlideForge 是一个“Agent-driven PPT UI Framework”：

```text
JSON DSL / Python Namespace API
  -> Registry / Parser
  -> Deck / Page / Block
  -> Component Tree
  -> Primitive Scene Graph
  -> PptxRenderer
  -> editable .pptx
```

### 2.2 SlideForge 不是什么

| 不是 | 原因 |
| --- | --- |
| 不是直接暴露 `python-pptx` 的 shape API | Agent 不应该直接写 `add_textbox`、`add_shape`。 |
| 不是固定模板生成器 | 一页可以组合多个组件，组件可以嵌套，主题和布局可替换。 |
| 不是截图转 PPT | 默认输出必须保持可编辑。图片化只作为特殊 fallback。 |
| 不是只换颜色的主题系统 | 主题要控制颜色、字体、字号、间距、圆角、阴影、装饰、组件默认和 slot 样式。 |

### 2.3 核心设计原则

| 原则 | 说明 |
| --- | --- |
| 语义优先 | Agent 描述“指标卡、时间轴、模型框架图”，而不是描述每个 shape 坐标。 |
| Primitive-first | 所有组件最终由基础 primitive 组合而成，组件不直接操作底层 PPT shape。 |
| Container-first | 容器决定外观和空间，语义组件只负责自身信息结构。 |
| Slot-first | 组件内部元素通过稳定 slot 暴露，例如 `label`、`value`、`icon`、`plot`、`legend`。 |
| Theme as defaults | theme 提供大部分默认值，JSON 不应反复填写颜色、字号、间距、圆角。 |
| CSS-like override | 支持 `type`、`id`、`class`、`type::slot` 等方式覆盖样式。 |
| 一组件一任务 | 每个组件的细化必须独立成任务，避免“统一优化组件”这种不可验收任务。 |
| Editable first | 默认输出必须是可编辑 PPTX。 |
| Diagnostics first | 内容过长、布局溢出、数据不匹配、未知 token 都要有诊断信息。 |
| Screenshot review | 视觉组件必须进入截图 review，而不是只靠单元测试。 |

## 3. 架构总览

### 3.1 能力金字塔

```text
Agent JSON / Python Namespace API
  -> Page / Master / Theme Presets
  -> Semantic Components
  -> Layout Containers
  -> Slot Layout Engine
  -> Primitive Scene Graph
  -> PptxRenderer / Export / Review
```

| 层级 | 责任 | 低门槛要求 | 高上限要求 |
| --- | --- | --- | --- |
| Renderer | 把 primitive 渲染成 PPTX | 默认稳定生成可编辑 PPT | 支持 native chart、shape chart、图片、图标、连接线、富文本 |
| Primitive | 最小视觉对象 | 内置文本、矩形、线条、图标、图片 | 支持 path、polygon、connector、rich text、group style |
| Slot Layout | 组件内部布局 | 默认 recipe 自动排版 | 支持 stack、row、grid、template、dock、overlay、flow |
| Layout Container | 页面和组件容器 | card/grid/stack 开箱即用 | 可递归组合，支持视觉 variant、响应式降级 |
| Semantic Component | 业务组件 | Agent 只填 props | slot、variant、bare mode、props schema、size hint |
| Page/Master/Theme | PPT 整体体验 | 一套主题即可好看 | 多 master、多主题、多风格差异、外部主题 |
| Agent API | 输入接口 | JSON DSL 简短清晰 | 可诊断、可扩展、自描述 schema、自动修复建议 |

### 3.2 核心对象职责

| 对象 | 职责 | 不应该负责 |
| --- | --- | --- |
| `Deck` | 管理整套文稿、主题、页面、注册表、样式表和渲染入口 | 不直接绘制组件 |
| `Page` | 管理单页类型、母版、标题、blocks、notes、chrome | 不决定组件内部视觉 |
| `Block` | 表示页面上的一个组件实例，包含 `type`、`variant`、`props`、`layout`、`style`、`id`、`class` | 不直接绘制 |
| `Component` | 把语义 props 转成 primitive tree | 不绘制页面标题、页码、全局 footer |
| `Primitive` | 最小可渲染图形或文本节点 | 不理解业务语义 |
| `Layout` | 分配空间和 box | 不决定颜色和字体 |
| `Theme` | 提供视觉 token 和组件默认样式 | 不决定页面是否有 footer |
| `StyleSheet` | 类 CSS 的样式覆盖 | 不替代 theme token |
| `Renderer` | 把 primitive tree 渲染为 PPT shape | 不理解业务组件 |
| `Registry` | 管理组件、页面、布局、母版、主题、渲染实现的可扩展注册 | 不做业务渲染 |

### 3.3 数据流

```text
JSON DSL
  -> Parser
  -> Deck / Page / Block
  -> Registry create component
  -> Layout resolves block box
  -> Component render_to_primitives()
  -> StyleResolver resolves theme/class/id/slot styles
  -> PptxRenderer renders editable PPTX
```

## 4. 状态说明

| 状态 | 含义 |
| --- | --- |
| Done | 已实现并有测试或明确验证。 |
| Partial | 已有基础能力，但没有完全满足目标设计。 |
| Todo | 尚未实现。 |
| Blocked | 依赖外部决策或前置任务。 |

## 5. 已完成能力总表

### 5.1 V2 基础能力

| ID | 模块 | 已完成能力 | 验证 |
| --- | --- | --- | --- |
| V2-001 | Primitive | 不可变 primitive model 和 style value objects | `tests/test_primitives.py` |
| V2-002 | Style | `StyleRule`、`StyleSheet`、type/id/class selector | `tests/test_stylesheet.py` |
| V2-003 | Style | `StyleResolver`，支持 token 解析和级联合并 | `tests/test_style_resolver.py` |
| V2-004 | Parser | block `id`、`class`、deck-level `styles` | `tests/test_parser.py` |
| V2-005 | Renderer | `render_tree()` 和 primitive renderer bridge | `tests/test_primitive_renderer.py` |
| V2-006 | Component | `render_to_primitives()` 组件协议 | `tests/test_component_contract.py` |
| V2-007 | Primitive Blocks | `primitive.text`、`primitive.rect`、`primitive.line`、`primitive.image`、`primitive.icon` | `tests/test_primitive_blocks.py` |
| V2-008 | Basic | `basic.text`、`basic.card`、`basic.divider` 迁移到 primitive | `tests/test_basic_v2.py` |
| V2-009 | Data | `data.metric_card`、`data.metric_cards`、`data.progress` primitive 化 | `tests/test_data_v2.py` |
| V2-010 | Chart | `chart.line`、`chart.bar`、`chart.pie`、`chart.donut` 初步 primitive/chart shell | `tests/test_chart_v2.py` |
| V2-011 | Table | `table.basic`、`table.comparison` primitive 化 | `tests/test_table_v2.py` |
| V2-012 | Narrative | `timeline`、`process_flow`、`roadmap`、`diagram.model` primitive 化 | `tests/test_narrative_v2.py` |
| V2-013 | Master | 母版可用 primitive chrome 渲染 | `tests/test_master_v2.py` |
| V2-014 | Text | fit、clip、resize、truncate overflow 策略 | `tests/test_text_overflow.py` |
| V2-015 | Diagnostics | parser/render diagnostics 带 path 和 suggestion | `tests/test_diagnostics_v2.py` |
| V2-016 | Export | 截图 review helper 和 contact sheet | `tests/test_export_review.py` |

### 5.2 最近完成的框架能力

| ID | 模块 | 已完成能力 | 验收 |
| --- | --- | --- | --- |
| FND-001 | Slot Layout | `SlotNode`、`SlotLayoutRecipe`、`SlotLayoutEngine` | 支持 `stack`、`row`、`grid`、`template`、`dock`、`overlay`、`flow` |
| FND-002 | Container-first | `layout.container`、`layout.card`、`layout.stack`、`layout.grid` | 容器可递归渲染子组件 |
| FND-003 | Bare Semantic | `data.metric_card` 和 `data.metric_cards` 支持 bare/plain | 语义组件可不强制自带卡片背景 |
| FND-004 | Slot Contract | `ComponentSlot` 和 `Component.slot_contract()` | metric 和 layout 容器已有首批 slot 声明 |
| FND-005 | Slot Style | 支持 `data.metric_card::value` 等 slot selector | renderer 通过 primitive metadata 应用 slot 样式 |
| FND-006 | Selector Decision | 本阶段采用 `type::slot` | 暂不做完整 CSS descendant parser |
| FND-007 | Group Inheritance | group 只继承文本相关样式 | fill/stroke/background 不继承 |
| FND-008 | Registry Variant | `ComponentRegistry` 支持 family、variant、implementation、default variant | `block.variant` 可参与组件创建 |
| V2-019 | Planning | 每个组件独立成任务 | 组件细化清单已建立 |

## 6. 未完成能力总表

### 6.1 框架层未完成

| ID | 状态 | 模块 | 需求 | 验收标准 |
| --- | --- | --- | --- | --- |
| FND-009 | Partial | Registry | 拆分 components、pages、layouts、masters、themes、primitive renderers 注册边界 | parser 不再承担过多路由；各 registry 单测 |
| FND-010 | Partial | Props Schema | 每个组件有 typed props 或 schema 描述 | 缺失必填、类型错误有诊断 |
| FND-011 | Todo | Size Hint | `SizeHint(min/preferred/max/aspect)` | box 太小时 warning，组件可自动降级 |
| FND-012 | Todo | Layout Diagnostics | 检测 grid 越界、重叠、负尺寸、block overlap | parser/render 单测 |
| FND-013 | Partial | Style Cascade | 明确 theme/page/master/layout/component/slot/inline 优先级 | 优先级冲突有单测 |
| FND-014 | Partial | Token Diagnostics | 未知 style key 和 unresolved token 诊断 | warning 包含 path 和 suggestion |
| FND-015 | Todo | RichText | editable multi-run text rendering | PPT 中文本仍可编辑，多 run 样式保留 |
| FND-016 | Partial | Shapes | connector、path、polygon 渲染完整化 | arrow、dash、filled polygon、freeform 策略 |
| FND-017 | Todo | Charts | native PPT chart 与 shape-composed chart 双实现 | chart variant 可选 implementation |
| FND-018 | Todo | Page Style | page-level styles | 页面局部 styles 与 deck styles 合并 |
| FND-019 | Todo | Speaker Notes | 写入 PPT speaker notes | `Page.notes` 输出到 PPT 备注页 |
| FND-020 | Todo | Asset Registry | 管理图片、icon、URL、缓存、生成资源 | 缺失资源和缓存状态有诊断 |
| FND-021 | Partial | Image | URL、crop、fit variants、alt text | `media.image` 支持更多来源和策略 |
| FND-022 | Partial | Icon | provider diagnostics、vector/editable strategy、style hooks | icon 居中、尺寸、颜色、stroke 可控 |
| FND-023 | Todo | Visual Regression | 截图 baseline diff | 组件主题矩阵可回归 |
| FND-024 | Todo | Public Docs | 更新 `docs/zh.md` 和 `docs/en.md` | 与真实 API 对齐 |
| FND-025 | Partial | Public API | 清理 namespace API | 容器/slot/schema 后 API 统一 |

### 6.2 下一阶段主线任务

| ID | 优先级 | 状态 | 任务 | 依赖 | 产物 | 验收 |
| --- | --- | --- | --- | --- | --- | --- |
| NEXT-001 | P0 | Todo | 拆分注册系统 | FND-008 | `ComponentRegistry`、`PageRegistry`、`LayoutRegistry`、`MasterRegistry`、`PrimitiveRendererRegistry` 边界清晰 | registry 单测；parser 简化 |
| NEXT-002 | P0 | Todo | 组件 props schema | NEXT-001 | 每个组件有 typed props 或 schema 描述 | 输入错误有诊断 |
| NEXT-003 | P0 | Todo | SizeHint | NEXT-002 | `SizeHint(min/preferred/max/aspect)` | 尺寸不足 warning |
| NEXT-004 | P0 | Todo | Layout diagnostics | FND-001 | grid 越界、重叠、负尺寸诊断 | 单测覆盖 |
| NEXT-005 | P0 | Todo | 完整 style cascade | FND-005 | theme/page/master/layout/component/slot/inline 优先级明确 | 单测覆盖优先级 |
| NEXT-006 | P1 | Todo | 未知 token/style 诊断 | NEXT-005 | unresolved token warning | 包含 path 和 suggestion |
| NEXT-007 | P1 | Todo | Page stylesheet | NEXT-005 | page-level styles | 页面局部样式单测 |

## 7. 模块化需求与计划

### 7.1 Page 与 Master

| ID | 状态 | 对象 | 需求 | 依赖 | 验收 |
| --- | --- | --- | --- | --- | --- |
| PAGE-001 | Partial | `page.cover` | 封面页 chrome、slots、theme defaults、master 交互 | FND-013 | 不同主题下封面有明显风格差异 |
| PAGE-002 | Partial | `page.standard` | 标题、副标题、内容区、chrome 统一 | FND-013 | 一页多组件不显得散 |
| PAGE-003 | Partial | `page.section` | 章节编号、关键词区、theme variants | FND-013 | 章节页不空、信息密度合理 |
| PAGE-004 | Partial | `page.blank` | 验证禁用 master 的纯画布行为 | None | 适合完全自定义 canvas |
| PAGE-005 | Partial | `page.closing` | 结论页内容 slots 和主题表现 | FND-013 | slogan、结论卡片和 footer 协调 |
| PAGE-006 | Partial | `page.qa` | Q&A 页极简但不空 | FND-013 | 项目名、说明、页脚可配置 |
| PAGE-007 | Partial | `master.default` | title/footer/page-number slots | FND-013 | 可覆盖 title/footer/page number |
| PAGE-008 | Partial | `master.tech_blue` | 转为 primitive-backed recipe | FND-013 | theme 控制 accent bar、footer、背景 |
| PAGE-009 | Partial | `master.blank` | 无 chrome 行为明确 | None | 完全无默认背景装饰 |

### 7.2 Primitive

| ID | 状态 | 组件 | 需求 | 依赖 | 验收 |
| --- | --- | --- | --- | --- | --- |
| PRIM-001 | Partial | `primitive.text` | overflow、文本样式诊断、slot-friendly defaults | FND-014 | 长文本不溢出且有诊断 |
| PRIM-002 | Todo | `primitive.rich_text` | JSON/Python API，多 run 可编辑渲染 | FND-015 | PPT 中多样式文本可编辑 |
| PRIM-003 | Partial | `primitive.rect` | radius、shadow、opacity、border、fill 行为完善 | FND-016 | token 与数值都可用 |
| PRIM-004 | Todo | `primitive.ellipse` | ellipse/circle JSON/Python API | FND-016 | 可画圆和椭圆 |
| PRIM-005 | Partial | `primitive.line` | line caps、dash、arrows、theme defaults | FND-016 | 连接线专业可控 |
| PRIM-006 | Todo | `primitive.connector` | 带箭头和语义连接元数据 | FND-016 | 流程图和模型图可用 |
| PRIM-007 | Partial | `primitive.polygon` | filled polygon 和 API | FND-016 | SWOT、金字塔、图形装饰可用 |
| PRIM-008 | Todo | `primitive.path` | path/freeform 策略或限制说明 | FND-016 | 能表达复杂形状或清楚 fallback |
| PRIM-009 | Partial | `primitive.image` | asset registry、URL、alt、fit/crop | FND-020/FND-021 | 图片资源可诊断 |
| PRIM-010 | Partial | `primitive.icon` | provider diagnostics、vector strategy、style hooks | FND-022 | icon 视觉居中且可控 |
| PRIM-011 | Partial | `primitive.table` | table style slots 和 cell styling | FND-013 | 单元格级样式可控 |
| PRIM-012 | Partial | `primitive.chart` | chart variants 和 chart style slots | FND-017 | native/shape 策略可选 |
| PRIM-013 | Partial | `primitive.group` | group inheritance 和 group layout | FND-007 | 文本继承清晰，背景不乱继承 |

### 7.3 Basic

| ID | 状态 | 组件 | 需求 | 依赖 | 验收 |
| --- | --- | --- | --- | --- | --- |
| BASIC-001 | Todo | `basic.title` | title、subtitle、eyebrow、marker slots | FND-004 | 页面内标题块可复用 |
| BASIC-002 | Partial | `basic.text` | plain text、bullets、rich text、overflow、slot styles | FND-004/FND-015 | 常规文字块可控 |
| BASIC-003 | Partial | `basic.divider` | direction、label、thickness、dash、theme defaults | FND-016 | 分割线可作为信息结构 |
| BASIC-004 | Todo | `basic.shape` | 基于 rect/ellipse/polygon 的通用 shape | FND-016 | 快速画基础装饰图形 |
| BASIC-005 | Partial | `basic.card` | 决定与 `layout.card` 的边界 | FND-002 | 不与容器职责冲突 |

### 7.4 Layout 与 Container

| ID | 状态 | 组件 | 需求 | 依赖 | 验收 |
| --- | --- | --- | --- | --- | --- |
| LAYOUT-001 | Done | `layout.container` | children、padding、background、border、shadow、slot layout | FND-001/FND-002 | 可递归嵌套任意组件 |
| LAYOUT-002 | Partial | `layout.card` | plain/glass/warm/outline/dark/academic variants | FND-001/FND-002 | 同一 bare 组件放入不同 card 后风格明显不同 |
| LAYOUT-003 | Done | `layout.stack` | vertical/horizontal、gap、padding、children | FND-001 | 适合卡片内部排布 |
| LAYOUT-004 | Partial | `layout.grid` | recursive grid、invalid spans diagnostics、overlap diagnostics | FND-001/FND-012 | dashboard 页面不用手写坐标 |
| LAYOUT-005 | Todo | `layout.two_column` | ratio、gap、divider、left/right children | FND-001 | 双栏图文页快速生成 |
| LAYOUT-006 | Todo | `layout.row` | flex-like row、grow、shrink、basis | FND-001 | 横向布局可控 |
| LAYOUT-007 | Todo | `layout.column` | flex-like column、grow、shrink、basis | FND-001 | 纵向布局可控 |
| LAYOUT-008 | Todo | `layout.dock` | top/right/bottom/left/center | FND-001 | 页角徽标、注释、图例、水印 |
| LAYOUT-009 | Todo | `layout.flow` | wrap、chip、tag、keyword | FND-001 | 关键词、标签、图例项 |

### 7.5 Data

| ID | 状态 | 组件 | 需求 | 依赖 | 验收 |
| --- | --- | --- | --- | --- | --- |
| DATA-001 | Partial | `data.metric_card` | slot recipes、stacked/horizontal/hero/compact/bare variants | FND-001/FND-003/FND-004 | 内部元素位置不写死 |
| DATA-002 | Partial | `data.metric_cards` | columns、density、auto-fit、flow、responsive fallback | DATA-001/LAYOUT-004 | 2/3/4/6 张卡自动排布 |
| DATA-003 | Partial | `data.progress` | label/value/track/fill/marker slots，compact/list/dashboard variants | FND-004 | 项目进度页可用 |
| DATA-004 | Todo | `data.gantt` | tasks、start/end、progress、milestone、time scale | FND-001 | 项目计划页可用 |
| DATA-005 | Todo | `data.heatmap` | matrix、labels、scale、legend、cell styles | FND-001 | 数据报告和实验对比可用 |

### 7.6 Chart

| ID | 状态 | 组件 | 需求 | 依赖 | 验收 |
| --- | --- | --- | --- | --- | --- |
| CHART-001 | Partial | `chart.line` | native/shape variants、title/plot/axis/legend/annotation slots、数据校验 | FND-017 | 折线图专业可读 |
| CHART-002 | Partial | `chart.bar` | vertical/horizontal/grouped/stacked、value labels | FND-017 | 数据对比清晰 |
| CHART-003 | Partial | `chart.pie` | legend/label variants、percentage、palette mapping | FND-017 | 标签不拥挤 |
| CHART-004 | Partial | `chart.donut` | center label、ring thickness、legend、percentage labels | FND-017 | 占比总览可用 |
| CHART-005 | Planned | `chart.scatter` | x/y series、trendline、label | FND-017 | 实验结果散点图 |
| CHART-006 | Planned | `chart.radar` | dimensions、series、scale | FND-017 | 能力雷达图 |
| CHART-007 | Planned | `chart.waterfall` | start/change/end | FND-017 | 商业分析瀑布图 |

### 7.7 Table

| ID | 状态 | 组件 | 需求 | 依赖 | 验收 |
| --- | --- | --- | --- | --- | --- |
| TABLE-001 | Partial | `table.basic` | header/body/cell slots、column widths、alignment、compact/dense variants | FND-004/FND-013 | 学术/商业表格可读 |
| TABLE-002 | Partial | `table.comparison` | recommendation badge、scoring cells、winner highlighting、conclusion slot | TABLE-001 | 方案对比页专业 |
| TABLE-003 | Planned | `table.matrix` | row/col headers、highlight、legend | TABLE-001 | 热力矩阵和功能对比 |

### 7.8 Narrative 与 Diagram

| ID | 状态 | 组件 | 需求 | 依赖 | 验收 |
| --- | --- | --- | --- | --- | --- |
| NARR-001 | Partial | `narrative.timeline` | horizontal/vertical/milestone/status-card variants | FND-001/FND-004 | 阶段信息不单薄 |
| NARR-002 | Partial | `narrative.process_flow` | step slots、connector variants、compact/detail、output slot | FND-001/FND-004 | 项目流程页可直接用 |
| NARR-003 | Partial | `narrative.roadmap` | lane、quarter、milestone、dependency、progress | FND-001/FND-004 | 产品路线图可用 |
| NARR-004 | Todo | `narrative.swot` | quadrant、center label、evidence bullets | FND-001/FND-004 | 战略分析页可用 |
| NARR-005 | Todo | `narrative.problem_solution` | paired rows、arrow、impact | FND-001/FND-004 | 问题-对策页可用 |
| NARR-006 | Todo | `narrative.logic_pyramid` | levels、evidence、labels | FND-001/FND-004 | 答辩论证结构可用 |
| NARR-007 | Partial | `diagram.model` | nodes、edges、groups、layers、annotations | FND-001/FND-004 | 论文模型框架图可表达复杂结构 |

### 7.9 Media 与 Asset

| ID | 状态 | 组件 | 需求 | 依赖 | 验收 |
| --- | --- | --- | --- | --- | --- |
| MEDIA-001 | Partial | `media.image` | local path、URL、fit/cover/crop、caption、alt text | FND-020/FND-021 | 图片页和图文页稳定 |
| MEDIA-002 | Partial | `media.icon` | provider:name、size、color、stroke_width、rotate、flip、diagnostics | FND-022 | Lucide 等图标库可直接使用 |
| MEDIA-003 | Planned | `media.logo` | brand mark、theme-aware placement | FND-020 | 封面和母版可用 |

### 7.10 Theme 与 Style

| ID | 状态 | 模块 | 需求 | 验收 |
| --- | --- | --- | --- | --- |
| THEME-001 | Partial | Built-in themes | `tech_blue`、`academic_clean`、`business_navy`、`data_dashboard`、`medical_teal`、`dark_tech`、`claude_warm` | 同一 deck 可切换主题 |
| THEME-002 | Partial | Theme JSON | 单文件 JSON 和多文件主题目录 | 外部主题可加载 |
| THEME-003 | Todo | Component defaults | theme 中补齐 component defaults 和 slot styles | 不写 style 也统一 |
| THEME-004 | Todo | Theme personality | 不同主题不仅换颜色，还要换字体、间距、装饰、密度、卡片策略 | Claude/Academic/Data 风格明显不同 |
| STYLE-001 | Done | Selector | `type`、`#id`、`.class`、`type::slot` | 样式可定位到 slot |
| STYLE-002 | Partial | Cascade | theme/page/master/layout/component/slot/inline | 优先级清晰 |
| STYLE-003 | Partial | Token diagnostics | 未知 token warning | Agent 可修复 |

### 7.11 Agent、JSON DSL 与 Python API

| ID | 状态 | 模块 | 需求 | 验收 |
| --- | --- | --- | --- | --- |
| DSL-001 | Done | Namespace type | `chart.line`、`data.metric_card`、`layout.card` 等命名空间 type | parser 可路由 |
| DSL-002 | Partial | DSL 层级 | Level 1 语义组件、Level 2 容器组合、Level 3 primitive escape hatch | Agent 默认用 Level 1 |
| DSL-003 | Todo | Schema docs | 每个组件 JSON 字段完整说明 | 文档可独立使用 |
| API-001 | Partial | Python namespace API | `chart.line(...)`、`layout.grid(...)`、`data.metric_card(...)` | 与 JSON DSL 对齐 |
| AGENT-001 | Todo | Agent prompt guide | 生成流程、约束、反例、修复建议 | Agent 不直接写 python-pptx |

### 7.12 Export、Review 与 Documentation

| ID | 状态 | 模块 | 需求 | 验收 |
| --- | --- | --- | --- | --- |
| REVIEW-001 | Todo | Component screenshot page | 每个组件出现在 demo/review 页 | 有截图 |
| REVIEW-002 | Todo | Component visual checklist | 每个组件记录截图 review 状态、问题和修复记录 | 可追踪视觉质量 |
| REVIEW-003 | Todo | JSON example coverage | 每个组件有 minimal JSON example | 示例可运行 |
| REVIEW-004 | Todo | Python API example coverage | 每个组件有 namespace API example | 示例可运行 |
| REVIEW-005 | Todo | Theme coverage matrix | 至少 `tech_blue`、`claude_warm`、`data_dashboard` | 主题切换有对比 |
| DOC-001 | Todo | `docs/zh.md` | 更新中文用户文档 | 与真实 API 对齐 |
| DOC-002 | Todo | `docs/en.md` | 更新英文用户文档 | 与中文结构一致 |
| DOC-003 | Todo | Component gallery | 展示所有完成组件 | 可用于开源 README/demo |

## 8. 组件任务模板

每个组件任务必须包含以下交付物：

| 模块 | 必填内容 |
| --- | --- |
| 组件名称 | 例如 `data.metric_card` |
| 适用场景 | 指标概览、实验结果、运营周报等 |
| Props schema | 必填字段、可选字段、默认值、类型、校验 |
| Slots | `root`、`surface`、`label`、`value` 等稳定 slot |
| Variants | `default`、`compact`、`hero`、`bare` 等 |
| Layout recipes | 每个 variant 对应 slot layout recipe |
| Theme defaults | 颜色、字号、间距、圆角、阴影、slot style |
| Python API | namespace factory 示例 |
| JSON DSL | minimal example 和 realistic example |
| Diagnostics | 缺字段、内容过长、数据不匹配、尺寸不足 |
| Tests | props/parser/unit/render smoke |
| Screenshot review | 至少 tech_blue、claude_warm、data_dashboard 三种主题 |
| 文档 | 更新用户文档或组件 gallery |

## 9. JSON DSL 分层策略

### 9.1 Level 1：Agent 推荐写法

Agent 默认只写语义组件和少量布局。

```json
{
  "type": "data.metric_cards",
  "layout": {"mode": "grid", "col": 1, "span": 12, "row": 1},
  "props": {
    "cards": [
      {"label": "Accuracy", "value": "92.3%", "delta": "+3.1%"},
      {"label": "AUC", "value": "0.948", "delta": "+0.026"}
    ]
  }
}
```

### 9.2 Level 2：设计可控写法

开发者可以用容器和 bare 组件控制结构，但不手写每个 shape。

```json
{
  "type": "layout.card",
  "variant": "glass",
  "layout": {"mode": "grid", "col": 1, "span": 4, "row": 1},
  "props": {
    "padding": 0.18,
    "children": [
      {
        "type": "data.metric_card",
        "variant": "bare",
        "props": {"label": "Accuracy", "value": "92.3%", "delta": "+3.1%"}
      }
    ]
  }
}
```

### 9.3 Level 3：高级 escape hatch

高级用户可以直接写 primitive，用于特殊图形、论文模型结构图、视觉装饰。

```json
{
  "type": "primitive.line",
  "layout": {"mode": "absolute", "x": 1.0, "y": 2.0, "w": 3.0, "h": 0.1},
  "style": {"stroke": "{colors.primary}", "stroke_width": 1.2}
}
```

## 10. Theme 与样式策略

### 10.1 Theme 必须控制的内容

| 类别 | 示例 token | 说明 |
| --- | --- | --- |
| 颜色 | `colors.primary`、`colors.surface`、`colors.border` | 基础视觉语言 |
| 字体 | `fonts.family`、`fonts.title_font`、`fonts.caption_font` | 不同主题的气质差异 |
| 字号 | `h1_size`、`body_size`、`caption_size` | 信息层级 |
| 间距 | `page_margin`、`content_top`、`gutter`、`card_padding` | 页面呼吸感 |
| 圆角 | `radius.sm/md/lg` | 卡片和形状风格 |
| 阴影 | `shadow.card`、`shadow.opacity` | 轻重和层次 |
| 装饰 | accent bar、footer line、background pattern | 主题识别度 |
| 组件默认 | `components.data.metric_card.default` | 低门槛关键 |
| slot 样式 | `data.metric_card::value` | 精细控制 |
| chart palette | `chart_palette` | 图表一致性 |

### 10.2 主题性格要求

| 主题 | 应体现的性格 |
| --- | --- |
| `theme.tech_blue` | 科技蓝紫、白底卡片、轻阴影、现代汇报 |
| `theme.academic_clean` | 学术、严肃、高信息密度、弱装饰 |
| `theme.business_navy` | 稳重商业、深蓝金色点缀、适合方案对比 |
| `theme.data_dashboard` | 数据面板、卡片感强、图表色板丰富 |
| `theme.medical_teal` | 医疗科研、干净克制、蓝绿专业感 |
| `theme.dark_tech` | 发布会、深色背景、高对比、霓虹科技 |
| `theme.claude_warm` | 温暖纸感、强调字体气质、少卡片重排版 |

### 10.3 Style Cascade 目标顺序

```text
theme primitive defaults
  < theme component family defaults
  < theme component variant defaults
  < master/page/layout defaults
  < stylesheet type selector
  < stylesheet class selector
  < stylesheet id selector
  < stylesheet type::slot selector
  < block inline style
  < runtime state
```

## 11. 低门槛验收标准

| ID | 要求 | 验收标准 |
| --- | --- | --- |
| LOW-001 | 默认主题美观 | 不写任何样式时，页面仍有合理字号、间距、卡片、标题区和页脚。 |
| LOW-002 | 默认布局合理 | Agent 可以只使用 grid/stack/组件集合，不需要手写绝对坐标。 |
| LOW-003 | 组件默认不空 | 指标卡、时间轴、流程图、结论页等都有足够信息密度。 |
| LOW-004 | 内容过长可处理 | 文本默认 fit 或 truncate，并输出诊断。 |
| LOW-005 | 图表数据容错 | series 长度不一致、空数据、过多标签时有 warning 或 fallback。 |
| LOW-006 | 快速 demo | `uv run python examples/demo_deck.py` 能生成 demo.pptx 和截图。 |
| LOW-007 | 主题一键切换 | 同一份 JSON 可以切换至少 3 种主题并保持可用。 |
| LOW-008 | Agent 友好错误 | 错误包含 path 和 suggestion。 |

## 12. 高上限验收标准

| ID | 要求 | 验收标准 |
| --- | --- | --- |
| HIGH-001 | Primitive escape hatch | 高级用户可以直接用 primitive 组合特殊图形。 |
| HIGH-002 | 自定义组件 | 新增组件只需定义 props、slots、render_to_primitives、registry、tests、docs。 |
| HIGH-003 | 自定义主题 | 支持单文件 JSON、多文件主题目录、外部主题路径。 |
| HIGH-004 | 多种实现策略 | chart/table/icon/image 可选择 native、shape、raster 等 implementation。 |
| HIGH-005 | 深度样式覆盖 | 支持 type、class、id、type::slot 覆盖，并形成清晰 cascade。 |
| HIGH-006 | 复杂布局 | 支持 nested container、dock、overlay、flow、template 区域。 |
| HIGH-007 | 复杂图表 | 可扩展 scatter、heatmap、gantt、waterfall、radar。 |
| HIGH-008 | 视觉回归 | 每个完成组件都有截图 review，主题切换可生成对比图。 |
| HIGH-009 | 资产系统 | 图片、图标、外部资源有 registry、缓存、诊断、可替换策略。 |
| HIGH-010 | 可发布 API | 文档、示例、schema、测试覆盖足够支撑开源发布。 |

## 13. 下一步执行顺序

| 顺序 | 任务 | 原因 |
| --- | --- | --- |
| 1 | `NEXT-001 / FND-009` 拆分注册系统 | 继续扩大组件库前，先把 registry 边界理顺。 |
| 2 | `NEXT-002 / FND-010` props schema | 后续每个组件都要依赖 schema，否则验证会散落在 parser 中。 |
| 3 | `NEXT-003 / FND-011` SizeHint | 组件美观下限依赖尺寸诊断和自动降级。 |
| 4 | `NEXT-004 / FND-012` Layout diagnostics | Agent 生成布局时最容易出错，必须早做。 |
| 5 | `NEXT-005 / FND-013` 完整 style cascade | 主题、页面、组件、slot 样式需要统一优先级。 |
| 6 | `DATA-001` metric_card slot recipes | 用一个高频组件验证 schema、size、slot、theme。 |
| 7 | `LAYOUT-002` layout.card variants | 用容器证明不同主题可以有完全不同外观。 |
| 8 | `CHART-001` chart.line | 把图表能力拉到专业报告可用级别。 |
| 9 | `TABLE-001` table.basic | 学术答辩和商业汇报都高度依赖表格质量。 |
| 10 | `NARR-001` narrative.timeline | 验证 slot、connector、状态和信息密度。 |

## 14. 暂缓事项

| 暂缓项 | 原因 |
| --- | --- |
| 一次性重写所有组件 | 会造成大量视觉回归，不利于定位问题。 |
| 完整 CSS parser | 当前 `type::slot` 已能解决核心 slot 控制，完整后代选择器可后置。 |
| 先做很多主题 | 主题需要组件 slot 和 component defaults 支撑，否则只是换色。 |
| 复杂动画 | PPTX 可编辑和专业排版优先级更高。 |
| 大量图片化渲染 | 会降低 PPT 可编辑性，只适合作为特殊 fallback。 |

## 15. 维护规则

| 规则 | 说明 |
| --- | --- |
| 计划唯一入口 | 后续 design/plan 状态以本文档为准。 |
| 一项一项实现 | 每次完成一个明确任务，再更新状态。 |
| 每个组件独立任务 | 不允许“优化所有组件”这种模糊任务。 |
| 完成即更新 | 代码、测试、文档、截图 review 完成后立刻更新本文档。 |
| 测试优先 | 框架能力必须有单测；视觉能力必须有 render smoke 或截图 review。 |
| pre-v1 不背兼容包袱 | 内部 API 可调整，但 examples 和文档要同步。 |

## 16. 结论

下一阶段的核心不是继续堆组件数量，而是把 SlideForge 真正做成“低门槛、高上限”的 PPT UI 框架：

- 低门槛靠主题默认值、自动布局、组件 preset、诊断和 demo。
- 高上限靠 primitive、slot、container、registry、schema、style cascade 和 render variants。
- 每个组件都必须有 props、slots、variants、theme defaults、tests、examples、screenshot review。

推荐下一步实现：`NEXT-001 / FND-009`，拆分注册系统。
