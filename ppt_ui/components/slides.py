from __future__ import annotations

from dataclasses import dataclass, field

from ppt_ui.core.component import RenderContext
from ppt_ui.core.layout import Box
from ppt_ui.core.slide import Slide


@dataclass
class TitleSlide(Slide):
    subtitle: str = ""
    presenter: str = ""
    date: str = ""
    logo: str = "YOUR LOGO"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        margin = ctx.theme.spacing.page_margin
        r.add_accent_bar(ctx.slide, x=0.30, y=0.46, h=0.72)
        r.text(ctx.slide, Box(margin, 0.52, 2.0, 0.22), self.logo, size=9, color=ctx.theme.colors.primary, bold=True)
        r.text(ctx.slide, Box(margin, 1.48, 6.7, 0.68), self.title, size=ctx.theme.fonts.title_size, bold=True)
        r.text(ctx.slide, Box(margin, 2.22, 6.3, 0.34), self.subtitle, size=ctx.theme.fonts.subtitle_size, color=ctx.theme.colors.text_secondary)
        if self.presenter or self.date:
            meta = "  |  ".join([v for v in [self.presenter, self.date] if v])
            r.pill(ctx.slide, Box(margin, 2.88, 2.26, 0.30), meta, fill=ctx.theme.colors.primary_soft, color=ctx.theme.colors.primary_dark)

        panel = Box(8.10, 1.08, 4.05, 3.80)
        r.add_card(ctx.slide, panel, fill=ctx.theme.colors.surface_white)
        r.circle(ctx.slide, Box(panel.x + 2.22, panel.y + 0.38, 1.18, 1.18), ctx.theme.colors.accent_soft, line=ctx.theme.colors.border_light)
        r.circle(ctx.slide, Box(panel.x + 1.50, panel.y + 1.06, 1.72, 1.72), ctx.theme.colors.primary_soft, line=ctx.theme.colors.border_light)
        r.circle(ctx.slide, Box(panel.x + 2.58, panel.y + 2.20, 0.86, 0.86), ctx.theme.colors.gray_50, line=ctx.theme.colors.border_light)
        tags = ["JSON DSL", "Theme Tokens", "Reusable Components", "PPTX Renderer"]
        for idx, tag in enumerate(tags):
            y = panel.y + 0.46 + idx * 0.68
            r.rect(ctx.slide, Box(panel.x + 0.35, y, 1.85, 0.34), ctx.theme.colors.surface, line=ctx.theme.colors.border_light, rounded=True)
            r.text(ctx.slide, Box(panel.x + 0.48, y + 0.07, 1.60, 0.15), tag, size=8, color=ctx.theme.colors.primary_dark, bold=True)

        r.text(ctx.slide, Box(margin, 5.78, 6.4, 0.32), "Agent 描述结构，SlideForge 负责组件化渲染与视觉一致性。", size=ctx.theme.fonts.body_size, color=ctx.theme.colors.text_secondary)
        r.add_footer(ctx.slide)


