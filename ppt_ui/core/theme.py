from __future__ import annotations

import json
import re
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any


TOKEN_REF_RE = re.compile(r"\{([A-Za-z0-9_.]+)\}")
STYLE_FIELDS = {"fill", "border", "accent", "title", "body"}
_BUILTIN_THEME_NAMES = [
    "tech_blue",
    "glassmorphism",
    "claude",
    "glitch_art",
    "paper_cut",
    "neon_cyberpunk",
    "apple",
    "google",
]
TOKEN_ALIASES = {
    "colors": {
        "card": "surface_white",
        "text_muted": "text_tertiary",
    },
    "fonts": {
        "font_family": "family",
        "title_font_family": "title_font",
        "mono_font_family": "mono_font",
        "latin_font_family": "latin_font",
        "caption_font_family": "caption_font",
    },
    "spacing": {
        "content_gap": "gutter",
    },
    "radius": {
        "card_radius": "md",
    },
}


@dataclass(frozen=True)
class ColorTokens:
    background: str = "FFFFFF"
    surface: str = "F8FAFC"
    surface_alt: str = "EEF2FF"
    surface_white: str = "FFFFFF"
    primary: str = "2563EB"
    primary_dark: str = "1E3A8A"
    primary_soft: str = "EFF6FF"
    primary_tint: str = "DBEAFE"
    accent: str = "7C3AED"
    accent_soft: str = "F5F3FF"
    accent_tint: str = "EDE9FE"
    secondary: str = "64748B"
    success: str = "10B981"
    success_soft: str = "ECFDF5"
    warning: str = "F59E0B"
    warning_soft: str = "FFF7ED"
    danger: str = "EF4444"
    text_primary: str = "0F172A"
    text_secondary: str = "64748B"
    text_tertiary: str = "94A3B8"
    border: str = "E2E8F0"
    border_light: str = "EEF2F7"
    gray_50: str = "F8FAFC"
    gray_100: str = "F1F5F9"
    gray_200: str = "E2E8F0"
    gray_700: str = "334155"
    shadow_light: str = "F8FAFE"
    shadow_card: str = "F2F6FC"

    @property
    def text(self) -> str:
        return self.text_primary

    @property
    def muted(self) -> str:
        return self.text_secondary

    @property
    def text_muted(self) -> str:
        return self.text_tertiary

    @property
    def soft_blue(self) -> str:
        return self.primary_soft

    @property
    def soft_purple(self) -> str:
        return self.accent_soft


@dataclass(frozen=True)
class FontTokens:
    family: str = "Microsoft YaHei"
    title_font: str = ""
    mono_font: str = ""
    latin_font: str = ""
    caption_font: str = ""
    title_size: int = 36
    subtitle_size: int = 15
    h1_size: int = 28
    h2_size: int = 18
    body_size: int = 11
    caption_size: int = 10
    tiny_size: int = 8
    display_size: int = 54


@dataclass(frozen=True)
class SpacingTokens:
    base: int = 8
    xs: float = 0.08
    sm: float = 0.12
    md: float = 0.20
    lg: float = 0.32
    xl: float = 0.48
    page_margin: float = 0.55
    page_x: float = 0.55
    page_y: float = 0.45
    title_top: float = 0.48
    content_top: float = 1.55
    footer_y: float = 7.04
    gutter: float = 0.20
    card_padding: float = 0.22


@dataclass(frozen=True)
class RadiusTokens:
    sm: float = 0.035
    md: float = 0.055
    lg: float = 0.075


@dataclass(frozen=True)
class ShadowTokens:
    light_offset_x: float = 0.010
    light_offset_y: float = 0.014
    card_offset_x: float = 0.012
    card_offset_y: float = 0.018
    blur_radius: float = 0.0
    distance: float = 0.0
    opacity: float = 0.4
    direction: int = 5400000


@dataclass(frozen=True)
class GradientStop:
    color: str
    position: int = 0


@dataclass(frozen=True)
class GradientConfig:
    stops: tuple[GradientStop, ...] = ()
    angle: int = 5400000


