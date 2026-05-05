from __future__ import annotations

from dataclasses import dataclass, field

from ppt_ui.core.component import RenderContext
from ppt_ui.core.layout import Box
from ppt_ui.core.slide import Slide


def _palette(ctx: RenderContext) -> list[str]:
    palette = [str(color).strip().lstrip("#") for color in getattr(ctx.theme, "chart_palette", []) if str(color).strip()]
    return palette or [ctx.theme.colors.primary, ctx.theme.colors.accent, ctx.theme.colors.success, ctx.theme.colors.warning]


@dataclass
class TimelineItem:
    label: str
    date: str = ""
    description: str = ""
    status: str = "normal"


@dataclass
class TimelineSlide(Slide):
    items: list[TimelineItem] = field(default_factory=list)
    subtitle: str = "用于展示项目阶段、研发计划与交付节奏"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, self.subtitle)
        area = Box(content.x + 0.10, content.y + 0.82, content.w - 0.20, 2.05)
        line_y = area.y + 0.13
        r.line(ctx.slide, area.x + 0.25, line_y, area.x + area.w - 0.25, line_y, color=ctx.theme.colors.border, width=1.0)
        slots = area.split_cols(max(1, len(self.items)), 0.16)
        for slot, item in zip(slots, self.items):
            r.add_status_timeline_node(
                ctx.slide,
                slot,
                label=item.label,
                date=item.date,
                description=item.description,
                status=item.status,
            )
        note_box = Box(content.x + 1.20, content.y + 3.62, content.w - 2.40, 0.50)
        r.add_card(ctx.slide, note_box, fill=ctx.theme.colors.surface_white, shadow=False)
        r.text(
            ctx.slide,
            note_box.inset(0.18, 0.14),
            "状态规范：已完成使用蓝色实心，当前阶段使用紫色高亮，未开始使用中性灰色。",
            size=ctx.theme.fonts.caption_size,
            color=ctx.theme.colors.text_secondary,
            align="center",
            valign="middle",
        )
        r.add_footer(ctx.slide)


@dataclass
class ProcessStep:
    title: str
    description: str = ""
    output: str = ""


@dataclass
class ProcessFlowSlide(Slide):
    steps: list[ProcessStep] = field(default_factory=list)

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, "从需求到交付的组件化生成流程")
        area = Box(content.x, content.y + 0.42, content.w, 2.08)
        slots = area.split_cols(max(1, len(self.steps)), 0.18)
        for idx, (slot, step) in enumerate(zip(slots, self.steps), start=1):
            r.add_process_step_card(
                ctx.slide,
                slot,
                index=idx,
                title=step.title,
                description=step.description,
                output=step.output,
            )
            if idx < len(slots):
                arrow_x = slot.x + slot.w + 0.035
                r.text(ctx.slide, Box(arrow_x, slot.y + 0.82, 0.11, 0.18), ">", size=11, color=ctx.theme.colors.text_tertiary, bold=True, align="center")

        chain = Box(content.x + 0.55, content.y + 3.25, content.w - 1.10, 0.74)
        r.add_card(ctx.slide, chain, fill=ctx.theme.colors.primary_soft, line=ctx.theme.colors.border_light, shadow=False)
        r.text(ctx.slide, Box(chain.x + 0.25, chain.y + 0.18, chain.w - 0.50, 0.22), "JSON DSL → Component Tree → Theme Tokens → PPTX Renderer → Editable Deck", size=ctx.theme.fonts.body_size, color=ctx.theme.colors.primary_dark, bold=True, align="center")
        r.text(ctx.slide, Box(chain.x + 0.25, chain.y + 0.46, chain.w - 0.50, 0.16), "Agent 不直接操作 shape，而是描述页面结构和组件数据。", size=ctx.theme.fonts.tiny_size, color=ctx.theme.colors.text_secondary, align="center")
        r.add_footer(ctx.slide)


@dataclass
class SWOTQuadrant:
    title: str
    subtitle: str = ""
    items: list[str] = field(default_factory=list)