@dataclass
class SectionSlide(Slide):
    number: str = "01"
    subtitle: str = ""
    keywords: list[str] = field(default_factory=list)

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        margin = ctx.theme.spacing.page_margin
        r.add_accent_bar(ctx.slide, x=0.30, y=0.56, h=0.78)
        r.text(ctx.slide, Box(margin, 0.68, 2.1, 0.24), f"SECTION {self.number}", size=10, color=ctx.theme.colors.primary, bold=True)
        r.text(ctx.slide, Box(margin, 1.58, 2.55, 0.86), self.number, size=ctx.theme.fonts.display_size, color=ctx.theme.colors.primary, bold=True)
        r.text(ctx.slide, Box(3.15, 1.62, 7.3, 0.48), self.title, size=ctx.theme.fonts.h1_size, bold=True)
        r.text(ctx.slide, Box(3.16, 2.17, 6.9, 0.30), self.subtitle, size=ctx.theme.fonts.subtitle_size, color=ctx.theme.colors.text_secondary)

        keyword_area = Box(3.15, 3.02, 7.9, 1.25)
        r.text(ctx.slide, Box(keyword_area.x, keyword_area.y - 0.32, 1.5, 0.20), "本章关键词", size=10, color=ctx.theme.colors.text_tertiary, bold=True)
        pills = keyword_area.split_cols(max(1, len(self.keywords)), 0.12)
        for pill_box, keyword in zip(pills, self.keywords):
            r.rect(ctx.slide, pill_box.top(0.42), ctx.theme.colors.surface, line=ctx.theme.colors.border, rounded=True)
            r.text(ctx.slide, pill_box.top(0.42).inset(0.05, 0.0), keyword, size=9, color=ctx.theme.colors.primary_dark, bold=True, align="center", valign="middle")

        guide = Box(3.15, 4.28, 7.90, 0.88)
        r.add_card(ctx.slide, guide, fill=ctx.theme.colors.surface_white, shadow=False)
        r.text(ctx.slide, Box(guide.x + 0.22, guide.y + 0.16, 1.20, 0.18), "布局原则", size=9, color=ctx.theme.colors.primary, bold=True)
        r.text(ctx.slide, Box(guide.x + 1.35, guide.y + 0.16, guide.w - 1.55, 0.18), "统一标题区、内容起点、卡片间距和轻量页脚，让组件组合后仍像完整汇报页面。", size=9, color=ctx.theme.colors.text_secondary)
        r.text(ctx.slide, Box(guide.x + 1.35, guide.y + 0.48, guide.w - 1.55, 0.16), "后续可按 component family + variant 扩展更多图表、布局和主题表达。", size=8, color=ctx.theme.colors.text_tertiary)

        progress = Box(margin, 5.78, 4.20, 0.22)
        r.line(ctx.slide, progress.x, progress.y + 0.10, progress.x + progress.w, progress.y + 0.10, ctx.theme.colors.border, width=1.0)
        for idx in range(5):
            x = progress.x + idx * (progress.w / 4)
            color = ctx.theme.colors.primary if idx <= 1 else ctx.theme.colors.gray_200
            r.circle(ctx.slide, Box(x - 0.045, progress.y + 0.055, 0.09, 0.09), color)
        r.add_footer(ctx.slide)


@dataclass
class TwoColumnSlide(Slide):
    left_title: str = ""
    left_items: list[str] = field(default_factory=list)
    right_title: str = ""
    right_items: list[str] = field(default_factory=list)

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, "从页面语义到可编辑 PPTX 的组件化渲染链路")
        left, right = Box(content.x, content.y + 0.10, content.w, 4.20).split_cols(2, ctx.theme.spacing.gutter)
        self._column(ctx, left, self.left_title, self.left_items, ctx.theme.colors.primary_soft, "01")
        self._column(ctx, right, self.right_title, self.right_items, ctx.theme.colors.accent_soft, "02")
        r.add_footer(ctx.slide)

    def _column(self, ctx: RenderContext, box: Box, title: str, items: list[str], fill: str, index: str) -> None:
        r = ctx.renderer
        r.add_card(ctx.slide, box, fill=fill)
        inner = box.inset(0.28, 0.26)
        r.add_section_label(ctx.slide, index, Box(inner.x, inner.y, 0.42, 0.26))
        r.text(ctx.slide, Box(inner.x + 0.55, inner.y + 0.01, inner.w - 0.55, 0.28), title, size=ctx.theme.fonts.h2_size, bold=True)
        r.line(ctx.slide, inner.x, inner.y + 0.55, inner.x + inner.w, inner.y + 0.55, ctx.theme.colors.border, width=0.8)
        r.bullet_list(ctx.slide, Box(inner.x, inner.y + 0.83, inner.w, 2.65), items, size=ctx.theme.fonts.body_size)


@dataclass
class ContentsItem:
    number: str
    title: str


@dataclass
class ContentsSlide(Slide):
    items: list[ContentsItem] = field(default_factory=list)
    subtitle: str = "CONTENTS"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title or "目录", self.subtitle)
        panel = Box(content.x + 1.15, content.y + 0.25, content.w - 2.30, 3.90)
        r.add_card(ctx.slide, panel, fill=ctx.theme.colors.surface_white)
        rows = panel.inset(0.45, 0.48, 0.45, 0.48).split_rows(max(1, len(self.items)), 0.12)
        for row, item in zip(rows, self.items):
            r.add_section_label(ctx.slide, item.number, Box(row.x, row.y + 0.05, 0.38, 0.24))
            r.rect(ctx.slide, Box(row.x + 0.55, row.y, row.w - 0.55, row.h), ctx.theme.colors.gray_50, line=ctx.theme.colors.border_light, rounded=True)
            r.text(ctx.slide, Box(row.x + 0.72, row.y + 0.11, row.w - 0.85, 0.14), item.title, size=ctx.theme.fonts.caption_size, color=ctx.theme.colors.text_primary)
        r.add_footer(ctx.slide)


