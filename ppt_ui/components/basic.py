from __future__ import annotations

from dataclasses import dataclass

from ppt_ui.core.component import Component, RenderContext
from ppt_ui.core.layout import Box


@dataclass
class Title(Component):
    text: str
    subtitle: str = ""

    def render(self, ctx: RenderContext, box: Box) -> None:
        ctx.renderer.add_slide_title(ctx.slide, self.text, self.subtitle)


@dataclass
class TextBlock(Component):
    text: str

    def render(self, ctx: RenderContext, box: Box) -> None:
        ctx.renderer.text(ctx.slide, box, self.text, size=ctx.theme.fonts.body_size, color=ctx.theme.colors.text_secondary)


@dataclass
class Divider(Component):
    color: str | None = None

    def render(self, ctx: RenderContext, box: Box) -> None:
        ctx.renderer.line(ctx.slide, box.x, box.y + box.h / 2, box.x + box.w, box.y + box.h / 2, self.color or ctx.theme.colors.border)


@dataclass
class Icon(Component):
    icon_id: str
    label: str = ""

    def render(self, ctx: RenderContext, box: Box) -> None:
        # MVP fallback: the icon provider layer resolves SVG sources; rendering
        # those SVGs into PPT pictures will be wired behind this component later.
        ctx.renderer.circle(ctx.slide, box, ctx.theme.colors.primary_soft, line=ctx.theme.colors.border_light)
        text = self.label or self.icon_id[:2].upper()
        ctx.renderer.text(ctx.slide, box.inset(0.04, 0.02), text, size=8, color=ctx.theme.colors.primary, bold=True, align="center", valign="middle")