@dataclass(frozen=True)
class ComponentStyle:
    fill: str
    border: str
    accent: str
    title: str
    body: str
    opacity: float = 1.0
    dash_style: int | None = None
    line_width: float | None = None
    shadow_blur: float | None = None


def default_component_styles() -> dict[str, ComponentStyle]:
    return {
        "card.default": ComponentStyle("FFFFFF", "E4ECF7", "2563EB", "08112F", "5B6B86"),
        "metric_card.default": ComponentStyle("FFFFFF", "E4ECF7", "2563EB", "08112F", "5B6B86"),
        "table.comparison": ComponentStyle("FFFFFF", "EEF3FA", "DBEAFE", "1E3A8A", "334155"),
        "timeline.status_cards": ComponentStyle("FFFFFF", "E4ECF7", "7C3AED", "08112F", "5B6B86"),
        "process_flow.compact_cards": ComponentStyle("FFFFFF", "E4ECF7", "2563EB", "08112F", "5B6B86"),
        "conclusion.hero": ComponentStyle("2563EB", "2563EB", "7C3AED", "FFFFFF", "FFFFFF"),
    }


@dataclass(frozen=True)
class Theme:
    name: str = "tech_blue"
    slide_width: float = 13.333
    slide_height: float = 7.5
    colors: ColorTokens = field(default_factory=ColorTokens)
    fonts: FontTokens = field(default_factory=FontTokens)
    spacing: SpacingTokens = field(default_factory=SpacingTokens)
    radius_tokens: RadiusTokens = field(default_factory=RadiusTokens)
    shadow: ShadowTokens = field(default_factory=ShadowTokens)
    component_styles: dict[str, ComponentStyle] = field(default_factory=default_component_styles)
    component_defaults: dict[str, dict[str, Any]] = field(default_factory=dict)
    chart_palette: list[str] = field(default_factory=lambda: ["2563EB", "7C3AED", "06B6D4", "10B981", "F59E0B", "EF4444"])
    card_shadow: bool = True
    gradient: GradientConfig = field(default_factory=GradientConfig)
    background_pattern: str = ""
    decorations: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def radius(self) -> float:
        return self.radius_tokens.md

    def component_style(self, family: str, variant: str = "default") -> ComponentStyle:
        style_keys = (
            f"{family}.{variant}",
            f"{family}.{variant}.default",
            f"{family}.default",
            "card.default",
        )
        for key in style_keys:
            default_style = self.component_defaults.get(key)
            if default_style:
                base = self.component_styles.get(key, self.component_styles["card.default"])
                return _component_style_from_mapping(default_style, base)
            if key in self.component_styles:
                return self.component_styles[key]
        return self.component_styles["card.default"]

    def component_default_style(self, type_name: str, variant: str | None = None) -> dict[str, Any]:
        """Return merged theme defaults for a component block."""

        variant_name = variant or "default"
        family = type_name.split(".", 1)[0]
        keys = [
            f"{family}.default",
            f"{type_name}.default",
        ]
        if variant_name != "default":
            keys.extend([f"{family}.{variant_name}", f"{type_name}.{variant_name}"])
        merged: dict[str, Any] = {}
        for key in keys:
            defaults = self.component_defaults.get(key)
            if defaults:
                merged = _deep_merge(merged, defaults)
        return deepcopy(merged)


@dataclass
class ThemeRegistry:
    themes: dict[str, Theme] = field(default_factory=dict)
    paths: dict[str, Path] = field(default_factory=dict)

    def register(self, name: str, theme: Theme) -> None:
        self.themes[name] = theme

    def register_path(self, name: str, path: str | Path) -> None:
        self.paths[name] = Path(path)

    def has(self, name: str) -> bool:
        return name in self.themes or name in self.paths

    def get(self, name: str) -> Theme | None:
        return self.themes.get(name)

    def get_path(self, name: str) -> Path | None:
        return self.paths.get(name)