@dataclass
class ImageTextSlide(Slide):
    image_label: str = "Image"
    body: str = ""
    bullets: list[str] = field(default_factory=list)
    image_side: str = "right"
    subtitle: str = "适合说明型页面、方案页和图文混排内容"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, self.subtitle)
        left, right = Box(content.x + 0.40, content.y + 0.05, content.w - 0.80, 4.35).split_cols(2, 0.35)
        text_box, image_box = (right, left) if self.image_side == "left" else (left, right)
        r.add_card(ctx.slide, image_box, fill=ctx.theme.colors.primary_soft, shadow=False)
        r.circle(ctx.slide, Box(image_box.x + image_box.w - 1.35, image_box.y + 0.35, 0.82, 0.82), ctx.theme.colors.accent_soft, line=ctx.theme.colors.border_light)
        r.text(ctx.slide, image_box.inset(0.30, 1.55), self.image_label, size=ctx.theme.fonts.h2_size, color=ctx.theme.colors.primary_dark, bold=True, align="center", valign="middle")
        r.add_card(ctx.slide, text_box, fill=ctx.theme.colors.surface_white)
        r.text(ctx.slide, Box(text_box.x + 0.35, text_box.y + 0.35, text_box.w - 0.70, 0.38), self.body, size=ctx.theme.fonts.body_size, color=ctx.theme.colors.text_secondary)
        r.bullet_list(ctx.slide, Box(text_box.x + 0.38, text_box.y + 1.15, text_box.w - 0.76, 2.10), self.bullets, size=ctx.theme.fonts.body_size)
        r.add_footer(ctx.slide)


@dataclass
class InfoCard:
    title: str
    description: str
    icon: str = ""


@dataclass
class ThreeInfoCardsSlide(Slide):
    cards: list[InfoCard] = field(default_factory=list)
    subtitle: str = "适合展示三类能力、价值或模块说明"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, self.subtitle)
        cards = Box(content.x + 0.65, content.y + 0.55, content.w - 1.30, 3.20).split_cols(max(1, len(self.cards)), 0.22)
        colors = [ctx.theme.colors.primary_soft, ctx.theme.colors.accent_soft, ctx.theme.colors.success_soft]
        for idx, (area, card) in enumerate(zip(cards, self.cards)):
            r.add_card(ctx.slide, area, fill=colors[idx % len(colors)], shadow=False)
            r.circle(ctx.slide, Box(area.x + area.w / 2 - 0.22, area.y + 0.48, 0.44, 0.44), "FFFFFF", line=ctx.theme.colors.border_light)
            r.text(ctx.slide, Box(area.x + area.w / 2 - 0.16, area.y + 0.60, 0.32, 0.10), card.icon or f"{idx + 1}", size=8, color=ctx.theme.colors.primary, bold=True, align="center")
            r.text(ctx.slide, Box(area.x + 0.22, area.y + 1.20, area.w - 0.44, 0.22), card.title, size=ctx.theme.fonts.body_size, color=ctx.theme.colors.text_primary, bold=True, align="center")
            r.text(ctx.slide, Box(area.x + 0.28, area.y + 1.62, area.w - 0.56, 0.72), card.description, size=9, color=ctx.theme.colors.text_secondary, align="center")
        r.add_footer(ctx.slide)


@dataclass
class GridItem:
    title: str
    description: str = ""
    icon: str = ""


