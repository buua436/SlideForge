from ppt_ui.core.theme import get_theme
from ppt_ui.primitives import Text
from ppt_ui.renderer.pptx_renderer import PptxRenderer
from ppt_ui.styles import Style, StyleResolver, StyleSheet, StyleTarget


def test_style_resolver_cascade_order() -> None:
    resolver = StyleResolver(
        theme=get_theme("theme.tech_blue"),
        stylesheet=StyleSheet.from_value(
            {
                "chart.line": {"color": "{colors.text_secondary}", "stroke_width": 1.5},
                ".hero": {"color": "{colors.accent}"},
            }
        ),
    )

    style = resolver.resolve(
        StyleTarget(type_name="chart.line", class_names=("hero",)),
        base=Style(fill="FFFFFF", color="111111"),
        theme_defaults={"fill": "{colors.surface_white}", "stroke": "{colors.border}"},
        inline={"stroke_width": 3.0},
    )

    assert style.fill == "FFFFFF"
    assert style.stroke == "E2E8F0"
    assert style.color == "7C3AED"
    assert style.stroke_width == 3.0


def test_style_resolver_keeps_unknown_token_literal() -> None:
    resolver = StyleResolver(theme=get_theme("theme.tech_blue"))

    assert resolver.resolve_value("{colors.not_real}") == "{colors.not_real}"


def test_style_resolver_supports_list_tokens() -> None:
    resolver = StyleResolver(theme=get_theme("theme.tech_blue"))

    assert resolver.resolve_value("{chart_palette.0}") == "2563EB"


def test_renderer_applies_slot_selector_after_component_default_style() -> None:
    theme = get_theme("theme.tech_blue")
    renderer = PptxRenderer(theme)
    resolver = StyleResolver(
        theme=theme,
        stylesheet=StyleSheet.from_value({"data.metric_card::value": {"color": "{colors.accent}", "font_size": 30}}),
    )
    primitive = Text(
        text="92.3%",
        style=Style(color="{colors.text_primary}", font_size=20),
        metadata={"component_type": "data.metric_card", "slot": "value"},
    )

    style = renderer._primitive_style(primitive, resolver)

    assert style.color == "7C3AED"
    assert style.font_size == 30