class ThemeLoader:
    """Loads built-in, single-file, directory, and inline JSON themes."""

    def __init__(self, registry: ThemeRegistry | None = None) -> None:
        self.registry = registry or default_theme_registry()

    def load(self, source: str | Path | Mapping[str, Any] | Theme | None = None, *, base_dir: str | Path | None = None) -> Theme:
        return self._load(source, Path(base_dir) if base_dir is not None else None, [])

    def _load(self, source: str | Path | Mapping[str, Any] | Theme | None, base_dir: Path | None, stack: list[str]) -> Theme:
        if isinstance(source, Theme):
            return source
        if source is None or source == "":
            return self._load_builtin("default_blue", stack)
        if isinstance(source, Mapping):
            return self._load_mapping(source, base_dir, stack)

        source_text = str(source)
        if self.registry.has(source_text):
            path = self.registry.get_path(source_text)
            if path is not None:
                return self._load_path(path, path.parent, stack)
            return self._load_builtin(source_text, stack)

        path = Path(source_text)
        if not path.is_absolute() and base_dir is not None:
            path = base_dir / path
        if path.exists():
            return self._load_path(path, path.parent if path.is_file() else path, stack)

        raise ValueError(f"Unknown theme: {source_text}")

    def _load_builtin(self, name: str, stack: list[str]) -> Theme:
        if name == "default":
            name = "default_blue"
        if name in stack:
            raise ValueError(f"Circular theme extends detected: {' -> '.join([*stack, name])}")
        theme = self.registry.get(name)
        if theme is None:
            raise ValueError(f"Unknown theme: {name}")
        return theme

    def _load_path(self, path: Path, base_dir: Path, stack: list[str]) -> Theme:
        resolved = path.resolve()
        key = str(resolved)
        if key in stack:
            raise ValueError(f"Circular theme extends detected: {' -> '.join([*stack, key])}")
        if resolved.is_dir():
            return self._load_file(resolved / "theme.json", [*stack, key])
        return self._load_file(resolved, [*stack, key])

    def _load_file(self, path: Path, stack: list[str]) -> Theme:
        if not path.exists():
            raise FileNotFoundError(f"Theme file not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, Mapping):
            raise ValueError(f"Theme file must contain a JSON object: {path}")
        return self._load_mapping(data, path.parent, stack)

    def _load_mapping(self, data: Mapping[str, Any], base_dir: Path | None, stack: list[str]) -> Theme:
        parent = Theme()
        extends = data.get("extends")
        if extends:
            parent = self._load(extends, base_dir, stack)

        tokens = self._load_fragment(data.get("tokens", {}), base_dir)
        colors_data = _deep_merge(_flat_token_values(data, ColorTokens, TOKEN_ALIASES["colors"]), _deep_merge(tokens.get("colors", {}), data.get("colors", {})))
        fonts_data = _deep_merge(_flat_token_values(data, FontTokens, TOKEN_ALIASES["fonts"]), _deep_merge(tokens.get("fonts", {}), data.get("fonts", {})))
        spacing_data = _deep_merge(_flat_token_values(data, SpacingTokens, TOKEN_ALIASES["spacing"]), _deep_merge(tokens.get("spacing", {}), data.get("spacing", {})))
        radius_data = _deep_merge(_flat_token_values(data, RadiusTokens, TOKEN_ALIASES["radius"]), _deep_merge(tokens.get("radius", tokens.get("radius_tokens", {})), data.get("radius", data.get("radius_tokens", {}))))
        shadow_data = _deep_merge(tokens.get("shadow", {}), data.get("shadow", {}))

        colors = _merge_token_group(parent.colors, colors_data, strip_color_hash=True, aliases=TOKEN_ALIASES["colors"])
        fonts = _merge_token_group(parent.fonts, fonts_data, aliases=TOKEN_ALIASES["fonts"])
        spacing = _merge_token_group(parent.spacing, spacing_data, aliases=TOKEN_ALIASES["spacing"])
        radius = _merge_token_group(parent.radius_tokens, radius_data, aliases=TOKEN_ALIASES["radius"])
        shadow = _merge_token_group(parent.shadow, shadow_data)

        chart_palette = data.get("chart_palette", tokens.get("chart_palette", parent.chart_palette))
        if not isinstance(chart_palette, list):
            chart_palette = parent.chart_palette

        gradient = _load_gradient(data.get("gradient"), parent.gradient)
        background_pattern = str(data.get("background_pattern", parent.background_pattern))
        decorations = _deep_merge(parent.decorations, dict(data.get("decorations", {})))

        theme = Theme(
            name=str(data.get("name", parent.name)),
            slide_width=float(data.get("slide_width", parent.slide_width)),
            slide_height=float(data.get("slide_height", parent.slide_height)),
            colors=colors,
            fonts=fonts,
            spacing=spacing,
            radius_tokens=radius,
            shadow=shadow,
            component_styles=dict(parent.component_styles),
            component_defaults=deepcopy(parent.component_defaults),
            chart_palette=[_strip_hex_hash(str(color)) for color in chart_palette],
            card_shadow=bool(data.get("card_shadow", parent.card_shadow)),
            gradient=gradient,
            background_pattern=background_pattern,
            decorations=decorations,
            metadata=_deep_merge(parent.metadata, dict(data.get("metadata", {}))),
        )

        component_defaults = _deep_merge(theme.component_defaults, _theme_component_defaults(theme.colors, theme.chart_palette))
        component_defaults = _deep_merge(component_defaults, self._load_component_defaults(data, base_dir))
        component_defaults = _resolve_token_refs(component_defaults, theme)
        component_styles = _deep_merge_component_styles(theme.component_styles, self._load_component_styles(data, base_dir), theme)
        component_styles = _component_styles_from_defaults(component_styles, component_defaults)

        return Theme(
            name=theme.name,
            slide_width=theme.slide_width,
            slide_height=theme.slide_height,
            colors=theme.colors,
            fonts=theme.fonts,
            spacing=theme.spacing,
            radius_tokens=theme.radius_tokens,
            shadow=theme.shadow,
            component_styles=component_styles,
            component_defaults=component_defaults,
            chart_palette=theme.chart_palette,
            card_shadow=theme.card_shadow,
            gradient=theme.gradient,
            background_pattern=theme.background_pattern,
            decorations=theme.decorations,
            metadata=theme.metadata,
        )

    def _load_fragment(self, value: object, base_dir: Path | None) -> dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, Mapping):
            return dict(value)
        if isinstance(value, list):
            merged: dict[str, Any] = {}
            for item in value:
                merged = _deep_merge(merged, self._load_fragment(item, base_dir))
            return merged
        if isinstance(value, str):
            path = Path(value)
            if not path.is_absolute() and base_dir is not None:
                path = base_dir / path
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, Mapping):
                raise ValueError(f"Theme fragment must contain a JSON object: {path}")
            return dict(data)
        raise TypeError(f"Unsupported theme fragment: {value!r}")

    def _load_component_defaults(self, data: Mapping[str, Any], base_dir: Path | None) -> dict[str, dict[str, Any]]:
        raw_components = self._load_fragment(data.get("components", {}), base_dir)
        return _flatten_component_defaults(raw_components)

    def _load_component_styles(self, data: Mapping[str, Any], base_dir: Path | None) -> dict[str, Mapping[str, Any]]:
        raw_styles = self._load_fragment(data.get("component_styles", {}), base_dir)
        return {str(key): value for key, value in raw_styles.items() if isinstance(value, Mapping)}