@dataclass
class SWOTSlide(Slide):
    quadrants: list[SWOTQuadrant] = field(default_factory=list)
    subtitle: str = "适合战略分析、方案评估和复盘讨论"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, self.subtitle)
        area = Box(content.x + 0.85, content.y + 0.10, content.w - 1.70, 4.25)
        rows = area.split_rows(2, 0.18)
        cells = rows[0].split_cols(2, 0.18) + rows[1].split_cols(2, 0.18)
        fills = [ctx.theme.colors.primary_soft, ctx.theme.colors.accent_soft, ctx.theme.colors.success_soft, ctx.theme.colors.warning_soft]
        for idx, (cell, quadrant) in enumerate(zip(cells, self.quadrants)):
            r.add_card(ctx.slide, cell, fill=fills[idx % len(fills)], shadow=False)
            r.text(ctx.slide, Box(cell.x + 0.20, cell.y + 0.18, cell.w - 0.40, 0.22), quadrant.title, size=ctx.theme.fonts.body_size, color=ctx.theme.colors.primary_dark, bold=True)
            if quadrant.subtitle:
                r.text(ctx.slide, Box(cell.x + 0.20, cell.y + 0.44, cell.w - 0.40, 0.16), quadrant.subtitle, size=8, color=ctx.theme.colors.text_tertiary)
            r.bullet_list(ctx.slide, Box(cell.x + 0.22, cell.y + 0.76, cell.w - 0.44, cell.h - 0.92), quadrant.items, size=9)
        center = Box(area.x + area.w / 2 - 0.35, area.y + area.h / 2 - 0.35, 0.70, 0.70)
        r.circle(ctx.slide, center, ctx.theme.colors.primary, line="FFFFFF", line_width=1.0)
        r.text(ctx.slide, center.inset(0.04, 0.02), "SWOT", size=11, color="FFFFFF", bold=True, align="center", valign="middle")
        r.add_footer(ctx.slide)


@dataclass
class ProblemSolutionPair:
    problem: str
    solution: str


@dataclass
class ProblemSolutionSlide(Slide):
    pairs: list[ProblemSolutionPair] = field(default_factory=list)
    subtitle: str = "适合把关键问题映射到可执行对策"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, self.subtitle)
        panel = Box(content.x + 0.90, content.y + 0.10, content.w - 1.80, 4.35)
        r.add_card(ctx.slide, panel, fill=ctx.theme.colors.surface_white)
        left = Box(panel.x + 0.35, panel.y + 0.40, (panel.w - 0.95) / 2, panel.h - 0.80)
        right = Box(left.x + left.w + 0.25, left.y, left.w, left.h)
        r.rect(ctx.slide, Box(left.x, panel.y + 0.22, left.w, 0.28), ctx.theme.colors.primary, rounded=True)
        r.rect(ctx.slide, Box(right.x, panel.y + 0.22, right.w, 0.28), ctx.theme.colors.accent, rounded=True)
        r.text(ctx.slide, Box(left.x, panel.y + 0.28, left.w, 0.12), "关键问题", size=9, color="FFFFFF", bold=True, align="center")
        r.text(ctx.slide, Box(right.x, panel.y + 0.28, right.w, 0.12), "对应对策", size=9, color="FFFFFF", bold=True, align="center")
        rows = left.split_rows(max(1, len(self.pairs)), 0.12)
        for idx, (row, pair) in enumerate(zip(rows, self.pairs), start=1):
            r.add_card(ctx.slide, row, fill=ctx.theme.colors.gray_50, shadow=False)
            r.add_section_label(ctx.slide, f"{idx:02d}", Box(row.x + 0.10, row.y + 0.13, 0.30, 0.20))
            r.text(ctx.slide, Box(row.x + 0.52, row.y + 0.13, row.w - 0.62, 0.20), pair.problem, size=9, color=ctx.theme.colors.text_primary)
            target = Box(right.x, row.y, right.w, row.h)
            r.add_card(ctx.slide, target, fill=ctx.theme.colors.gray_50, shadow=False)
            r.text(ctx.slide, Box(target.x + 0.18, target.y + 0.13, target.w - 0.36, 0.22), pair.solution, size=9, color=ctx.theme.colors.text_primary, align="center")
            r.text(ctx.slide, Box(left.x + left.w + 0.07, row.y + 0.15, 0.12, 0.12), ">", size=10, color=ctx.theme.colors.primary, bold=True, align="center")
        r.add_footer(ctx.slide)


