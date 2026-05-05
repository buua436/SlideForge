from __future__ import annotations

from typing import Any

from ppt_ui.core.master import default_master
from ppt_ui.core.page import Block, Page
from ppt_ui.core.theme import get_theme


def _block(
    type_name: str,
    *,
    props: dict[str, Any] | None = None,
    variant: str = "default",
    layout: dict[str, Any] | None = None,
    style: dict[str, Any] | None = None,
    id: str | None = None,
    visible: bool = True,
) -> Block:
    return Block(type=type_name, variant=variant, props=props or {}, layout=layout or {}, style=style or {}, id=id, visible=visible)


class PageNamespace:
    def cover(
        self,
        *,
        title: str,
        subtitle: str = "",
        blocks: list[Block] | None = None,
        master: str | None = None,
        chrome: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Page:
        return Page(type="page.cover", layout="cover", title=title, subtitle=subtitle, blocks=blocks or [], master=master, chrome=chrome or {}, metadata=metadata or {})

    def standard(
        self,
        *,
        title: str = "",
        subtitle: str = "",
        blocks: list[Block] | None = None,
        layout: str | dict[str, Any] = "standard",
        master: str | None = None,
        chrome: dict[str, Any] | None = None,
        use_master: bool = True,
    ) -> Page:
        return Page(type="page.standard", layout=layout, title=title, subtitle=subtitle, blocks=blocks or [], master=master, chrome=chrome or {}, use_master=use_master)

    def section(
        self,
        *,
        title: str,
        subtitle: str = "",
        number: str = "01",
        blocks: list[Block] | None = None,
        master: str | None = None,
        chrome: dict[str, Any] | None = None,
    ) -> Page:
        metadata = {"number": number}
        merged_chrome = {"section": number, **(chrome or {})}
        return Page(type="page.section", layout="section", title=title, subtitle=subtitle, blocks=blocks or [], master=master, chrome=merged_chrome, metadata=metadata)

    def blank(self, *, blocks: list[Block] | None = None, layout: str | dict[str, Any] = "blank", chrome: dict[str, Any] | None = None) -> Page:
        return Page(type="page.blank", layout=layout, use_master=False, blocks=blocks or [], chrome=chrome or {})

    def closing(self, *, title: str = "Conclusion", subtitle: str = "", blocks: list[Block] | None = None, master: str | None = None) -> Page:
        return Page(type="page.closing", layout="closing", title=title, subtitle=subtitle, blocks=blocks or [], master=master)

    def qa(self, *, title: str = "Q&A", subtitle: str = "Thank you", blocks: list[Block] | None = None, master: str | None = None) -> Page:
        return Page(type="page.qa", layout="qa", title=title, subtitle=subtitle, blocks=blocks or [], master=master)


class LayoutNamespace:
    def grid(self, *, columns: int = 12, rows: int = 6, gap: float = 0.2) -> dict[str, Any]:
        return {"type": "layout.grid", "columns": columns, "rows": rows, "gap": gap}

    def absolute(self) -> dict[str, Any]:
        return {"type": "layout.absolute"}

    def grid_item(self, *, col: int, span: int, row: int = 1, row_span: int = 1) -> dict[str, Any]:
        return {"mode": "grid", "col": col, "span": span, "row": row, "row_span": row_span}

    def box(self, *, x: float, y: float, w: float, h: float) -> dict[str, Any]:
        return {"mode": "absolute", "x": x, "y": y, "w": w, "h": h}


class BlockNamespace:
    def component(
        self,
        type_name: str,
        *,
        props: dict[str, Any] | None = None,
        variant: str = "default",
        layout: dict[str, Any] | None = None,
        style: dict[str, Any] | None = None,
        id: str | None = None,
        visible: bool = True,
    ) -> Block:
        return _block(type_name, props=props, variant=variant, layout=layout, style=style, id=id, visible=visible)


class BasicNamespace:
    def text(
        self,
        *,
        text: str = "",
        bullets: list[str] | None = None,
        layout: dict[str, Any] | None = None,
        size: int | None = None,
        color: str | None = None,
        bold: bool = False,
        align: str = "left",
        valign: str = "top",
        id: str | None = None,
    ) -> Block:
        props: dict[str, Any] = {"text": text, "bullets": bullets or [], "bold": bold, "align": align, "valign": valign}
        if size is not None:
            props["size"] = size
        if color is not None:
            props["color"] = color
        return _block("basic.text", props=props, layout=layout, id=id)


class DataNamespace:
    def metric_card(self, *, label: str, value: str, delta: str = "", compare: str = "", note: str = "", icon: str = "") -> dict[str, Any]:
        return {"label": label, "value": value, "delta": delta, "compare": compare or note, "icon": icon}

    def metric_cards(self, *, cards: list[dict[str, Any]], layout: dict[str, Any] | None = None, id: str | None = None) -> Block:
        return _block("data.metric_cards", props={"cards": cards}, layout=layout, id=id)

    def progress(self, *, items: list[dict[str, Any]], layout: dict[str, Any] | None = None, id: str | None = None) -> Block:
        return _block("data.progress", props={"items": items}, layout=layout, id=id)


class ChartNamespace:
    def line(
        self,
        *,
        categories: list[str],
        series: list[dict[str, Any]],
        layout: dict[str, Any] | None = None,
        id: str | None = None,
    ) -> Block:
        return _block("chart.line", props={"categories": categories, "series": series}, layout=layout, id=id)

    def bar(
        self,
        *,
        categories: list[str],
        series: list[dict[str, Any]],
        layout: dict[str, Any] | None = None,
        id: str | None = None,
    ) -> Block:
        return _block("chart.bar", props={"categories": categories, "series": series}, layout=layout, id=id)

    def pie(self, *, labels: list[str], values: list[float], layout: dict[str, Any] | None = None, id: str | None = None) -> Block:
        return _block("chart.pie", props={"labels": labels, "values": values}, layout=layout, id=id)

    def donut(self, *, labels: list[str], values: list[float], layout: dict[str, Any] | None = None, id: str | None = None) -> Block:
        return _block("chart.donut", props={"labels": labels, "values": values}, layout=layout, id=id)


class TableNamespace:
    def comparison(
        self,
        *,
        headers: list[str],
        rows: list[list[str]],
        conclusion: str = "",
        layout: dict[str, Any] | None = None,
        id: str | None = None,
    ) -> Block:
        return _block("table.comparison", props={"headers": headers, "rows": rows, "conclusion": conclusion}, layout=layout, id=id)


class NarrativeNamespace:
    def timeline(self, *, items: list[dict[str, Any]], layout: dict[str, Any] | None = None, id: str | None = None) -> Block:
        return _block("narrative.timeline", props={"items": items}, layout=layout, id=id)

    def process_flow(self, *, steps: list[dict[str, Any]], layout: dict[str, Any] | None = None, id: str | None = None) -> Block:
        return _block("narrative.process_flow", props={"steps": steps}, layout=layout, id=id)

    def roadmap(self, *, items: list[dict[str, Any]], layout: dict[str, Any] | None = None, id: str | None = None) -> Block:
        return _block("narrative.roadmap", props={"items": items}, layout=layout, id=id)


class MediaNamespace:
    def icon(
        self,
        *,
        name: str,
        label: str = "",
        source: str = "",
        description: str = "",
        src: str = "",
        color: str = "",
        size: int | None = None,
        width: int | None = None,
        height: int | None = None,
        rotate: str | int | None = None,
        flip: str = "",
        stroke_width: float | None = None,
        opacity: float = 1.0,
        layout: dict[str, Any] | None = None,
        style: dict[str, Any] | None = None,
        id: str | None = None,
    ) -> Block:
        props: dict[str, Any] = {
            "name": name,
            "label": label,
            "source": source,
            "description": description,
            "src": src,
            "color": color,
            "flip": flip,
            "opacity": opacity,
        }
        if size is not None:
            props["size"] = size
        if width is not None:
            props["width"] = width
        if height is not None:
            props["height"] = height
        if rotate is not None:
            props["rotate"] = rotate
        if stroke_width is not None:
            props["stroke_width"] = stroke_width
        return _block(
            "media.icon",
            props=props,
            layout=layout,
            style=style,
            id=id,
        )

    def image(self, *, src: str, fit: str = "contain", layout: dict[str, Any] | None = None, id: str | None = None) -> Block:
        return _block("media.image", props={"src": src, "fit": fit}, layout=layout, id=id)


class MasterNamespace:
    def tech_blue(self):
        return default_master("tech_blue")

    def blank(self):
        return default_master("blank")


class ThemeNamespace:
    def tech_blue(self):
        return get_theme("theme.tech_blue")

    def glassmorphism(self):
        return get_theme("theme.glassmorphism")

    def claude(self):
        return get_theme("theme.claude")

    def glitch_art(self):
        return get_theme("theme.glitch_art")

    def paper_cut(self):
        return get_theme("theme.paper_cut")

    def neon_cyberpunk(self):
        return get_theme("theme.neon_cyberpunk")

    def apple(self):
        return get_theme("theme.apple")

    def google(self):
        return get_theme("theme.google")


page = PageNamespace()
slide = page
layout = LayoutNamespace()
block = BlockNamespace()
basic = BasicNamespace()
data = DataNamespace()
chart = ChartNamespace()
table = TableNamespace()
narrative = NarrativeNamespace()
media = MediaNamespace()
master = MasterNamespace()
theme = ThemeNamespace()

__all__ = ["basic", "block", "chart", "data", "layout", "master", "media", "narrative", "page", "slide", "table", "theme"]
