from __future__ import annotations

from typing import Any, TypedDict


class BlockDict(TypedDict, total=False):
    id: str
    type: str
    variant: str
    props: dict[str, Any]
    layout: dict[str, Any]
    style: dict[str, Any]
    visible: bool
    metadata: dict[str, Any]


class PageDict(TypedDict, total=False):
    type: str
    layout: str | dict[str, Any]
    master: str
    use_master: bool
    master_overrides: dict[str, Any]
    chrome: dict[str, Any]
    title: str
    subtitle: str
    blocks: list[BlockDict]
    notes: str
    hidden: bool
    metadata: dict[str, Any]


class DeckDict(TypedDict, total=False):
    schema_version: str
    title: str
    theme: str | dict[str, Any]
    default_master: str
    masters: dict[str, dict[str, Any]]
    pages: list[PageDict]
    metadata: dict[str, Any]
    export: dict[str, Any]
