from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    w: float
    h: float

    def inset(self, left: float = 0, top: float = 0, right: float | None = None, bottom: float | None = None) -> "Box":
        right = left if right is None else right
        bottom = top if bottom is None else bottom
        return Box(self.x + left, self.y + top, max(0, self.w - left - right), max(0, self.h - top - bottom))

    def split_cols(self, count: int, gutter: float = 0.0) -> list["Box"]:
        if count <= 0:
            return []
        col_w = (self.w - gutter * (count - 1)) / count
        return [Box(self.x + i * (col_w + gutter), self.y, col_w, self.h) for i in range(count)]

    def split_rows(self, count: int, gutter: float = 0.0) -> list["Box"]:
        if count <= 0:
            return []
        row_h = (self.h - gutter * (count - 1)) / count
        return [Box(self.x, self.y + i * (row_h + gutter), self.w, row_h) for i in range(count)]

    def top(self, height: float) -> "Box":
        return Box(self.x, self.y, self.w, min(height, self.h))

    def bottom(self, height: float) -> "Box":
        height = min(height, self.h)
        return Box(self.x, self.y + self.h - height, self.w, height)

    def remaining_below(self, top_height: float, gap: float = 0.0) -> "Box":
        y = self.y + top_height + gap
        return Box(self.x, y, self.w, max(0, self.y + self.h - y))


@dataclass(frozen=True)
class SlotPadding:
    """CSS-like padding in inch units."""

    left: float = 0.0
    top: float = 0.0
    right: float = 0.0
    bottom: float = 0.0

    @classmethod
    def from_value(cls, value: object) -> "SlotPadding":
        if isinstance(value, Mapping):
            all_value = _float(value.get("all", value.get("value", 0.0)))
            horizontal = _float(value.get("horizontal", value.get("x", all_value)))
            vertical = _float(value.get("vertical", value.get("y", all_value)))
            return cls(
                left=_float(value.get("left", horizontal)),
                top=_float(value.get("top", vertical)),
                right=_float(value.get("right", horizontal)),
                bottom=_float(value.get("bottom", vertical)),
            )
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            values = [_float(item) for item in value]
            if len(values) == 1:
                return cls(values[0], values[0], values[0], values[0])
            if len(values) == 2:
                vertical, horizontal = values
                return cls(horizontal, vertical, horizontal, vertical)
            if len(values) == 3:
                top, horizontal, bottom = values
                return cls(horizontal, top, horizontal, bottom)
            if len(values) >= 4:
                top, right, bottom, left = values[:4]
                return cls(left, top, right, bottom)
        amount = _float(value)
        return cls(amount, amount, amount, amount)

    def apply(self, box: Box) -> Box:
        return box.inset(self.left, self.top, self.right, self.bottom)


@dataclass(frozen=True)
class SlotNode:
    """Declarative slot used by semantic components.

    A slot is a named semantic region such as ``label``, ``value``, ``icon``,
    or ``plot``. Recipes decide where the slot lives; components decide what
    primitives are rendered into that slot.
    """

    name: str
    layout: Mapping[str, Any] = field(default_factory=dict)
    children: tuple["SlotNode", ...] = ()
    hidden: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "layout", dict(self.layout))
        object.__setattr__(self, "children", tuple(_slot_node(child) for child in self.children))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_value(cls, value: object) -> "SlotNode":
        return _slot_node(value)


@dataclass(frozen=True)
class ResolvedSlot:
    """A slot after recipe layout has resolved it to a concrete Box."""

    name: str
    box: Box
    node: SlotNode
    children: tuple["ResolvedSlot", ...] = ()

    def walk(self, prefix: str = "") -> Iterable[tuple[str, "ResolvedSlot"]]:
        key = f"{prefix}.{self.name}" if prefix else self.name
        yield key, self
        for child in self.children:
            yield from child.walk(key)


