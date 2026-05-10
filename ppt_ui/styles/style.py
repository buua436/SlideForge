from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields, replace
from typing import Any


@dataclass(frozen=True)
class EdgeInsets:
    """Inset values in inches."""

    top: float = 0.0
    right: float = 0.0
    bottom: float = 0.0
    left: float = 0.0

    @classmethod
    def all(cls, value: float) -> "EdgeInsets":
        return cls(top=value, right=value, bottom=value, left=value)

    @classmethod
    def symmetric(cls, *, horizontal: float = 0.0, vertical: float = 0.0) -> "EdgeInsets":
        return cls(top=vertical, right=horizontal, bottom=vertical, left=horizontal)

    @classmethod
    def from_value(cls, value: object) -> "EdgeInsets":
        if value is None:
            return cls()
        if isinstance(value, EdgeInsets):
            return value
        if isinstance(value, (int, float)):
            return cls.all(float(value))
        if isinstance(value, (list, tuple)):
            items = [float(item) for item in value]
            if len(items) == 1:
                return cls.all(items[0])
            if len(items) == 2:
                return cls.symmetric(vertical=items[0], horizontal=items[1])
            if len(items) == 4:
                return cls(top=items[0], right=items[1], bottom=items[2], left=items[3])
        if isinstance(value, Mapping):
            return cls(
                top=float(value.get("top", 0.0)),
                right=float(value.get("right", 0.0)),
                bottom=float(value.get("bottom", 0.0)),
                left=float(value.get("left", 0.0)),
            )
        raise TypeError(f"Unsupported padding value: {value!r}")

    def to_dict(self) -> dict[str, float]:
        return {
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
            "left": self.left,
        }


@dataclass(frozen=True)
class Style:
    """CSS-like primitive style values.

    Values are intentionally renderer-neutral. They can reference theme tokens
    before the style resolver turns them into concrete PPT values.
    """

    fill: str | None = None
    stroke: str | None = None
    stroke_width: float | None = None
    color: str | None = None
    font_family: str | None = None
    font_size: int | None = None
    font_weight: str | None = None
    radius: float | str | None = None
    opacity: float | None = None
    shadow: bool | str | None = None
    padding: EdgeInsets | None = None
    align: str | None = None
    valign: str | None = None
    line_spacing: int | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "Style":
        if not data:
            return cls()

        normalized: dict[str, Any] = {}
        extras: dict[str, Any] = {}
        field_names = {item.name for item in fields(cls)}

        for key, value in data.items():
            style_key = _normalize_style_key(str(key), value)
            if style_key == "extras":
                if isinstance(value, Mapping):
                    extras.update(dict(value))
                continue
            if style_key == "padding":
                normalized[style_key] = EdgeInsets.from_value(value)
            elif style_key == "stroke_width":
                normalized[style_key] = float(value)
            elif style_key == "font_size":
                normalized[style_key] = int(value)
            elif style_key == "radius":
                try:
                    normalized[style_key] = float(value)
                except (TypeError, ValueError):
                    normalized[style_key] = value
            elif style_key == "opacity":
                normalized[style_key] = float(value)
            elif style_key == "font_weight" and isinstance(value, bool):
                normalized[style_key] = "bold" if value else None
            elif style_key in field_names:
                normalized[style_key] = value
            else:
                extras[key] = value

        if "bold" in data and "font_weight" not in normalized:
            normalized["font_weight"] = "bold" if data.get("bold") else None

        return cls(**normalized, extras=extras)

    def merge(self, *others: "Style | Mapping[str, Any] | None") -> "Style":
        """Return a style where later styles override earlier values."""

        current = self
        field_names = [item.name for item in fields(self) if item.name != "extras"]
        for item in others:
            other = Style.from_dict(item) if isinstance(item, Mapping) or item is None else item
            values: dict[str, Any] = {}
            for name in field_names:
                value = getattr(other, name)
                if value is not None:
                    values[name] = value
            values["extras"] = {**current.extras, **other.extras}
            current = replace(current, **values)
        return current

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for item in fields(self):
            if item.name == "extras":
                continue
            value = getattr(self, item.name)
            if value is None:
                continue
            if isinstance(value, EdgeInsets):
                data[item.name] = value.to_dict()
            else:
                data[item.name] = value
        data.update(self.extras)
        return data

    @property
    def bold(self) -> bool:
        return self.font_weight in {"bold", "600", "700", "800", "900"}


def _normalize_style_key(key: str, value: object) -> str:
    aliases = {
        "border": "stroke",
        "line": "stroke",
        "strokeWidth": "stroke_width",
        "stroke-width": "stroke_width",
        "line_width": "stroke_width",
        "size": "font_size",
        "fontSize": "font_size",
        "font-size": "font_size",
        "fontFamily": "font_family",
        "font-family": "font_family",
        "fontWeight": "font_weight",
        "font-weight": "font_weight",
        "bold": "font_weight",
        "vertical_align": "valign",
        "verticalAlign": "valign",
        "text_align": "align",
        "textAlign": "align",
        "lineSpacing": "line_spacing",
        "line-spacing": "line_spacing",
    }
    if key == "bold" and isinstance(value, bool):
        return "font_weight"
    return aliases.get(key, key)