@dataclass
class GridSlide(Slide):
    items: list[GridItem] = field(default_factory=list)
    columns: int = 3
    subtitle: str = "适合展示网格化模块、能力矩阵和功能入口"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, self.subtitle)
        columns = max(1, self.columns)
        rows_count = max(1, (len(self.items) + columns - 1) // columns)
        area = Box(content.x + 0.60, content.y + 0.10, content.w - 1.20, 4.35)
        rows = area.split_rows(rows_count, 0.18)
        cells = [cell for row in rows for cell in row.split_cols(columns, 0.18)]
        for idx, (cell, item) in enumerate(zip(cells, self.items)):
            fill = ctx.theme.colors.primary_soft if idx % 2 == 0 else ctx.theme.colors.accent_soft
            r.add_card(ctx.slide, cell, fill=fill, shadow=False)
            r.circle(ctx.slide, Box(cell.x + 0.22, cell.y + 0.22, 0.34, 0.34), "FFFFFF", line=ctx.theme.colors.border_light)
            r.text(ctx.slide, Box(cell.x + 0.28, cell.y + 0.31, 0.22, 0.10), item.icon or str(idx + 1), size=7, color=ctx.theme.colors.primary, bold=True, align="center")
            r.text(ctx.slide, Box(cell.x + 0.70, cell.y + 0.23, cell.w - 0.92, 0.20), item.title, size=ctx.theme.fonts.body_size, color=ctx.theme.colors.text_primary, bold=True)
            r.text(ctx.slide, Box(cell.x + 0.24, cell.y + 0.72, cell.w - 0.48, 0.38), item.description, size=8, color=ctx.theme.colors.text_secondary)
        r.add_footer(ctx.slide)


@dataclass
class QuoteSlide(Slide):
    quote: str = ""
    source: str = ""
    subtitle: str = "适合观点强调、专家引用和章节过渡"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, self.subtitle)
        panel = Box(content.x + 2.10, content.y + 0.60, content.w - 4.20, 2.85)
        r.add_card(ctx.slide, panel, fill=ctx.theme.colors.gray_50, shadow=False)
        r.text(ctx.slide, Box(panel.x + 0.35, panel.y + 0.34, 0.45, 0.38), "“", size=40, color=ctx.theme.colors.accent, bold=True)
        r.text(ctx.slide, Box(panel.x + 0.72, panel.y + 0.92, panel.w - 1.44, 0.70), self.quote, size=ctx.theme.fonts.h2_size, color=ctx.theme.colors.text_primary, align="center", valign="middle")
        if self.source:
            r.text(ctx.slide, Box(panel.x + 0.72, panel.y + 2.05, panel.w - 1.44, 0.20), f"—— {self.source}", size=ctx.theme.fonts.caption_size, color=ctx.theme.colors.text_secondary, align="right")
        r.add_footer(ctx.slide)


@dataclass
class HeaderFooterSlide(Slide):
    section: str = "01"
    body: str = "页面内容区域"
    source: str = "数据来源：公司内部数据 / 公开资料整理"
    page: str = "/ 12"
    subtitle: str = "适合展示统一页眉、页脚和正文占位规范"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, self.subtitle, section=self.section)
        panel = Box(content.x + 1.35, content.y + 0.10, content.w - 2.70, 3.75)
        r.add_card(ctx.slide, panel, fill=ctx.theme.colors.surface_white, shadow=False)
        r.text(ctx.slide, Box(panel.x, panel.y + 1.42, panel.w, 0.22), self.body, size=ctx.theme.fonts.body_size, color=ctx.theme.colors.text_secondary, align="center")
        r.text(ctx.slide, Box(panel.x + 0.20, panel.y + panel.h - 0.32, panel.w - 0.40, 0.14), self.source, size=ctx.theme.fonts.tiny_size, color=ctx.theme.colors.text_tertiary)
        r.text(ctx.slide, Box(panel.x + panel.w - 0.55, panel.y + panel.h - 0.32, 0.40, 0.14), self.page, size=ctx.theme.fonts.tiny_size, color=ctx.theme.colors.text_tertiary, align="right")
        r.add_footer(ctx.slide)


@dataclass
class DesignSpecSlide(Slide):
    specs: list[str] = field(default_factory=list)
    subtitle: str = "适合展示主题 token、组件规范和设计系统规则"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, self.subtitle)
        panel = Box(content.x + 0.70, content.y + 0.05, content.w - 1.40, 4.45)
        r.add_card(ctx.slide, panel, fill=ctx.theme.colors.surface_white)
        grid = panel.inset(0.35, 0.40, 0.35, 0.35).split_rows(2, 0.22)
        cells = grid[0].split_cols(3, 0.18) + grid[1].split_cols(3, 0.18)
        for idx, (cell, spec) in enumerate(zip(cells, self.specs)):
            fill = ctx.theme.colors.primary_soft if idx % 2 == 0 else ctx.theme.colors.accent_soft
            r.rect(ctx.slide, cell, fill, line=ctx.theme.colors.border_light, rounded=True)
            r.text(ctx.slide, cell.inset(0.08, 0.0), spec, size=ctx.theme.fonts.body_size, color=ctx.theme.colors.primary_dark, bold=True, align="center", valign="middle")
        r.add_footer(ctx.slide)


@dataclass
class ConclusionPoint:
    title: str
    description: str


