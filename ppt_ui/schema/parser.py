from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ppt_ui.components.registry import build_default_component_registry
from ppt_ui.core.diagnostics import DiagnosticBag
from ppt_ui.core.master import MasterRegistry, SlideMaster, default_master
from ppt_ui.core.page import Block, Page
from ppt_ui.core.presentation import Deck
from ppt_ui.core.registry import ComponentRegistry
from ppt_ui.core.theme import get_theme


def deck_from_json(path: str | Path) -> Deck:
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    return deck_from_dict(data, base_dir=source.parent)


PAGE_TYPES = {"page.cover", "page.standard", "page.section", "page.blank", "page.closing", "page.qa"}


def deck_from_dict(
    data: Mapping[str, Any],
    component_registry: ComponentRegistry | None = None,
    *,
    strict: bool = True,
    base_dir: str | Path | None = None,
) -> Deck:
    registry = component_registry or build_default_component_registry()
    diagnostics = validate_deck_dict(data, registry)
    if strict:
        diagnostics.raise_for_errors()
    masters = masters_from_dict(data.get("masters", {}))
    deck = Deck(
        title=str(data.get("title", "SlideForge Deck")),
        theme=get_theme(data.get("theme", "default_blue"), base_dir=base_dir),
        default_master=str(data.get("default_master", "tech_blue")),
        masters=masters,
        components=registry,
        metadata=dict(data.get("metadata", {})),
        diagnostics=diagnostics.items,
    )
    for page_data in data.get("pages", []):
        deck.add_page(page_from_dict(page_data))
    return deck


def validate_deck_dict(data: Mapping[str, Any], registry: ComponentRegistry) -> DiagnosticBag:
    diagnostics = DiagnosticBag()

    if not isinstance(data, Mapping):
        diagnostics.error("INVALID_DECK", "Deck input must be an object.", path="$")
        return diagnostics

    schema_version = str(data.get("schema_version", "0.2"))
    if schema_version != "0.2":
        diagnostics.warning(
            "UNSUPPORTED_SCHEMA_VERSION",
            f"Schema version {schema_version} is not the current target version.",
            path="$.schema_version",
            suggestion="Use schema_version: 0.2 for the page/block DSL.",
        )

    pages = data.get("pages")
    if not isinstance(pages, list):
        diagnostics.error("MISSING_PAGES", "Deck must contain a pages array.", path="$.pages")
        return diagnostics

    raw_masters = data.get("masters", {})
    master_names = {"default", "tech_blue", "blank"}
    if isinstance(raw_masters, Mapping):
        master_names.update(str(name) for name in raw_masters.keys())
    default_master = str(data.get("default_master", "tech_blue"))
    if default_master not in master_names:
        diagnostics.error("UNKNOWN_MASTER", f"Unknown default master: {default_master}", path="$.default_master")

    for page_index, raw_page in enumerate(pages):
        page_path = f"$.pages[{page_index}]"
        if not isinstance(raw_page, Mapping):
            diagnostics.error("INVALID_PAGE", "Page must be an object.", path=page_path)
            continue
        page_type = str(raw_page.get("type", "page.standard"))
        if page_type not in PAGE_TYPES:
            diagnostics.error(
                "UNKNOWN_PAGE_TYPE",
                f"Unsupported page type: {page_type}",
                path=f"{page_path}.type",
                suggestion=f"Use one of: {', '.join(sorted(PAGE_TYPES))}",
            )
        page_master = raw_page.get("master")
        if page_master is not None and str(page_master) not in master_names:
            diagnostics.error("UNKNOWN_MASTER", f"Unknown page master: {page_master}", path=f"{page_path}.master")
        blocks = raw_page.get("blocks", [])
        if not isinstance(blocks, list):
            diagnostics.error("INVALID_BLOCKS", "Page blocks must be an array.", path=f"{page_path}.blocks")
            continue
        for block_index, raw_block in enumerate(blocks):
            block_path = f"{page_path}.blocks[{block_index}]"
            validate_block(raw_block, registry, diagnostics, block_path)

    return diagnostics


