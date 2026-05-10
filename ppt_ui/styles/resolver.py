from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ppt_ui.styles.style import Style
from ppt_ui.styles.stylesheet import StyleSheet, StyleTarget


TOKEN_REF_RE = re.compile(r"\{([A-Za-z0-9_.]+)\}")


@dataclass(frozen=True)
class StyleResolver:
    """Resolve theme tokens and merge style layers.

    Cascade order:
    base -> theme defaults -> stylesheet rules -> inline/block style.
    """

    theme: object
    stylesheet: StyleSheet = field(default_factory=StyleSheet)

    def resolve(
        self,
        target: StyleTarget | object,
        *,
        base: Style | Mapping[str, Any] | None = None,
        theme_defaults: Style | Mapping[str, Any] | None = None,
        inline: Style | Mapping[str, Any] | None = None,
    ) -> Style:
        style = Style.from_dict(base) if isinstance(base, Mapping) or base is None else base
        style = style.merge(theme_defaults)
        style = self.stylesheet.resolve(target, base=style)
        style = style.merge(inline)
        return self.resolve_style(style)

    def resolve_style(self, style: Style | Mapping[str, Any] | None) -> Style:
        source = Style.from_dict(style) if isinstance(style, Mapping) or style is None else style
        resolved = self.resolve_value(source.to_dict())
        if not isinstance(resolved, Mapping):
            return Style()
        return Style.from_dict(resolved)

    def resolve_value(self, value: object) -> Any:
        if isinstance(value, Mapping):
            return {key: self.resolve_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.resolve_value(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self.resolve_value(item) for item in value)
        if isinstance(value, str):
            return TOKEN_REF_RE.sub(lambda match: str(self.lookup_token(match.group(1))), value)
        return value

    def lookup_token(self, path: str) -> Any:
        parts = path.split(".")
        if not parts:
            return "{" + path + "}"
        if parts[0] == "radius":
            parts[0] = "radius_tokens"

        current: Any = self.theme
        for part in parts:
            if isinstance(current, Mapping):
                current = current.get(part)
            elif isinstance(current, (list, tuple)) and part.isdigit():
                index = int(part)
                current = current[index] if 0 <= index < len(current) else None
            else:
                current = getattr(current, part, None)

            if current is None:
                return "{" + path + "}"
        return current