@dataclass(frozen=True)
class SlotLayoutRecipe:
    """A reusable slot layout recipe.

    The model names intentionally mirror front-end layout vocabulary while
    keeping the output simple: every slot resolves to a PPT inch-based Box.
    """

    model: str = "stack"
    gap: float = 0.0
    padding: SlotPadding = field(default_factory=SlotPadding)
    options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "model", str(self.model).lower().replace("-", "_"))
        object.__setattr__(self, "gap", _float(self.gap))
        if not isinstance(self.padding, SlotPadding):
            object.__setattr__(self, "padding", SlotPadding.from_value(self.padding))
        object.__setattr__(self, "options", dict(self.options))

    @classmethod
    def from_value(cls, value: object) -> "SlotLayoutRecipe":
        if isinstance(value, SlotLayoutRecipe):
            return value
        if isinstance(value, str):
            return cls(model=value)
        if isinstance(value, Mapping):
            options = dict(value)
            model = str(options.pop("model", options.pop("type", "stack")))
            if model.startswith("layout."):
                model = model.removeprefix("layout.")
            gap = _float(options.pop("gap", 0.0))
            padding = SlotPadding.from_value(options.pop("padding", 0.0))
            return cls(model=model, gap=gap, padding=padding, options=options)
        return cls()


@dataclass(frozen=True)
class SlotLayoutResult:
    root: Box
    slots: Mapping[str, ResolvedSlot]
    warnings: tuple[str, ...] = ()

    def box(self, name: str, default: Box | None = None) -> Box:
        slot = self.slots.get(name)
        if slot is None:
            if default is not None:
                return default
            raise KeyError(f"Unknown slot: {name}")
        return slot.box


