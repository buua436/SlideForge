from __future__ import annotations

from dataclasses import dataclass

from ppt_ui.primitives.base import Primitive


@dataclass(frozen=True)
class TablePrimitive(Primitive):
    headers: tuple[str, ...] = ()
    rows: tuple[tuple[str, ...], ...] = ()

    @property
    def type(self) -> str:
        return "table"

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "headers", tuple(str(item) for item in self.headers))
        object.__setattr__(self, "rows", tuple(tuple(str(cell) for cell in row) for row in self.rows))
