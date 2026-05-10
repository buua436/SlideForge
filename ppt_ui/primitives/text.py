from __future__ import annotations

from dataclasses import dataclass, field

from ppt_ui.primitives.base import Primitive
from ppt_ui.styles import Style


@dataclass(frozen=True)
class TextRun:
    text: str
    style: Style = field(default_factory=Style)


@dataclass(frozen=True)
class Text(Primitive):
    text: str = ""

    @property
    def type(self) -> str:
        return "text"


@dataclass(frozen=True)
class RichText(Primitive):
    runs: tuple[TextRun, ...] = ()

    @property
    def type(self) -> str:
        return "rich_text"

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "runs", tuple(self.runs))