class SlotLayoutEngine:
    """Resolve semantic slots into concrete Boxes.

    This class is renderer-independent and is safe to use from components,
    tests, parsers, or future preview backends.
    """

    def layout(self, box: Box, slots: Sequence[SlotNode | str | Mapping[str, Any]], recipe: SlotLayoutRecipe | Mapping[str, Any] | str | None = None) -> SlotLayoutResult:
        layout_recipe = SlotLayoutRecipe.from_value(recipe)
        nodes = tuple(node for node in (_slot_node(slot) for slot in slots) if not node.hidden)
        content = layout_recipe.padding.apply(box)
        resolved, warnings = self._layout_nodes(content, nodes, layout_recipe)
        flattened: dict[str, ResolvedSlot] = {}
        for slot in resolved:
            for key, item in slot.walk():
                flattened[key] = item
        return SlotLayoutResult(root=content, slots=flattened, warnings=tuple(warnings))

    resolve = layout

    def _layout_nodes(self, box: Box, nodes: Sequence[SlotNode], recipe: SlotLayoutRecipe) -> tuple[list[ResolvedSlot], list[str]]:
        model = recipe.model
        warnings: list[str] = []
        if model in {"row", "hstack", "horizontal"}:
            raw = self._layout_stack(box, nodes, recipe, horizontal=True)
        elif model in {"grid"}:
            raw = self._layout_grid(box, nodes, recipe)
        elif model in {"template", "areas"}:
            raw = self._layout_template(box, nodes, recipe)
        elif model in {"dock"}:
            raw = self._layout_dock(box, nodes, recipe)
        elif model in {"overlay", "absolute"}:
            raw = self._layout_overlay(box, nodes, recipe)
        elif model in {"flow", "wrap"}:
            raw = self._layout_flow(box, nodes, recipe)
        else:
            if model not in {"stack", "vstack", "vertical"}:
                warnings.append(f"Unknown slot layout model '{model}', falling back to stack.")
            raw = self._layout_stack(box, nodes, recipe, horizontal=False)

        result: list[ResolvedSlot] = []
        for node, slot_box in raw:
            children, child_warnings = self._layout_child_slots(slot_box, node)
            warnings.extend(child_warnings)
            result.append(ResolvedSlot(name=node.name, box=slot_box, node=node, children=tuple(children)))
        return result, warnings

    def _layout_child_slots(self, box: Box, node: SlotNode) -> tuple[list[ResolvedSlot], list[str]]:
        if not node.children:
            return [], []
        child_recipe = SlotLayoutRecipe.from_value(node.layout.get("recipe", node.layout.get("layout", "stack")))
        return self._layout_nodes(box, node.children, child_recipe)

    def _layout_stack(self, box: Box, nodes: Sequence[SlotNode], recipe: SlotLayoutRecipe, *, horizontal: bool) -> list[tuple[SlotNode, Box]]:
        if not nodes:
            return []
        gap = _option_float(recipe, "column_gap" if horizontal else "row_gap", recipe.gap)
        available = max(0.0, (box.w if horizontal else box.h) - gap * max(0, len(nodes) - 1))
        fixed_total = 0.0
        grow_total = 0.0
        lengths: list[float | None] = []
        grow_values: list[float] = []

        for node in nodes:
            length = _node_axis_size(node, horizontal=horizontal)
            lengths.append(length)
            if length is None:
                grow = max(0.0, _float(node.layout.get("grow", node.layout.get("fr", 1.0)), 1.0))
                grow_values.append(grow)
                grow_total += grow
            else:
                grow_values.append(0.0)
                fixed_total += max(0.0, length)

        remaining = max(0.0, available - fixed_total)
        cursor = box.x if horizontal else box.y
        result: list[tuple[SlotNode, Box]] = []
        for index, node in enumerate(nodes):
            length = lengths[index]
            if length is None:
                length = remaining * (grow_values[index] / grow_total) if grow_total else 0.0
            length = max(0.0, length)
            if horizontal:
                slot_box = Box(cursor, box.y, length, box.h)
                slot_box = _fit_box(slot_box, node)
                cursor += length + gap
            else:
                slot_box = Box(box.x, cursor, box.w, length)
                slot_box = _fit_box(slot_box, node)
                cursor += length + gap
            result.append((node, slot_box))
        return result

    def _layout_grid(self, box: Box, nodes: Sequence[SlotNode], recipe: SlotLayoutRecipe) -> list[tuple[SlotNode, Box]]:
        if not nodes:
            return []
        columns = max(1, int(_option_float(recipe, "columns", 1)))
        rows = max(1, int(_option_float(recipe, "rows", (len(nodes) + columns - 1) // columns)))
        gap_x = _option_float(recipe, "column_gap", recipe.gap)
        gap_y = _option_float(recipe, "row_gap", recipe.gap)
        cell_w = (box.w - gap_x * (columns - 1)) / columns
        cell_h = (box.h - gap_y * (rows - 1)) / rows
        result: list[tuple[SlotNode, Box]] = []
        for index, node in enumerate(nodes):
            col = max(1, int(_float(node.layout.get("col", index % columns + 1), index % columns + 1)))
            row = max(1, int(_float(node.layout.get("row", index // columns + 1), index // columns + 1)))
            span = max(1, int(_float(node.layout.get("span", node.layout.get("col_span", 1)), 1)))
            row_span = max(1, int(_float(node.layout.get("row_span", 1), 1)))
            slot_box = Box(
                box.x + (col - 1) * (cell_w + gap_x),
                box.y + (row - 1) * (cell_h + gap_y),
                cell_w * span + gap_x * (span - 1),
                cell_h * row_span + gap_y * (row_span - 1),
            )
            result.append((node, _fit_box(slot_box, node)))
        return result

    def _layout_template(self, box: Box, nodes: Sequence[SlotNode], recipe: SlotLayoutRecipe) -> list[tuple[SlotNode, Box]]:
        areas = _template_rows(recipe.options.get("areas", recipe.options.get("template", [])))
        if not areas:
            return self._layout_grid(box, nodes, SlotLayoutRecipe(model="grid", gap=recipe.gap, options={"columns": max(1, len(nodes)), "rows": 1}))
        rows = len(areas)
        columns = max(1, max(len(row) for row in areas))
        gap_x = _option_float(recipe, "column_gap", recipe.gap)
        gap_y = _option_float(recipe, "row_gap", recipe.gap)
        cell_w = (box.w - gap_x * (columns - 1)) / columns
        cell_h = (box.h - gap_y * (rows - 1)) / rows
        extents: dict[str, tuple[int, int, int, int]] = {}
        for row_index, row in enumerate(areas):
            for col_index, name in enumerate(row):
                if name in {"", "."}:
                    continue
                if name not in extents:
                    extents[name] = (row_index, col_index, row_index, col_index)
                else:
                    top, left, bottom, right = extents[name]
                    extents[name] = (min(top, row_index), min(left, col_index), max(bottom, row_index), max(right, col_index))

        result: list[tuple[SlotNode, Box]] = []
        for node in nodes:
            extent = extents.get(node.name)
            if extent is None:
                result.append((node, _anchored_box(box, node, fill=True)))
                continue
            top, left, bottom, right = extent
            slot_box = Box(
                box.x + left * (cell_w + gap_x),
                box.y + top * (cell_h + gap_y),
                cell_w * (right - left + 1) + gap_x * (right - left),
                cell_h * (bottom - top + 1) + gap_y * (bottom - top),
            )
            result.append((node, _fit_box(slot_box, node)))
        return result

    def _layout_dock(self, box: Box, nodes: Sequence[SlotNode], recipe: SlotLayoutRecipe) -> list[tuple[SlotNode, Box]]:
        remaining = box
        gap = recipe.gap
        result: list[tuple[SlotNode, Box]] = []
        for node in nodes:
            dock = str(node.layout.get("dock", node.layout.get("position", "center"))).lower().replace("_", "-")
            if dock == "top":
                height = _float(node.layout.get("height", node.layout.get("h", recipe.options.get("dock_size", remaining.h))), remaining.h)
                slot_box = remaining.top(height)
                remaining = Box(remaining.x, remaining.y + height + gap, remaining.w, max(0.0, remaining.h - height - gap))
            elif dock == "bottom":
                height = _float(node.layout.get("height", node.layout.get("h", recipe.options.get("dock_size", remaining.h))), remaining.h)
                slot_box = remaining.bottom(height)
                remaining = Box(remaining.x, remaining.y, remaining.w, max(0.0, remaining.h - height - gap))
            elif dock == "left":
                width = _float(node.layout.get("width", node.layout.get("w", recipe.options.get("dock_size", remaining.w))), remaining.w)
                slot_box = Box(remaining.x, remaining.y, min(width, remaining.w), remaining.h)
                remaining = Box(remaining.x + width + gap, remaining.y, max(0.0, remaining.w - width - gap), remaining.h)
            elif dock == "right":
                width = _float(node.layout.get("width", node.layout.get("w", recipe.options.get("dock_size", remaining.w))), remaining.w)
                slot_box = Box(remaining.x + max(0.0, remaining.w - width), remaining.y, min(width, remaining.w), remaining.h)
                remaining = Box(remaining.x, remaining.y, max(0.0, remaining.w - width - gap), remaining.h)
            elif dock in {"center", "fill", "content"}:
                slot_box = remaining
            else:
                slot_box = _anchored_box(box, node, fill=False, anchor=dock)
            result.append((node, _fit_box(slot_box, node)))
        return result

    def _layout_overlay(self, box: Box, nodes: Sequence[SlotNode], recipe: SlotLayoutRecipe) -> list[tuple[SlotNode, Box]]:
        return [(node, _anchored_box(box, node, fill=True, anchor=str(node.layout.get("anchor", recipe.options.get("anchor", "stretch"))))) for node in nodes]

    def _layout_flow(self, box: Box, nodes: Sequence[SlotNode], recipe: SlotLayoutRecipe) -> list[tuple[SlotNode, Box]]:
        gap_x = _option_float(recipe, "column_gap", recipe.gap)
        gap_y = _option_float(recipe, "row_gap", recipe.gap)
        default_w = _option_float(recipe, "item_width", _option_float(recipe, "width", box.w))
        default_h = _option_float(recipe, "item_height", _option_float(recipe, "height", box.h))
        cursor_x = box.x
        cursor_y = box.y
        row_h = 0.0
        result: list[tuple[SlotNode, Box]] = []
        for node in nodes:
            width = _float(node.layout.get("width", node.layout.get("w", default_w)), default_w)
            height = _float(node.layout.get("height", node.layout.get("h", default_h)), default_h)
            if result and cursor_x + width > box.x + box.w + 1e-9:
                cursor_x = box.x
                cursor_y += row_h + gap_y
                row_h = 0.0
            slot_box = Box(cursor_x, cursor_y, min(width, box.w), height)
            result.append((node, _fit_box(slot_box, node)))
            cursor_x += width + gap_x
            row_h = max(row_h, height)
        return result


def _float(value: object, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _option_float(recipe: SlotLayoutRecipe, key: str, default: float) -> float:
    return _float(recipe.options.get(key), default)


def _slot_node(value: object) -> SlotNode:
    if isinstance(value, SlotNode):
        return value
    if isinstance(value, str):
        return SlotNode(name=value)
    if isinstance(value, Mapping):
        data = dict(value)
        children = tuple(_slot_node(child) for child in data.pop("children", ()))
        layout = dict(data.pop("layout", {}))
        for key in (
            "anchor",
            "col",
            "col_span",
            "dock",
            "fr",
            "grow",
            "h",
            "height",
            "position",
            "recipe",
            "row",
            "row_span",
            "span",
            "w",
            "width",
            "x",
            "y",
        ):
            if key in data and key not in layout:
                layout[key] = data.pop(key)
        return SlotNode(
            name=str(data.pop("name", data.pop("slot", ""))),
            layout=layout,
            children=children,
            hidden=bool(data.pop("hidden", False)),
            metadata=data,
        )
    return SlotNode(name=str(value))


def _node_axis_size(node: SlotNode, *, horizontal: bool) -> float | None:
    keys = ("width", "w", "size") if horizontal else ("height", "h", "size")
    for key in keys:
        if key in node.layout:
            return _float(node.layout[key])
    return None


def _node_cross_size(node: SlotNode, *, horizontal: bool) -> float | None:
    keys = ("height", "h") if horizontal else ("width", "w")
    for key in keys:
        if key in node.layout:
            return _float(node.layout[key])
    return None


def _fit_box(box: Box, node: SlotNode) -> Box:
    width = _node_cross_size(node, horizontal=False)
    height = _node_cross_size(node, horizontal=True)
    if width is None and height is None:
        return box
    width = box.w if width is None else min(width, box.w)
    height = box.h if height is None else min(height, box.h)
    align = str(node.layout.get("align", node.layout.get("justify", "stretch" if width == box.w else "start"))).lower()
    valign = str(node.layout.get("valign", node.layout.get("vertical_align", "stretch" if height == box.h else "start"))).lower()
    x = _align_start(box.x, box.w, width, align)
    y = _align_start(box.y, box.h, height, valign)
    return Box(x, y, width, height)


def _align_start(start: float, available: float, size: float, align: str) -> float:
    align = align.replace("_", "-")
    if align in {"center", "middle"}:
        return start + (available - size) / 2
    if align in {"end", "right", "bottom"}:
        return start + available - size
    return start


def _anchored_box(box: Box, node: SlotNode, *, fill: bool, anchor: str | None = None) -> Box:
    layout = node.layout
    if "x" in layout or "y" in layout:
        width = _float(layout.get("width", layout.get("w", box.w if fill else min(1.0, box.w))), box.w if fill else min(1.0, box.w))
        height = _float(layout.get("height", layout.get("h", box.h if fill else min(1.0, box.h))), box.h if fill else min(1.0, box.h))
        x = box.x + _float(layout.get("x", 0.0))
        y = box.y + _float(layout.get("y", 0.0))
        return Box(x, y, min(width, box.w), min(height, box.h))

    anchor = (anchor or str(layout.get("anchor", "stretch" if fill else "center"))).lower().replace("_", "-")
    width = _float(layout.get("width", layout.get("w", box.w if fill or anchor == "stretch" else min(1.0, box.w))), box.w)
    height = _float(layout.get("height", layout.get("h", box.h if fill or anchor == "stretch" else min(1.0, box.h))), box.h)
    width = min(width, box.w)
    height = min(height, box.h)
    if anchor == "stretch":
        return Box(box.x, box.y, box.w, box.h)

    x_align = "center"
    y_align = "center"
    if "left" in anchor:
        x_align = "start"
    elif "right" in anchor:
        x_align = "end"
    if "top" in anchor:
        y_align = "start"
    elif "bottom" in anchor:
        y_align = "end"
    return Box(_align_start(box.x, box.w, width, x_align), _align_start(box.y, box.h, height, y_align), width, height)


def _template_rows(value: object) -> list[list[str]]:
    rows: list[list[str]] = []
    if isinstance(value, str):
        value = [line for line in value.splitlines() if line.strip()]
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return rows
    for row in value:
        if isinstance(row, str):
            rows.append([item for item in row.split() if item])
        elif isinstance(row, Sequence):
            rows.append([str(item) for item in row])
    return rows


class PageBox(Box):
    @classmethod
    def from_theme(cls, theme: object) -> "PageBox":
        spacing = theme.spacing
        return cls(
            spacing.page_margin,
            spacing.page_y,
            theme.slide_width - spacing.page_margin * 2,
            theme.slide_height - spacing.page_y * 2,
        )


@dataclass(frozen=True)
class GridSpec:
    columns: int = 12
    rows: int = 6
    gap: float = 0.20


@dataclass(frozen=True)
class PageLayout:
    name: str = "standard"
    title_box: Box | None = None
    subtitle_box: Box | None = None
    content_box: Box | None = None
    footer_box: Box | None = None
    page_number_box: Box | None = None
    grid: GridSpec = field(default_factory=GridSpec)
    zones: dict[str, Box] = field(default_factory=dict)


def default_page_layout(name: str, theme: object) -> PageLayout:
    """Return a built-in page layout in inch units."""

    margin = theme.spacing.page_margin
    width = theme.slide_width
    height = theme.slide_height
    footer_y = theme.spacing.footer_y

    if name == "cover":
        return PageLayout(
            name="cover",
            title_box=Box(margin, 1.38, 7.2, 0.72),
            subtitle_box=Box(margin, 2.18, 7.2, 0.34),
            content_box=Box(margin, 3.05, width - margin * 2, 3.45),
            footer_box=Box(margin, footer_y, 5.2, 0.24),
            page_number_box=Box(width - margin - 0.8, footer_y + 0.05, 0.8, 0.18),
            grid=GridSpec(columns=12, rows=4, gap=theme.spacing.gutter),
        )

    if name == "section":
        return PageLayout(
            name="section",
            title_box=Box(3.05, 1.55, 8.0, 0.52),
            subtitle_box=Box(3.07, 2.13, 7.6, 0.30),
            content_box=Box(3.05, 2.92, 8.1, 2.65),
            footer_box=Box(margin, footer_y, 5.2, 0.24),
            page_number_box=Box(width - margin - 0.8, footer_y + 0.05, 0.8, 0.18),
            grid=GridSpec(columns=12, rows=3, gap=theme.spacing.gutter),
        )

    if name in {"blank", "full_bleed"}:
        return PageLayout(
            name=name,
            title_box=Box(margin, theme.spacing.title_top, 9.4, 0.42),
            subtitle_box=Box(margin, theme.spacing.title_top + 0.45, 9.4, 0.27),
            content_box=Box(0, 0, width, height),
            footer_box=Box(margin, footer_y, 5.2, 0.24),
            page_number_box=Box(width - margin - 0.8, footer_y + 0.05, 0.8, 0.18),
            grid=GridSpec(columns=12, rows=6, gap=theme.spacing.gutter),
        )

    if name in {"closing", "qa"}:
        return PageLayout(
            name=name,
            title_box=Box(margin, 1.35, width - margin * 2, 0.72),
            subtitle_box=Box(margin, 2.18, width - margin * 2, 0.32),
            content_box=Box(margin, 2.88, width - margin * 2, 3.50),
            footer_box=Box(margin, footer_y, 5.2, 0.24),
            page_number_box=Box(width - margin - 0.8, footer_y + 0.05, 0.8, 0.18),
            grid=GridSpec(columns=12, rows=4, gap=theme.spacing.gutter),
        )

    return PageLayout(
        name="standard",
        title_box=Box(margin, theme.spacing.title_top - 0.03, 9.2, 0.42),
        subtitle_box=Box(margin, theme.spacing.title_top + 0.45, 9.4, 0.27),
        content_box=Box(margin, theme.spacing.content_top, width - margin * 2, height - theme.spacing.content_top - 0.70),
        footer_box=Box(margin, footer_y, 5.2, 0.24),
        page_number_box=Box(width - margin - 0.8, footer_y + 0.05, 0.8, 0.18),
        grid=GridSpec(columns=12, rows=6, gap=theme.spacing.gutter),
    )


def layout_from_spec(spec: str | Mapping[str, Any] | None, theme: object) -> PageLayout:
    """Build a PageLayout from a layout name or inline layout spec."""

    if spec is None:
        return default_page_layout("standard", theme)
    if isinstance(spec, str):
        return default_page_layout(spec, theme)

    layout_type = str(spec.get("type", spec.get("name", "layout.grid")))
    name = layout_type.removeprefix("layout.")
    base = default_page_layout(name if name in {"cover", "section", "blank", "closing", "qa"} else "standard", theme)
    grid = GridSpec(
        columns=int(spec.get("columns", base.grid.columns)),
        rows=int(spec.get("rows", base.grid.rows)),
        gap=float(spec.get("gap", base.grid.gap)),
    )
    return PageLayout(
        name=name,
        title_box=base.title_box,
        subtitle_box=base.subtitle_box,
        content_box=base.content_box,
        footer_box=base.footer_box,
        page_number_box=base.page_number_box,
        grid=grid,
        zones=base.zones,
    )


def resolve_block_box(layout: PageLayout, block_layout: Mapping[str, Any] | None) -> Box:
    """Resolve a block layout spec to a concrete Box."""

    content = layout.content_box or Box(0, 0, 0, 0)
    spec: Mapping[str, Any] = block_layout or {}
    mode = str(spec.get("mode", "grid" if "col" in spec or "row" in spec else "absolute"))

    if mode == "absolute":
        return Box(
            float(spec.get("x", content.x)),
            float(spec.get("y", content.y)),
            float(spec.get("w", content.w)),
            float(spec.get("h", content.h)),
        )

    if mode == "zone":
        zone = str(spec.get("zone", "content"))
        return layout.zones.get(zone, content)

    grid = layout.grid
    col = max(1, int(spec.get("col", 1)))
    span = max(1, int(spec.get("span", grid.columns)))
    row = max(1, int(spec.get("row", 1)))
    row_span = max(1, int(spec.get("row_span", 1)))

    col_w = (content.w - grid.gap * (grid.columns - 1)) / max(1, grid.columns)
    row_h = (content.h - grid.gap * (grid.rows - 1)) / max(1, grid.rows)
    x = content.x + (col - 1) * (col_w + grid.gap)
    y = content.y + (row - 1) * (row_h + grid.gap)
    w = col_w * span + grid.gap * (span - 1)
    h = row_h * row_span + grid.gap * (row_span - 1)
    return Box(x, y, w, h)