@dataclass
class ConclusionSlide(Slide):
    points: list[ConclusionPoint] = field(default_factory=list)
    closing: str = "携手共进，共创未来！"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        panel = Box(box.x + 0.35, 1.05, box.w - 0.70, 5.15)
        r.add_card(ctx.slide, panel, fill=ctx.theme.colors.primary_soft, line=ctx.theme.colors.border, shadow=True)
        r.rect(ctx.slide, Box(panel.x + panel.w * 0.58, panel.y, panel.w * 0.42, panel.h), ctx.theme.colors.accent_soft, rounded=True)
        r.rect(ctx.slide, Box(panel.x + 0.35, panel.y + 0.36, 1.25, 0.045), ctx.theme.colors.primary, rounded=True)
        r.rect(ctx.slide, Box(panel.x + 1.60, panel.y + 0.36, 0.70, 0.045), ctx.theme.colors.accent, rounded=True)
        r.text(ctx.slide, Box(panel.x + 0.45, panel.y + 0.64, panel.w - 0.90, 0.42), self.title or "结论与展望", size=ctx.theme.fonts.h1_size, color=ctx.theme.colors.text_primary, bold=True)
        r.text(
            ctx.slide,
            Box(panel.x + 0.45, panel.y + 1.12, panel.w - 0.90, 0.26),
            "以组件、主题和 DSL 为核心，让 Agent 生成的每一页都更稳定、更一致、更可编辑。",
            size=ctx.theme.fonts.body_size,
            color=ctx.theme.colors.text_secondary,
        )

        cards = Box(panel.x + 0.45, panel.y + 1.95, panel.w - 0.90, 1.48).split_cols(max(1, len(self.points)), 0.18)
        for area, point in zip(cards, self.points):
            r.add_card(ctx.slide, area, fill="FFFFFF", line="FFFFFF", shadow=False)
            r.text(ctx.slide, Box(area.x + 0.18, area.y + 0.18, area.w - 0.36, 0.26), point.title, size=ctx.theme.fonts.body_size, color=ctx.theme.colors.primary_dark, bold=True, align="center")
            r.text(ctx.slide, Box(area.x + 0.20, area.y + 0.58, area.w - 0.40, 0.70), point.description, size=9, color=ctx.theme.colors.text_secondary, align="center")

        r.rect(ctx.slide, Box(panel.x + 3.55, panel.y + 4.02, panel.w - 7.10, 0.48), ctx.theme.colors.primary, line=ctx.theme.colors.primary, rounded=True)
        r.text(ctx.slide, Box(panel.x + 3.55, panel.y + 4.15, panel.w - 7.10, 0.18), self.closing, size=ctx.theme.fonts.body_size, color="FFFFFF", bold=True, align="center", valign="middle")
        r.text(ctx.slide, Box(panel.x, panel.y + 4.68, panel.w, 0.18), "SlideForge · reusable PPT UI components for agents", size=ctx.theme.fonts.tiny_size, color=ctx.theme.colors.text_tertiary, align="center")


@dataclass
class QASlide(Slide):
    subtitle: str = "感谢聆听，期待交流"
    project: str = "SlideForge"
    description: str = "欢迎交流组件设计、主题扩展与 Agent 生成链路"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        r.add_accent_bar(ctx.slide, x=0.30, y=0.54, h=0.72)
        r.circle(ctx.slide, Box(9.55, 1.10, 1.05, 1.05), ctx.theme.colors.primary_soft, line=ctx.theme.colors.border_light)
        r.circle(ctx.slide, Box(10.30, 4.65, 0.72, 0.72), ctx.theme.colors.accent_soft, line=ctx.theme.colors.border_light)
        r.text(ctx.slide, Box(box.x, 1.76, box.w, 0.34), self.project, size=ctx.theme.fonts.h2_size, color=ctx.theme.colors.text_secondary, bold=True, align="center")
        r.text(ctx.slide, Box(box.x, 2.25, box.w, 0.82), self.title or "Q&A", size=54, color=ctx.theme.colors.primary, bold=True, align="center")
        r.text(ctx.slide, Box(box.x, 3.18, box.w, 0.30), self.subtitle, size=ctx.theme.fonts.subtitle_size, color=ctx.theme.colors.text_primary, align="center")
        r.add_card(ctx.slide, Box(3.25, 4.10, 6.80, 0.82), fill=ctx.theme.colors.surface_white)
        r.text(ctx.slide, Box(3.55, 4.35, 6.20, 0.22), self.description, size=ctx.theme.fonts.body_size, color=ctx.theme.colors.text_secondary, align="center")
        r.add_footer(ctx.slide)
