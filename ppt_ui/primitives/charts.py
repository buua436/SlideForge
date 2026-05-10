from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ppt_ui.primitives.base import Primitive


@dataclass(frozen=True)
class ChartSeries:
    name: str
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", tuple(float(value) for value in self.values))


@dataclass(frozen=True)
class ChartPrimitive(Primitive):
    chart_type: str = "line"
    categories: tuple[str, ...] = ()
    series: tuple[ChartSeries, ...] = ()
    labels: tuple[str, ...] = ()
    values: tuple[float, ...] = ()
    options: dict[str, Any] | None = None

    @property
    def type(self) -> str:
        return "chart"

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "categories", tuple(str(item) for item in self.categories))
        object.__setattr__(self, "series", tuple(self.series))
        object.__setattr__(self, "labels", tuple(str(item) for item in self.labels))
        object.__setattr__(self, "values", tuple(float(item) for item in self.values))
