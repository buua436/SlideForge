from __future__ import annotations

from dataclasses import dataclass

from ppt_ui.core.component import Component, RenderContext
from ppt_ui.core.layout import PageBox


@dataclass
class Slide(Component):
    title: str = ""

    def render(self, ctx: RenderContext, box: PageBox) -> None:
        raise NotImplementedError
