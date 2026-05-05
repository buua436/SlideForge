from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Block:
    """A component instance placed on a page."""

    type: str
    variant: str = "default"
    props: dict[str, Any] = field(default_factory=dict)
    layout: dict[str, Any] = field(default_factory=dict)
    style: dict[str, Any] = field(default_factory=dict)
    id: str | None = None
    visible: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "Block":
        return cls(
            id=str(data["id"]) if data.get("id") is not None else None,
            type=str(data.get("type", "")),
            variant=str(data.get("variant", "default")),
            props=dict(data.get("props", {})),
            layout=dict(data.get("layout", {})),
            style=dict(data.get("style", {})),
            visible=bool(data.get("visible", True)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class Page:
    """A single PPT page composed from page chrome and content blocks."""

    type: str = "page.standard"
    layout: str | dict[str, Any] = "standard"
    master: str | None = None
    use_master: bool = True
    master_overrides: dict[str, Any] = field(default_factory=dict)
    chrome: dict[str, Any] = field(default_factory=dict)
    title: str = ""
    subtitle: str = ""
    blocks: list[Block] = field(default_factory=list)
    notes: str = ""
    hidden: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "Page":
        page_type = str(data.get("type", "page.standard"))
        layout = data.get("layout")
        if layout is None:
            layout = page_type.removeprefix("page.")
        return cls(
            type=page_type,
            layout=layout,
            master=str(data["master"]) if data.get("master") is not None else None,
            use_master=bool(data.get("use_master", True)),
            master_overrides=dict(data.get("master_overrides", {})),
            chrome=dict(data.get("chrome", {})),
            title=str(data.get("title", "")),
            subtitle=str(data.get("subtitle", "")),
            blocks=[Block.from_mapping(item) for item in data.get("blocks", [])],
            notes=str(data.get("notes", "")),
            hidden=bool(data.get("hidden", False)),
            metadata=dict(data.get("metadata", {})),
        )