def get_theme(source: str | Path | Mapping[str, Any] | Theme | None = None, *, base_dir: str | Path | None = None, registry: ThemeRegistry | None = None) -> Theme:
    return ThemeLoader(registry).load(source, base_dir=base_dir)


def builtin_theme_names() -> list[str]:
    return [f"theme.{name}" for name in _BUILTIN_THEME_NAMES]


_DEFAULT_THEME_REGISTRY: ThemeRegistry | None = None


def default_theme_registry() -> ThemeRegistry:
    global _DEFAULT_THEME_REGISTRY
    if _DEFAULT_THEME_REGISTRY is None:
        registry = ThemeRegistry()
        themes_dir = Path(__file__).resolve().parents[1] / "themes"
        for theme_name in _BUILTIN_THEME_NAMES:
            theme_path = themes_dir / f"{theme_name}.json"
            registry.register_path(theme_name, theme_path)
            registry.register_path(f"theme.{theme_name}", theme_path)
        tech_blue = themes_dir / "tech_blue.json"
        registry.register_path("default_blue", tech_blue)
        registry.register_path("theme.default_blue", tech_blue)
        registry.register_path("default", tech_blue)
        _DEFAULT_THEME_REGISTRY = registry
    return _DEFAULT_THEME_REGISTRY


