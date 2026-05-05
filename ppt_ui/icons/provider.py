from __future__ import annotations

import re
import hashlib
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_ICON_ALIASES = {
    "bi": "bi",
    "bootstrap": "bi",
    "boxicons": "bx",
    "boxicons-regular": "bx",
    "boxicons-solid": "bxs",
    "bx": "bx",
    "bxs": "bxs",
    "carbon": "carbon",
    "fa": "fa6-solid",
    "fa-brands": "fa6-brands",
    "fa-regular": "fa6-regular",
    "fa-solid": "fa6-solid",
    "fluent": "fluent",
    "fontawesome": "fa6-solid",
    "hero": "heroicons",
    "heroicon": "heroicons",
    "heroicons": "heroicons",
    "hugeicons": "hugeicons",
    "iconamoon": "iconamoon",
    "lucide": "lucide",
    "material": "material-symbols",
    "material-symbols": "material-symbols",
    "mdi": "mdi",
    "mingcute": "mingcute",
    "octicon": "octicon",
    "ph": "ph",
    "phosphor": "ph",
    "radix": "radix-icons",
    "radix-icons": "radix-icons",
    "remix": "ri",
    "remixicon": "ri",
    "ri": "ri",
    "simple": "simple-icons",
    "simple-icons": "simple-icons",
    "solar": "solar",
    "tabler": "tabler",
}


def default_icon_aliases() -> dict[str, str]:
    return dict(DEFAULT_ICON_ALIASES)


@dataclass(frozen=True)
class IconRequest:
    """Normalized icon lookup and rendering options."""

    prefix: str
    name: str
    color: str = "currentColor"
    width: int | None = None
    height: int | None = None
    rotate: str | None = None
    flip: str | None = None
    stroke_width: float | None = None

    @property
    def icon_id(self) -> str:
        return f"{self.prefix}:{self.name}"


def normalize_icon_name(icon_id: str, aliases: Mapping[str, str] | None = None) -> tuple[str, str] | None:
    """Accept frontend-like `lucide.sparkles` and Iconify-like `lucide:sparkles`."""

    value = icon_id.strip()
    if not value:
        return None
    if ":" in value:
        prefix, _, name = value.partition(":")
    elif "." in value:
        prefix, _, name = value.partition(".")
    else:
        return None
    alias_map = aliases or DEFAULT_ICON_ALIASES
    prefix = alias_map.get(prefix.lower(), prefix.lower())
    name = name.strip()
    if not prefix or not name:
        return None
    return prefix, name


def _apply_svg_overrides(svg: str, request: IconRequest) -> str:
    if request.stroke_width is not None:
        value = f'{request.stroke_width:g}'
        if re.search(r"stroke-width=(['\"])[^'\"]+\1", svg):
            svg = re.sub(r"stroke-width=(['\"])[^'\"]+\1", f'stroke-width="{value}"', svg)
        else:
            svg = svg.replace("<svg ", f'<svg stroke-width="{value}" ', 1)
    return svg


class IconProvider(Protocol):
    """Source adapter for frontend-style icon libraries."""

    def resolve_svg(self, request: IconRequest) -> str | None:
        raise NotImplementedError


@dataclass
class IconRegistry:
    providers: list[IconProvider] = field(default_factory=list)
    aliases: dict[str, str] = field(default_factory=default_icon_aliases)

    def register(self, provider: IconProvider) -> None:
        self.providers.append(provider)

    def register_alias(self, alias: str, prefix: str) -> None:
        self.aliases[alias.strip().lower()] = prefix.strip().lower()

    def normalize(self, icon_id: str) -> tuple[str, str] | None:
        return normalize_icon_name(icon_id, self.aliases)

    def create_request(
        self,
        name: str,
        *,
        color: str = "currentColor",
        size: int | None = None,
        width: int | None = None,
        height: int | None = None,
        rotate: str | int | None = None,
        flip: str | None = None,
        stroke_width: float | None = None,
    ) -> IconRequest | None:
        return icon_request_from_props(
            name,
            color=color,
            size=size,
            width=width,
            height=height,
            rotate=rotate,
            flip=flip,
            stroke_width=stroke_width,
            aliases=self.aliases,
        )

    def resolve_svg(self, request: IconRequest) -> str | None:
        for provider in self.providers:
            svg = provider.resolve_svg(request)
            if svg is not None:
                return _apply_svg_overrides(svg, request)
        return None


