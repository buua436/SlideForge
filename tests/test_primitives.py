from ppt_ui.core.layout import Box
from ppt_ui.primitives import Group, Rect, Text, normalize_class_names
from ppt_ui.styles import EdgeInsets, Style


def test_style_from_dict_normalizes_aliases() -> None:
    style = Style.from_dict(
        {
            "border": "#E2E8F0",
            "strokeWidth": 1.25,
            "size": 14,
            "bold": True,
            "padding": [0.1, 0.2],
            "custom": "kept",
        }
    )

    assert style.stroke == "#E2E8F0"
    assert style.stroke_width == 1.25
    assert style.font_size == 14
    assert style.font_weight == "bold"
    assert style.padding == EdgeInsets.symmetric(vertical=0.1, horizontal=0.2)
    assert style.extras["custom"] == "kept"


def test_style_merge_uses_later_values() -> None:
    base = Style(fill="FFFFFF", color="0F172A")
    override = Style(color="2563EB")

    merged = base.merge(override)

    assert merged.fill == "FFFFFF"
    assert merged.color == "2563EB"


def test_primitive_tree_walk_preserves_order() -> None:
    tree = Group(children=(Rect(id="surface", box=Box(0, 0, 2, 1)), Text(id="label", text="Hello")))

    assert [item.id for item in tree.walk()] == [None, "surface", "label"]


def test_class_name_normalization() -> None:
    assert normalize_class_names("hero card  active") == ("hero", "card", "active")
    assert normalize_class_names(["hero", "card"]) == ("hero", "card")
