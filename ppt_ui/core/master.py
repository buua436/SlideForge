from __future__ import annotations

from copy import deepcopy
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ppt_ui.core.component import RenderContext
from ppt_ui.core.layout import Box, PageLayout, resolve_block_box
from ppt_ui.core.page import Page
from ppt_ui.primitives import IconPrimitive, ImagePrimitive, Line, Rect, Text, normalize_class_names
from ppt_ui.styles import Style


def deep_merge(*values: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge dictionaries without mutating inputs."""

    result: dict[str, Any] = {}
    for value in values:
        for key, item in value.items():
            if isinstance(item, dict) and isinstance(result.get(key), dict):
                result[key] = deep_merge(result[key], item)
            else:
                result[key] = deepcopy(item)
    return result


def chrome_visible(chrome: dict[str, Any], key: str, default: bool = True) -> bool:
    value = chrome.get(key, {})
    if isinstance(value, dict):
        return bool(value.get("visible", default))
    return default


@dataclass
class SlideMaster:
    """Deck-level page rules for background and common chrome."""

    name: str
    chrome: dict[str, Any] = field(default_factory=dict)
    background: dict[str, Any] = field(default_factory=dict)
    back_primitives: list[dict[str, Any]] = field(default_factory=list)
    fore_primitives: list[dict[str, Any]] = field(default_factory=list)

    def effective_chrome(self, page: Page, layout: PageLayout) -> dict[str, Any]:
        layout_chrome = {
            "title": {"visible": True},
            "subtitle": {"visible": True},
        }
        override_chrome = dict(page.master_overrides.get("chrome", {}))
        return deep_merge(self.chrome, layout_chrome, override_chrome, page.chrome)

    def render_background(self, ctx: RenderContext, page: Page) -> None:
        if not self.background:
            ctx.renderer.background(ctx.slide)
            return
        fill = str(self.background.get("fill", ctx.theme.colors.background))
        ctx.slide.background.fill.solid()
        ctx.slide.background.fill.fore_color.rgb = ctx.renderer.rgb(fill)

    def render_back_chrome(self, ctx: RenderContext, page: Page, layout: PageLayout, page_index: int, total_pages: int) -> None:
        chrome = self.effective_chrome(page, layout)
        r = ctx.renderer

        self._render_primitive_specs(ctx, page, layout, page_index, total_pages, self.back_primitives)

        if chrome_visible(chrome, "accent_bar", self.name != "blank"):
            r.add_accent_bar(ctx.slide)

        logo = chrome.get("logo", {})
        if isinstance(logo, dict) and logo.get("visible", bool(logo.get("text"))):
            text = str(logo.get("text", ""))
            if text:
                r.text(ctx.slide, Box(ctx.theme.spacing.page_margin, 0.30, 1.8, 0.18), text, size=8, color=ctx.theme.colors.primary, bold=True)

        if page.type == "page.section":
            number = str(page.metadata.get("number", page.chrome.get("section", "01")))
            r.text(ctx.slide, Box(ctx.theme.spacing.page_margin, 0.70, 1.2, 0.18), f"SECTION {number}", size=9, color=ctx.theme.colors.primary, bold=True)
            r.text(ctx.slide, Box(ctx.theme.spacing.page_margin, 1.50, 2.2, 0.78), number, size=ctx.theme.fonts.display_size, color=ctx.theme.colors.primary, bold=True)

        if page.title and layout.title_box and chrome_visible(chrome, "title"):
            size = ctx.theme.fonts.title_size if page.type == "page.cover" else ctx.theme.fonts.h1_size
            align = "center" if page.type in {"page.qa", "page.closing"} else "left"
            title_font = getattr(ctx.theme.fonts, "title_font", "") or None
            r.text(ctx.slide, layout.title_box, page.title, size=size, color=ctx.theme.colors.text_primary, bold=True, align=align, font=title_font)

        if page.subtitle and layout.subtitle_box and chrome_visible(chrome, "subtitle"):
            align = "center" if page.type in {"page.qa", "page.closing"} else "left"
            r.text(ctx.slide, layout.subtitle_box, page.subtitle, size=ctx.theme.fonts.subtitle_size, color=ctx.theme.colors.text_secondary, align=align)

    def render_fore_chrome(self, ctx: RenderContext, page: Page, layout: PageLayout, page_index: int, total_pages: int) -> None:
        chrome = self.effective_chrome(page, layout)
        r = ctx.renderer

        footer = chrome.get("footer", {})
        if isinstance(footer, dict) and footer.get("visible", self.name != "blank") and layout.footer_box:
            text = str(footer.get("text", "SlideForge - Agent-driven PPT UI Framework"))
            r.add_footer(ctx.slide, text=text)

        page_number = chrome.get("page_number", {})
        if isinstance(page_number, dict) and page_number.get("visible", self.name != "blank") and layout.page_number_box:
            fmt = str(page_number.get("format", "{current} / {total}"))
            text = fmt.format(current=page_index, total=total_pages)
            caption_font = getattr(ctx.theme.fonts, "caption_font", "") or None
            r.text(ctx.slide, layout.page_number_box, text, size=ctx.theme.fonts.tiny_size, color=ctx.theme.colors.text_tertiary, align="right", font=caption_font)

        self._render_primitive_specs(ctx, page, layout, page_index, total_pages, self.fore_primitives)

    def _render_primitive_specs(
        self,
        ctx: RenderContext,
        page: Page,
        layout: PageLayout,
        page_index: int,
        total_pages: int,
        specs: list[dict[str, Any]],
    ) -> None:
        for spec in specs:
            primitive = self._primitive_from_spec(ctx, page, layout, page_index, total_pages, spec)
            if primitive is not None:
                ctx.renderer.render_tree(ctx.slide, primitive, stylesheet=ctx.stylesheet)

    def _primitive_from_spec(
        self,
        ctx: RenderContext,
        page: Page,
        layout: PageLayout,
        page_index: int,
        total_pages: int,
        spec: Mapping[str, Any],
    ) -> object | None:
        type_name = str(spec.get("type", "primitive.text"))
        props = dict(spec.get("props", {})) if isinstance(spec.get("props", {}), Mapping) else {}
        style_data = dict(spec.get("style", {})) if isinstance(spec.get("style", {}), Mapping) else {}
        style = Style.from_dict({**style_data, **_style_props(props)})
        box = resolve_block_box(layout, dict(spec.get("layout", {})) if isinstance(spec.get("layout", {}), Mapping) else {})
        primitive_id = str(spec["id"]) if spec.get("id") is not None else None
        class_names = normalize_class_names(spec.get("class_names", spec.get("classes", spec.get("class"))))

        if type_name == "primitive.rect":
            return Rect(id=primitive_id, class_names=class_names, box=box, style=style)
        if type_name == "primitive.line":
            return Line(
                id=primitive_id,
                class_names=class_names,
                box=box,
                x1=float(props.get("x1", 0.0)),
                y1=float(props.get("y1", 0.0)),
                x2=float(props.get("x2", 0.0)),
                y2=float(props.get("y2", 0.0)),
                style=style,
            )
        if type_name == "primitive.image":
            return ImagePrimitive(id=primitive_id, class_names=class_names, box=box, src=str(props.get("src", "")), fit=str(props.get("fit", "contain")), style=style)
        if type_name == "primitive.icon":
            return IconPrimitive(id=primitive_id, class_names=class_names, box=box, name=str(props.get("name", "")), icon_props=dict(props), style=style)
        return Text(
            id=primitive_id,
            class_names=class_names,
            box=box,
            text=_format_master_text(str(props.get("text", "")), page, page_index, total_pages),
            style=style,
        )


def _style_props(props: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: props[key]
        for key in (
            "fill",
            "stroke",
            "border",
            "color",
            "font_size",
            "size",
            "font_family",
            "font_weight",
            "bold",
            "radius",
            "opacity",
            "shadow",
            "align",
            "valign",
            "stroke_width",
            "line_width",
        )
        if key in props
    }


def _format_master_text(template: str, page: Page, page_index: int, total_pages: int) -> str:
    try:
        return template.format(
            title=page.title,
            subtitle=page.subtitle,
            current=page_index,
            total=total_pages,
            page_type=page.type,
        )
    except (KeyError, ValueError):
        return template


@dataclass
class MasterRegistry:
    masters: dict[str, SlideMaster] = field(default_factory=dict)

    def register(self, name: str, master: SlideMaster) -> None:
        self.masters[name] = master

    def get(self, name: str) -> SlideMaster:
        if name not in self.masters:
            raise ValueError(f"Unknown master: {name}")
        return self.masters[name]

    @classmethod
    def with_defaults(cls) -> "MasterRegistry":
        registry = cls()
        registry.register("default", default_master("default"))
        registry.register("tech_blue", default_master("tech_blue"))
        registry.register("blank", default_master("blank"))
        return registry


def default_master(name: str = "tech_blue") -> SlideMaster:
    if name == "blank":
        return SlideMaster(
            name="blank",
            chrome={
                "accent_bar": {"visible": False},
                "footer": {"visible": False},
                "page_number": {"visible": False},
                "logo": {"visible": False},
            },
        )

    return SlideMaster(
        name=name,
        background={},
        chrome={
            "accent_bar": {"visible": True},
            "footer": {"visible": True, "text": "SlideForge - Agent-driven PPT UI Framework"},
            "page_number": {"visible": True, "format": "{current} / {total}"},
            "logo": {"visible": False, "text": "SlideForge"},
        },
    )
