from dataclasses import dataclass

from ppt_ui.components.data_v2 import DataMetricCardComponent
from ppt_ui.components.layout_v2 import LayoutContainerComponent
from ppt_ui.core.component import ComponentSlot
from ppt_ui.core.component import Component, RenderContext
from ppt_ui.core.layout import Box
from ppt_ui.core.theme import get_theme
from ppt_ui.primitives import Primitive, Rect, Text
from ppt_ui.renderer.pptx_renderer import PptxRenderer
from ppt_ui.styles import Style, StyleSheet


@dataclass
class PrimitiveBadge(Component):
    label: str

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> list[Primitive]:
        return [
            Rect(box=box, class_names=("badge",), style=Style(fill="{colors.primary_soft}", stroke="{colors.border}", radius=0.05)),
            Text(box=box.inset(0.10, 0.06), class_names=("badge-label",), text=self.label, style=Style(font_size=12, font_weight="bold")),
        ]


def test_component_default_render_uses_primitive_tree(tmp_path) -> None:
    renderer = PptxRenderer(get_theme("theme.tech_blue"))
    slide = renderer.prs.slides.add_slide(renderer.prs.slide_layouts[6])
    ctx = RenderContext(
        slide=slide,
        theme=renderer.theme,
        renderer=renderer,
        stylesheet=StyleSheet.from_value({".badge-label": {"color": "{colors.primary}"}}),
    )

    PrimitiveBadge("Ready").render(ctx, Box(0.8, 0.8, 1.6, 0.42))
    output = renderer.save(tmp_path / "component_contract.pptx")

    assert output.exists()
    assert len(slide.shapes) >= 2


def test_component_slot_contract_defaults_to_empty() -> None:
    assert PrimitiveBadge.slot_contract() == ()
    assert PrimitiveBadge.slot_names() == ()


def test_component_slot_can_be_converted_to_slot_node() -> None:
    slot = ComponentSlot("value", role="text", required=True, default_layout={"height": 0.4})
    node = slot.to_slot_node()

    assert node.name == "value"
    assert node.layout["height"] == 0.4
    assert node.metadata["role"] == "text"


def test_metric_card_declares_stable_slots() -> None:
    names = DataMetricCardComponent.slot_names()

    assert names == ("root", "surface", "label", "value", "delta", "compare", "icon")


def test_layout_container_declares_recursive_child_slot() -> None:
    names = LayoutContainerComponent.slot_names()

    assert "children" in names
