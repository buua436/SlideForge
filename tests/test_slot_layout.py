import pytest

from ppt_ui.core.layout import Box, SlotLayoutEngine, SlotNode


def assert_box(box: Box, expected: tuple[float, float, float, float]) -> None:
    assert box.x == pytest.approx(expected[0])
    assert box.y == pytest.approx(expected[1])
    assert box.w == pytest.approx(expected[2])
    assert box.h == pytest.approx(expected[3])


def test_slot_stack_layout_supports_padding_gap_fixed_and_grow() -> None:
    result = SlotLayoutEngine().layout(
        Box(0, 0, 4, 4),
        [
            SlotNode("title", layout={"height": 1.0}),
            SlotNode("body", layout={"grow": 1}),
            SlotNode("footer", layout={"height": 0.5}),
        ],
        {"model": "stack", "gap": 0.1, "padding": 0.2},
    )

    assert_box(result.root, (0.2, 0.2, 3.6, 3.6))
    assert_box(result.box("title"), (0.2, 0.2, 3.6, 1.0))
    assert_box(result.box("body"), (0.2, 1.3, 3.6, 1.9))
    assert_box(result.box("footer"), (0.2, 3.3, 3.6, 0.5))


def test_slot_row_layout_supports_fixed_and_flexible_widths() -> None:
    result = SlotLayoutEngine().layout(
        Box(0, 0, 6, 2),
        [
            SlotNode("icon", layout={"width": 1.0}),
            SlotNode("content", layout={"grow": 1}),
            SlotNode("action", layout={"width": 1.5}),
        ],
        {"model": "row", "gap": 0.25},
    )

    assert_box(result.box("icon"), (0, 0, 1.0, 2.0))
    assert_box(result.box("content"), (1.25, 0, 3.0, 2.0))
    assert_box(result.box("action"), (4.5, 0, 1.5, 2.0))


def test_slot_grid_layout_supports_explicit_cell_spans() -> None:
    result = SlotLayoutEngine().layout(
        Box(0, 0, 12, 6),
        [
            SlotNode("a"),
            SlotNode("b", layout={"col": 2, "row": 2, "span": 2}),
        ],
        {"model": "grid", "columns": 3, "rows": 2, "gap": 0.2},
    )

    assert_box(result.box("a"), (0, 0, 3.8666666667, 2.9))
    assert_box(result.box("b"), (4.0666666667, 3.1, 7.9333333333, 2.9))


def test_slot_template_layout_resolves_named_areas() -> None:
    result = SlotLayoutEngine().layout(
        Box(0, 0, 4, 2),
        ["icon", "label", "value"],
        {"model": "template", "gap": 0.1, "areas": ["icon label", "icon value"]},
    )

    assert_box(result.box("icon"), (0, 0, 1.95, 2.0))
    assert_box(result.box("label"), (2.05, 0, 1.95, 0.95))
    assert_box(result.box("value"), (2.05, 1.05, 1.95, 0.95))


def test_slot_dock_layout_consumes_edges_before_center() -> None:
    result = SlotLayoutEngine().layout(
        Box(0, 0, 10, 5),
        [
            SlotNode("top", layout={"dock": "top", "height": 1.0}),
            SlotNode("rail", layout={"dock": "left", "width": 2.0}),
            SlotNode("content", layout={"dock": "center"}),
        ],
        {"model": "dock", "gap": 0.1},
    )

    assert_box(result.box("top"), (0, 0, 10, 1.0))
    assert_box(result.box("rail"), (0, 1.1, 2.0, 3.9))
    assert_box(result.box("content"), (2.1, 1.1, 7.9, 3.9))


def test_slot_overlay_layout_supports_anchor_and_explicit_offsets() -> None:
    result = SlotLayoutEngine().layout(
        Box(0, 0, 10, 5),
        [
            SlotNode("background"),
            SlotNode("badge", layout={"anchor": "bottom-right", "width": 2.0, "height": 1.0}),
            SlotNode("note", layout={"x": 1.0, "y": 0.5, "w": 3.0, "h": 0.6}),
        ],
        {"model": "overlay"},
    )

    assert_box(result.box("background"), (0, 0, 10, 5))
    assert_box(result.box("badge"), (8, 4, 2, 1))
    assert_box(result.box("note"), (1, 0.5, 3, 0.6))


def test_slot_flow_layout_wraps_items() -> None:
    result = SlotLayoutEngine().layout(
        Box(0, 0, 3, 3),
        ["a", "b", "c"],
        {"model": "flow", "gap": 0.1, "item_width": 1.2, "item_height": 0.4},
    )

    assert_box(result.box("a"), (0, 0, 1.2, 0.4))
    assert_box(result.box("b"), (1.3, 0, 1.2, 0.4))
    assert_box(result.box("c"), (0, 0.5, 1.2, 0.4))


def test_slot_layout_flattens_nested_child_slots() -> None:
    result = SlotLayoutEngine().layout(
        Box(0, 0, 4, 2),
        [
            SlotNode(
                "card",
                children=(SlotNode("label", layout={"height": 0.4}), SlotNode("value")),
                layout={"recipe": {"model": "stack", "gap": 0.1}},
            )
        ],
        {"model": "overlay"},
    )

    assert_box(result.box("card"), (0, 0, 4, 2))
    assert_box(result.box("card.label"), (0, 0, 4, 0.4))
    assert_box(result.box("card.value"), (0, 0.5, 4, 1.5))