def _theme_component_defaults(colors: ColorTokens, palette: list[str]) -> dict[str, dict[str, Any]]:
    return {
        "card.default": {
            "fill": colors.surface_white,
            "border": colors.border,
            "accent": colors.primary,
            "title": colors.text_primary,
            "body": colors.text_secondary,
            "shadow": True,
        },
        "basic.text.default": {
            "color": colors.text_secondary,
            "accent": colors.primary,
        },
        "data.metric_cards.default": {
            "fill": colors.surface_white,
            "border": colors.border,
            "accent": colors.primary,
        },
        "data.metric_cards.hero": {
            "fill": colors.primary_soft,
            "border": colors.primary_tint,
            "accent": colors.accent,
        },
        "data.progress.default": {
            "fill": colors.surface_white,
            "border": colors.border,
            "accent": colors.primary,
        },
        "chart.line.default": {
            "fill": colors.surface_white,
            "border": colors.border,
            "accent": colors.primary,
            "palette": palette,
            "line_width": 2.0,
        },
        "chart.bar.default": {
            "fill": colors.surface_white,
            "border": colors.border,
            "accent": colors.primary,
            "palette": palette,
        },
        "chart.pie.default": {
            "fill": colors.surface_white,
            "border": colors.border,
            "accent": colors.primary,
            "palette": palette,
        },
        "chart.donut.default": {
            "fill": colors.surface_white,
            "border": colors.border,
            "accent": colors.primary,
            "palette": palette,
        },
        "table.comparison.default": {
            "fill": colors.surface_white,
            "border": colors.border,
            "accent": colors.primary_tint,
            "title": colors.primary_dark,
            "body": colors.text_primary,
        },
        "table.basic.default": {
            "fill": colors.surface_white,
            "border": colors.border,
            "accent": colors.primary_tint,
            "title": colors.primary_dark,
            "body": colors.text_primary,
        },
        "narrative.timeline.default": {
            "fill": colors.surface_white,
            "border": colors.border,
            "accent": colors.accent,
        },
        "narrative.process_flow.default": {
            "fill": colors.surface_white,
            "border": colors.border,
            "accent": colors.primary,
        },
        "narrative.roadmap.default": {
            "fill": colors.surface_white,
            "border": colors.border,
            "accent": colors.primary,
            "palette": palette,
        },
        "media.icon.default": {
            "fill": colors.primary_soft,
            "border": colors.border,
            "accent": colors.primary,
        },
    }


def _field_dict(obj: object) -> dict[str, Any]:
    return {item.name: getattr(obj, item.name) for item in fields(obj)}


def _flat_token_values(data: Mapping[str, Any], token_type: type, aliases: Mapping[str, str] | None = None) -> dict[str, Any]:
    field_names = {item.name for item in fields(token_type)}
    result: dict[str, Any] = {}
    for key, value in data.items():
        normalized = aliases.get(str(key), str(key)) if aliases else str(key)
        if normalized in field_names:
            result[normalized] = value
    return result


def _merge_token_group(base: object, data: object, *, strip_color_hash: bool = False, aliases: Mapping[str, str] | None = None) -> object:
    if not isinstance(data, Mapping):
        return base
    values = _field_dict(base)
    for key, value in data.items():
        key = aliases.get(str(key), str(key)) if aliases else str(key)
        if key not in values:
            continue
        if strip_color_hash and isinstance(value, str):
            values[key] = _strip_hex_hash(value)
        else:
            values[key] = value
    return type(base)(**values)