@dataclass
class RoadmapRow:
    label: str
    start: int
    end: int
    color: str = ""


@dataclass
class RoadmapSlide(Slide):
    periods: list[str] = field(default_factory=list)
    rows: list[RoadmapRow] = field(default_factory=list)
    subtitle: str = "适合展示路线图、能力建设节奏和季度规划"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, self.subtitle)
        panel = Box(content.x + 0.75, content.y + 0.10, content.w - 1.50, 4.25)
        r.add_card(ctx.slide, panel, fill=ctx.theme.colors.surface_white)
        inner = panel.inset(0.40, 0.42, 0.40, 0.45)
        label_w = 1.15
        grid = Box(inner.x + label_w, inner.y, inner.w - label_w, inner.h)
        period_count = max(1, len(self.periods))
        for idx, period in enumerate(self.periods):
            x = grid.x + idx * grid.w / period_count
            r.rect(ctx.slide, Box(x + 0.04, grid.y, grid.w / period_count - 0.08, 0.24), ctx.theme.colors.gray_50, line=ctx.theme.colors.border_light, rounded=True)
            r.text(ctx.slide, Box(x, grid.y + 0.06, grid.w / period_count, 0.10), period, size=8, color=ctx.theme.colors.primary_dark, bold=True, align="center")
        lanes = Box(inner.x, inner.y + 0.55, inner.w, inner.h - 0.55).split_rows(max(1, len(self.rows)), 0.16)
        colors = _palette(ctx)
        for idx, (lane, row) in enumerate(zip(lanes, self.rows)):
            r.text(ctx.slide, Box(lane.x, lane.y + 0.08, label_w - 0.12, 0.16), row.label, size=8, color=ctx.theme.colors.text_primary, align="right")
            r.line(ctx.slide, grid.x, lane.y + 0.16, grid.x + grid.w, lane.y + 0.16, ctx.theme.colors.border_light, width=0.6)
            x = grid.x + row.start * grid.w / period_count
            w = max(0.14, (row.end - row.start) * grid.w / period_count)
            r.rect(ctx.slide, Box(x, lane.y + 0.08, w, 0.12), row.color or colors[idx % len(colors)], rounded=True)
        r.add_footer(ctx.slide)


@dataclass
class PyramidLevel:
    label: str
    note: str = ""


@dataclass
class LogicPyramidSlide(Slide):
    levels: list[PyramidLevel] = field(default_factory=list)
    side_notes: list[str] = field(default_factory=list)
    subtitle: str = "适合展示结论、论点、论据和支撑材料"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, self.subtitle)
        panel = Box(content.x + 1.10, content.y + 0.05, content.w - 2.20, 4.40)
        r.add_card(ctx.slide, panel, fill=ctx.theme.colors.surface_white)
        base_x = panel.x + 1.60
        base_y = panel.y + 0.55
        widths = [2.15, 3.35, 4.55, 5.75]
        height = 0.58
        fills = [ctx.theme.colors.accent, "8B5CF6", "6366F1", ctx.theme.colors.primary]
        count = max(1, len(self.levels))
        for idx, level in enumerate(self.levels[:4]):
            w = widths[idx]
            x = base_x + (widths[-1] - w) / 2
            y = base_y + idx * (height + 0.06)
            r.rect(ctx.slide, Box(x, y, w, height), fills[idx % len(fills)], rounded=True)
            r.text(ctx.slide, Box(x + 0.10, y + 0.18, w - 0.20, 0.16), level.label, size=10, color="FFFFFF", bold=True, align="center")
        for idx, note in enumerate(self.side_notes):
            y = base_y + idx * (height + 0.06) + height / 2
            r.line(ctx.slide, base_x + widths[-1] + 0.25, y, base_x + widths[-1] + 1.15, y, ctx.theme.colors.border, width=0.7)
            r.text(ctx.slide, Box(base_x + widths[-1] + 1.25, y - 0.08, 1.25, 0.16), note, size=9, color=ctx.theme.colors.text_secondary)
        r.add_footer(ctx.slide)


