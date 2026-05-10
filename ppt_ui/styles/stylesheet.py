from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from ppt_ui.styles.style import Style


@dataclass(frozen=True)
class StyleTarget:
    """A style matching target.

    `type_name` is intentionally separate from class names because SlideForge
    component types use namespace dots such as `chart.line`.
    """

    type_name: str = ""
    id: str | None = None
    class_names: tuple[str, ...] = ()
    slot_name: str | None = None

    @classmethod
    def from_object(cls, value: object, *, type_name: str | None = None) -> "StyleTarget":
        return cls(
            type_name=type_name or str(getattr(value, "type", "")),
            id=getattr(value, "id", None),
            class_names=tuple(getattr(value, "class_names", ())),
            slot_name=getattr(value, "slot_name", None),
        )


@dataclass(frozen=True)
class Selector:
    """A compact selector supporting `*`, type, `#id`, and `.class`."""

    raw: str
    type_name: str | None = None
    id: str | None = None
    class_names: tuple[str, ...] = ()
    slot_name: str | None = None
    universal: bool = False

    @classmethod
    def parse(cls, raw: str) -> "Selector":
        selector = raw.strip()
        if not selector:
            raise ValueError("Selector cannot be empty.")
        slot_name: str | None = None
        if "::" in selector:
            selector, slot_name = selector.split("::", 1)
            selector = selector.strip() or "*"
            slot_name = slot_name.strip() or None
        if selector == "*":
            return cls(raw=raw, universal=True, slot_name=slot_name)

        if selector.startswith("#"):
            id_part, classes = _split_id_and_classes(selector[1:])
            return cls(raw=raw, id=id_part, class_names=classes, slot_name=slot_name)

        if selector.startswith("."):
            return cls(raw=raw, class_names=_split_classes(selector), slot_name=slot_name)

        if "#" in selector:
            type_part, remainder = selector.split("#", 1)
            id_part, classes = _split_id_and_classes(remainder)
            return cls(raw=raw, type_name=type_part or None, id=id_part, class_names=classes, slot_name=slot_name)

        # Bare selectors are exact type selectors. This avoids ambiguity with
        # namespaced component types such as `data.metric_cards`.
        return cls(raw=raw, type_name=selector, slot_name=slot_name)

    @property
    def specificity(self) -> tuple[int, int, int]:
        return (
            1 if self.id else 0,
            len(self.class_names),
            (0 if self.universal or not self.type_name else 1) + (1 if self.slot_name else 0),
        )

    def matches(self, target: StyleTarget) -> bool:
        if self.slot_name and self.slot_name != target.slot_name:
            return False
        if self.type_name and self.type_name != target.type_name:
            return False
        if self.id and self.id != target.id:
            return False
        target_classes = set(target.class_names)
        return all(class_name in target_classes for class_name in self.class_names)


@dataclass(frozen=True)
class StyleRule:
    selector: str
    style: Style = field(default_factory=Style)
    order: int = 0
    selectors: tuple[Selector, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.style, Mapping):
            object.__setattr__(self, "style", Style.from_dict(self.style))
        if not self.selectors:
            object.__setattr__(self, "selectors", tuple(Selector.parse(item) for item in self.selector.split(",") if item.strip()))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any], *, order: int = 0) -> "StyleRule":
        return cls(
            selector=str(data.get("selector", data.get("selectors", "*"))),
            style=Style.from_dict(data.get("style", data.get("props", {}))),
            order=int(data.get("order", order)),
        )

    def best_specificity(self, target: StyleTarget) -> tuple[int, int, int] | None:
        matches = [selector.specificity for selector in self.selectors if selector.matches(target)]
        return max(matches) if matches else None


@dataclass(frozen=True)
class StyleSheet:
    rules: tuple[StyleRule, ...] = ()

    @classmethod
    def from_value(cls, value: object) -> "StyleSheet":
        if value is None:
            return cls()
        if isinstance(value, StyleSheet):
            return value
        if isinstance(value, list):
            return cls(
                rules=tuple(
                    StyleRule.from_mapping(item, order=index)
                    for index, item in enumerate(value)
                    if isinstance(item, Mapping)
                )
            )
        if isinstance(value, Mapping):
            if isinstance(value.get("rules"), list):
                return cls.from_value(value.get("rules"))
            rules: list[StyleRule] = []
            for index, (selector, style_data) in enumerate(value.items()):
                if not isinstance(style_data, Mapping):
                    continue
                rules.append(StyleRule(selector=str(selector), style=Style.from_dict(style_data), order=index))
            return cls(rules=tuple(rules))
        raise TypeError(f"Unsupported stylesheet value: {value!r}")

    def matching_rules(self, target: StyleTarget) -> list[tuple[tuple[int, int, int], int, StyleRule]]:
        matches: list[tuple[tuple[int, int, int], int, StyleRule]] = []
        for rule in self.rules:
            specificity = rule.best_specificity(target)
            if specificity is not None:
                matches.append((specificity, rule.order, rule))
        return sorted(matches, key=lambda item: (item[0], item[1]))

    def resolve(self, target: StyleTarget | object, base: Style | Mapping[str, Any] | None = None) -> Style:
        style = Style.from_dict(base) if isinstance(base, Mapping) or base is None else base
        style_target = target if isinstance(target, StyleTarget) else StyleTarget.from_object(target)
        for _, _, rule in self.matching_rules(style_target):
            style = style.merge(rule.style)
        return style

    def extend(self, rules: Iterable[StyleRule]) -> "StyleSheet":
        return StyleSheet(rules=(*self.rules, *tuple(rules)))


def _split_classes(value: str) -> tuple[str, ...]:
    return tuple(item for item in value.split(".") if item)


def _split_id_and_classes(value: str) -> tuple[str, tuple[str, ...]]:
    id_part, *classes = value.split(".")
    return id_part, tuple(item for item in classes if item)
