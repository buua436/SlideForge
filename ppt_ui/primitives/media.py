from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ppt_ui.primitives.base import Primitive


@dataclass(frozen=True)
class ImagePrimitive(Primitive):
    src: str | Path = ""
    fit: str = "contain"
    alt: str = ""

    @property
    def type(self) -> str:
        return "image"


@dataclass(frozen=True)
class IconPrimitive(Primitive):
    name: str = ""
    provider: str | None = None
    icon_props: dict[str, Any] | None = None

    @property
    def type(self) -> str:
        return "icon"
