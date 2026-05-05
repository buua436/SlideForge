from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ppt_ui.components.registry import build_default_component_registry
from ppt_ui.core.diagnostics import Diagnostic
from ppt_ui.core.master import MasterRegistry
from ppt_ui.core.page import Page
from ppt_ui.core.registry import ComponentRegistry
from ppt_ui.core.theme import Theme
from ppt_ui.icons.provider import IconRegistry, default_icon_registry
from ppt_ui.renderer.pptx_renderer import PptxRenderer


@dataclass
class Deck:
    pages: list[Page] = field(default_factory=list)
    theme: Theme = field(default_factory=Theme)
    title: str = "SlideForge Deck"
    default_master: str = "tech_blue"
    masters: MasterRegistry = field(default_factory=MasterRegistry.with_defaults)
    components: ComponentRegistry = field(default_factory=build_default_component_registry)
    icons: IconRegistry = field(default_factory=default_icon_registry)
    metadata: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    def add_page(self, page: Page) -> None:
        self.pages.append(page)

    def render(self, output_path: str | Path) -> Path:
        renderer = PptxRenderer(self.theme, icon_registry=self.icons)
        renderer.render_deck(self)
        return renderer.save(output_path)