@dataclass
class LocalSvgIconProvider:
    root: Path
    prefix: str | None = None

    def resolve_svg(self, request: IconRequest) -> str | None:
        if self.prefix and request.prefix != self.prefix:
            return None
        path = (self.root / f"{request.icon_id.replace(':', '_')}.svg").resolve()
        if not path.exists() or not path.is_file():
            path = (self.root / f"{request.name}.svg").resolve()
        if not path.exists() or not path.is_file():
            return None
        svg = path.read_text(encoding="utf-8")
        return svg.replace("currentColor", request.color)


@dataclass
class IconifyJsonProvider:
    """Resolve icons from an Iconify icon-set JSON object."""

    prefix: str
    icon_set: Mapping[str, object]

    def resolve_svg(self, request: IconRequest) -> str | None:
        if request.prefix != self.prefix:
            return None
        icons = self.icon_set.get("icons")
        if not isinstance(icons, Mapping):
            return None
        icon = icons.get(request.name)
        if not isinstance(icon, Mapping):
            return None
        body = icon.get("body")
        if not isinstance(body, str):
            return None
        width = int(request.width or icon.get("width", self.icon_set.get("width", 24)))
        height = int(request.height or icon.get("height", self.icon_set.get("height", 24)))
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" fill="none" stroke="{request.color}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
        )


@dataclass
class IconifyApiProvider:
    """Resolve icons from the public Iconify API without requiring local icon files."""

    base_url: str = "https://api.iconify.design"
    timeout: float = 8.0
    cache_dir: Path | None = None
    disable_cache: bool = False

    def resolve_svg(self, request: IconRequest) -> str | None:
        query: dict[str, str] = {}
        if request.color and request.color != "currentColor":
            query["color"] = request.color
        if request.width:
            query["width"] = str(request.width)
        if request.height:
            query["height"] = str(request.height)
        if request.rotate:
            query["rotate"] = str(request.rotate)
        if request.flip:
            query["flip"] = str(request.flip)
        query["box"] = "true"
        suffix = f"?{urlencode(query)}" if query else ""
        url = f"{self.base_url.rstrip('/')}/{request.prefix}/{request.name}.svg{suffix}"
        cache_path = self._cache_path(url)
        if cache_path and cache_path.exists():
            return cache_path.read_text(encoding="utf-8")
        try:
            req = Request(url, headers={"User-Agent": "SlideForge/0.1"})
            with urlopen(req, timeout=self.timeout) as response:
                data = response.read()
        except (HTTPError, URLError, TimeoutError, ValueError):
            return None
        try:
            svg = data.decode("utf-8")
        except UnicodeDecodeError:
            return None
        if "<svg" not in svg:
            return None
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(svg, encoding="utf-8")
        return svg

    def _cache_path(self, url: str) -> Path | None:
        if self.disable_cache:
            return None
        root = self.cache_dir or Path(tempfile.gettempdir()) / "slideforge" / "iconify_svg"
        key = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return root / f"{key}.svg"


@dataclass
class UrlTemplateIconProvider:
    """Resolve SVG from a custom HTTP endpoint.

    The template can use `{prefix}`, `{name}`, `{color}`, `{color_hex}`,
    `{width}`, and `{height}` placeholders.
    """

    url_template: str
    prefixes: set[str] | None = None
    timeout: float = 8.0

    def resolve_svg(self, request: IconRequest) -> str | None:
        if self.prefixes and request.prefix not in self.prefixes:
            return None
        values = {
            "prefix": request.prefix,
            "name": request.name,
            "color": request.color,
            "color_hex": request.color.lstrip("#"),
            "width": str(request.width or ""),
            "height": str(request.height or request.width or ""),
        }
        try:
            url = self.url_template.format(**values)
            req = Request(url, headers={"User-Agent": "SlideForge/0.1"})
            with urlopen(req, timeout=self.timeout) as response:
                data = response.read()
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError):
            return None
        try:
            svg = data.decode("utf-8")
        except UnicodeDecodeError:
            return None
        return svg if "<svg" in svg else None


def icon_request_from_props(
    name: str,
    *,
    color: str = "currentColor",
    size: int | None = None,
    width: int | None = None,
    height: int | None = None,
    rotate: str | int | None = None,
    flip: str | None = None,
    stroke_width: float | None = None,
    aliases: Mapping[str, str] | None = None,
) -> IconRequest | None:
    normalized = normalize_icon_name(name, aliases)
    if normalized is None:
        return None
    prefix, icon_name = normalized
    return IconRequest(
        prefix=prefix,
        name=icon_name,
        color=color,
        width=width or size,
        height=height or size,
        rotate=str(rotate) if rotate not in (None, "") else None,
        flip=flip or None,
        stroke_width=stroke_width,
    )


def default_icon_registry() -> IconRegistry:
    registry = IconRegistry()
    registry.register(IconifyApiProvider())
    return registry