def _strip_hex_hash(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"#?[0-9A-Fa-f]{6}", value):
        return value.lstrip("#").upper()
    return value


def _deep_merge(base: Mapping[str, Any], update: object) -> dict[str, Any]:
    result = deepcopy(dict(base))
    if not isinstance(update, Mapping):
        return result
    for key, value in update.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _flatten_component_defaults(data: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    flattened: dict[str, dict[str, Any]] = {}
    for component_name, raw_value in data.items():
        if not isinstance(raw_value, Mapping):
            continue
        component = str(component_name)
        if _looks_like_variant_map(raw_value):
            for variant, style in raw_value.items():
                if isinstance(style, Mapping):
                    flattened[f"{component}.{variant}"] = dict(style)
        else:
            flattened[f"{component}.default"] = dict(raw_value)
    return flattened


def _looks_like_variant_map(value: Mapping[str, Any]) -> bool:
    return bool(value) and all(isinstance(item, Mapping) for item in value.values())


def _resolve_token_refs(value: object, theme: Theme) -> Any:
    if isinstance(value, Mapping):
        return {key: _resolve_token_refs(item, theme) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_token_refs(item, theme) for item in value]
    if isinstance(value, str):
        return TOKEN_REF_RE.sub(lambda match: str(_lookup_theme_token(theme, match.group(1))), value)
    return value


def _lookup_theme_token(theme: Theme, path: str) -> Any:
    group, _, key = path.partition(".")
    if group == "radius":
        group = "radius_tokens"
    target = getattr(theme, group, None)
    if target is None or not key:
        return "{" + path + "}"
    return getattr(target, key, "{" + path + "}")


def _deep_merge_component_styles(
    base: Mapping[str, ComponentStyle],
    update: Mapping[str, Mapping[str, Any]],
    theme: Theme,
) -> dict[str, ComponentStyle]:
    merged = dict(base)
    for key, style_data in update.items():
        resolved = _resolve_token_refs(style_data, theme)
        base_style = merged.get(key, merged["card.default"])
        merged[key] = _component_style_from_mapping(resolved, base_style)
    return merged


def _component_styles_from_defaults(
    base: Mapping[str, ComponentStyle],
    defaults: Mapping[str, Mapping[str, Any]],
) -> dict[str, ComponentStyle]:
    merged = dict(base)
    for key, style_data in defaults.items():
        if not STYLE_FIELDS.intersection(style_data):
            continue
        base_style = merged.get(key, merged.get(_legacy_style_key(key), merged["card.default"]))
        merged[key] = _component_style_from_mapping(style_data, base_style)
    return merged


def _legacy_style_key(key: str) -> str:
    if key.endswith(".default"):
        return key.removesuffix(".default")
    return key


def _component_style_from_mapping(data: Mapping[str, Any], base: ComponentStyle) -> ComponentStyle:
    return ComponentStyle(
        fill=str(data.get("fill", base.fill)),
        border=str(data.get("border", base.border)),
        accent=str(data.get("accent", base.accent)),
        title=str(data.get("title", base.title)),
        body=str(data.get("body", base.body)),
        opacity=float(data.get("opacity", base.opacity)),
        dash_style=int(data["dash_style"]) if data.get("dash_style") is not None else base.dash_style,
        line_width=float(data["line_width"]) if data.get("line_width") is not None else base.line_width,
        shadow_blur=float(data["shadow_blur"]) if data.get("shadow_blur") is not None else base.shadow_blur,
    )


def _load_gradient(data: object, parent: GradientConfig) -> GradientConfig:
    if data is None:
        return parent
    if isinstance(data, Mapping):
        stops = []
        for item in data.get("stops", []):
            if isinstance(item, Mapping):
                stops.append(GradientStop(
                    color=_strip_hex_hash(str(item.get("color", "000000"))),
                    position=int(item.get("position", 0)),
                ))
        angle = int(data.get("angle", parent.angle))
        return GradientConfig(stops=tuple(stops) if stops else parent.stops, angle=angle)
    return parent
