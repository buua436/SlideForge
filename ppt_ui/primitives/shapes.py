from __future__ import annotations

from dataclasses import dataclass

from ppt_ui.primitives.base import Primitive


@dataclass(frozen=True)
class Rect(Primitive):
    @property
    def type(self) -> str:
        return "rect"


@dataclass(frozen=True)
class Ellipse(Primitive):
    @property
    def type(self) -> str:
        return "ellipse"


@dataclass(frozen=True)
class Line(Primitive):
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0

    @property
    def type(self) -> str:
        return "line"


@dataclass(frozen=True)
class Connector(Line):
    arrow: str | None = None

    @property
    def type(self) -> str:
        return "connector"


@dataclass(frozen=True)
class Polygon(Primitive):
    points: tuple[tuple[float, float], ...] = ()

    @property
    def type(self) -> str:
        return "polygon"

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "points", tuple((float(x), float(y)) for x, y in self.points))


@dataclass(frozen=True)
class PathPrimitive(Primitive):
    commands: tuple[tuple[str, tuple[float, ...]], ...] = ()

    @property
    def type(self) -> str:
        return "path"

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "commands", tuple((cmd, tuple(values)) for cmd, values in self.commands))