@dataclass
class RiskItem:
    category: str
    impact: str
    suggestion: str


@dataclass
class RiskTableSlide(Slide):
    risks: list[RiskItem] = field(default_factory=list)
    subtitle: str = "适合展示风险识别、影响程度和应对建议"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, self.subtitle)
        rows = [[item.category, item.impact, item.suggestion] for item in self.risks]
        r.add_table(ctx.slide, Box(content.x + 0.95, content.y + 0.10, content.w - 1.90, 4.10), ["风险项", "影响程度", "应对建议"], rows)
        r.add_footer(ctx.slide)


@dataclass
class MilestoneSlide(Slide):
    items: list[TimelineItem] = field(default_factory=list)
    subtitle: str = "适合展示关键里程碑和阶段验收点"

    def render(self, ctx: RenderContext, box: Box) -> None:
        TimelineSlide(title=self.title, subtitle=self.subtitle, items=self.items).render(ctx, box)


@dataclass
class RelationRow:
    action: str
    owner: str
    priority: str
    due: str
    progress: str
    status: str


@dataclass
class RelationTableSlide(Slide):
    rows: list[RelationRow] = field(default_factory=list)
    subtitle: str = "适合展示行动项、负责人、优先级、进度与状态"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, self.subtitle)
        table_rows = [[row.action, row.owner, row.priority, row.due, row.progress, row.status] for row in self.rows]
        r.add_table(ctx.slide, Box(content.x + 0.45, content.y + 0.10, content.w - 0.90, 4.15), ["行动项", "负责人", "优先级", "计划完成时间", "当前进度", "状态"], table_rows)
        r.add_footer(ctx.slide)


@dataclass
class StoryStep:
    title: str
    description: str
    icon: str = ""


@dataclass
class StoryStructureSlide(Slide):
    steps: list[StoryStep] = field(default_factory=list)
    subtitle: str = "适合搭建背景、问题、方法、结果、结论的叙事结构"

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        content = r.add_slide_title(ctx.slide, self.title, self.subtitle)
        panel = Box(content.x + 3.00, content.y + 0.02, content.w - 6.00, 4.55)
        rows = panel.split_rows(max(1, len(self.steps)), 0.16)
        for idx, (row, step) in enumerate(zip(rows, self.steps)):
            r.add_card(ctx.slide, row, fill=ctx.theme.colors.surface_white if idx % 2 else ctx.theme.colors.gray_50, shadow=False)
            r.circle(ctx.slide, Box(row.x + 0.20, row.y + 0.16, 0.32, 0.32), ctx.theme.colors.primary_soft, line=ctx.theme.colors.border_light)
            r.text(ctx.slide, Box(row.x + 0.25, row.y + 0.24, 0.22, 0.10), step.icon or str(idx + 1), size=8, color=ctx.theme.colors.primary, bold=True, align="center")
            r.text(ctx.slide, Box(row.x + 0.72, row.y + 0.14, row.w - 0.92, 0.18), step.title, size=ctx.theme.fonts.body_size, color=ctx.theme.colors.text_primary, bold=True)
            r.text(ctx.slide, Box(row.x + 0.72, row.y + 0.38, row.w - 0.92, 0.14), step.description, size=8, color=ctx.theme.colors.text_secondary)
            if idx < len(rows) - 1:
                r.text(ctx.slide, Box(row.x + row.w / 2 - 0.05, row.y + row.h + 0.03, 0.10, 0.10), "↓", size=8, color=ctx.theme.colors.text_tertiary, align="center")
        r.add_footer(ctx.slide)
