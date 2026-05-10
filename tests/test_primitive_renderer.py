from pathlib import Path

from ppt_ui.core.layout import Box
from ppt_ui.core.theme import get_theme
from ppt_ui.primitives import ChartPrimitive, ChartSeries, Group, IconPrimitive, Line, Rect, TablePrimitive, Text
from ppt_ui.renderer.pptx_renderer import PptxRenderer
from ppt_ui.styles import Style, StyleSheet


def test_pptx_renderer_renders_primitive_tree(tmp_path: Path) -> None:
    renderer = PptxRenderer(get_theme("theme.tech_blue"))
    slide = renderer.prs.slides.add_slide(renderer.prs.slide_layouts[6])
    renderer.background(slide)

    tree = Group(
        children=(
            Rect(box=Box(0.6, 0.6, 3.0, 0.8), class_names=("card",), style=Style(fill="{colors.surface_white}", stroke="{colors.border}", radius=0.05)),
            Text(box=Box(0.8, 0.78, 2.6, 0.32), class_names=("headline",), text="Primitive Title"),
            Line(x1=0.6, y1=1.6, x2=3.6, y2=1.6, style=Style(stroke="{colors.primary}", stroke_width=1.2)),
            IconPrimitive(box=Box(0.6, 1.85, 0.45, 0.45), name="sparkles", style=Style(color="{colors.accent}", font_size=9)),
            TablePrimitive(box=Box(0.6, 2.5, 3.4, 1.1), headers=("A", "B"), rows=(("1", "2"), ("3", "4"))),
            ChartPrimitive(
                box=Box(4.4, 0.6, 4.2, 2.4),
                chart_type="line",
                categories=("A", "B", "C"),
                series=(ChartSeries("S1", (1, 2, 3)), ChartSeries("S2", (3, 2, 4))),
            ),
        )
    )

    shapes = renderer.render_tree(slide, tree, stylesheet=StyleSheet.from_value({".headline": {"color": "{colors.primary}", "font_size": 18}}))
    output = renderer.save(tmp_path / "primitive_tree.pptx")

    assert shapes
    assert output.exists()


def test_group_inherits_text_style_but_not_surface_fill() -> None:
    theme = get_theme("theme.tech_blue")
    renderer = PptxRenderer(theme)
    slide = renderer.prs.slides.add_slide(renderer.prs.slide_layouts[6])
    tree = Group(
        style=Style(color="{colors.accent}", font_size=18, fill="EF4444"),
        children=(
            Text(box=Box(0.5, 0.5, 2.0, 0.4), text="Inherited"),
            Rect(box=Box(0.5, 1.1, 1.0, 0.5), style=Style(stroke="{colors.border}")),
        ),
    )

    shapes = renderer.render_tree(slide, tree)

    text_shape = shapes[0]
    rect_shape = shapes[1]
    run = text_shape.text_frame.paragraphs[0].runs[0]
    assert str(run.font.color.rgb) == theme.colors.accent
    assert run.font.size.pt == 18
    assert str(rect_shape.fill.fore_color.rgb) == theme.colors.surface_white