def validate_block(raw_block: object, registry: ComponentRegistry, diagnostics: DiagnosticBag, path: str) -> None:
    if not isinstance(raw_block, Mapping):
        diagnostics.error("INVALID_BLOCK", "Block must be an object.", path=path)
        return

    type_name = str(raw_block.get("type", ""))
    if not type_name:
        diagnostics.error("MISSING_BLOCK_TYPE", "Block type is required.", path=f"{path}.type")
        return
    if not registry.has(type_name):
        diagnostics.error(
            "UNKNOWN_COMPONENT_TYPE",
            f"Unsupported component type: {type_name}",
            path=f"{path}.type",
            suggestion=f"Use one of: {', '.join(registry.type_names())}",
        )

    props = raw_block.get("props", {})
    if not isinstance(props, Mapping):
        diagnostics.error("INVALID_PROPS", "Block props must be an object.", path=f"{path}.props")
        return

    if type_name == "chart.line":
        validate_chart_series(props, diagnostics, f"{path}.props")
    elif type_name in {"chart.bar", "chart.pie", "chart.donut"}:
        values = props.get("values", props.get("data"))
        if values is not None and not isinstance(values, list):
            diagnostics.warning("INVALID_CHART_VALUES", "Chart values should be an array.", path=f"{path}.props.values")
    elif type_name in {"table.comparison", "table.basic"}:
        validate_table(props, diagnostics, f"{path}.props")


def validate_chart_series(props: Mapping[str, Any], diagnostics: DiagnosticBag, path: str) -> None:
    categories = props.get("categories", [])
    series = props.get("series", [])
    if not isinstance(categories, list):
        diagnostics.error("INVALID_CHART_CATEGORIES", "chart.line categories must be an array.", path=f"{path}.categories")
        return
    if not isinstance(series, list):
        diagnostics.error("INVALID_CHART_SERIES", "chart.line series must be an array.", path=f"{path}.series")
        return
    for series_index, raw_series in enumerate(series):
        if not isinstance(raw_series, Mapping):
            diagnostics.error("INVALID_CHART_SERIES_ITEM", "Each chart series must be an object.", path=f"{path}.series[{series_index}]")
            continue
        values = raw_series.get("values", [])
        if not isinstance(values, list):
            diagnostics.error("INVALID_CHART_VALUES", "Series values must be an array.", path=f"{path}.series[{series_index}].values")
            continue
        if categories and len(values) != len(categories):
            diagnostics.warning(
                "CHART_SERIES_LENGTH_MISMATCH",
                "Series values length does not match categories length.",
                path=f"{path}.series[{series_index}].values",
            )


def validate_table(props: Mapping[str, Any], diagnostics: DiagnosticBag, path: str) -> None:
    headers = props.get("headers", [])
    rows = props.get("rows", [])
    if not isinstance(headers, list):
        diagnostics.error("INVALID_TABLE_HEADERS", "Table headers must be an array.", path=f"{path}.headers")
        return
    if not isinstance(rows, list):
        diagnostics.error("INVALID_TABLE_ROWS", "Table rows must be an array.", path=f"{path}.rows")
        return
    for row_index, row in enumerate(rows):
        if not isinstance(row, list):
            diagnostics.error("INVALID_TABLE_ROW", "Each table row must be an array.", path=f"{path}.rows[{row_index}]")
            continue
        if headers and len(row) != len(headers):
            diagnostics.warning("TABLE_ROW_LENGTH_MISMATCH", "Table row length does not match headers length.", path=f"{path}.rows[{row_index}]")


def masters_from_dict(data: object) -> MasterRegistry:
    registry = MasterRegistry.with_defaults()
    if not isinstance(data, Mapping):
        return registry

    for name, raw_master in data.items():
        if not isinstance(raw_master, Mapping):
            continue
        master_type = str(raw_master.get("type", f"master.{name}")).removeprefix("master.")
        base = default_master(master_type if master_type in {"blank", "default", "tech_blue"} else "tech_blue")
        registry.register(
            str(name),
            SlideMaster(
                name=str(name),
                chrome={**base.chrome, **dict(raw_master.get("chrome", {}))},
                background={**base.background, **dict(raw_master.get("background", {}))},
            ),
        )
    return registry


def page_from_dict(data: Mapping[str, Any]) -> Page:
    return Page.from_mapping(data)


def block_from_dict(data: Mapping[str, Any]) -> Block:
    return Block.from_mapping(data)
