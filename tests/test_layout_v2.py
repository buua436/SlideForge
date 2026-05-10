from pathlib import Path

from ppt_ui import basic, data, layout, page
from ppt_ui.core.presentation import Deck
from ppt_ui.schema.parser import deck_from_dict


def test_layout_card_json_renders_recursive_children(tmp_path: Path) -> None:
    deck = deck_from_dict(
        {
            "schema_version": "0.2",
            "pages": [
                {
                    "type": "page.blank",
                    "blocks": [
                        {
                            "type": "layout.card",
                            "layout": {"mode": "absolute", "x": 0.8, "y": 0.8, "w": 4.8, "h": 2.3},
                            "props": {
                                "recipe": {"model": "stack", "gap": 0.12, "padding": 0.22},
                                "children": [
                                    {
                                        "slot": "title",
                                        "type": "basic.text",
                                        "layout": {"height": 0.32},
                                        "props": {"text": "Container-first composition", "bold": True, "size": 16},
                                    },
                                    {
                                        "slot": "metric",
                                        "type": "data.metric_card",
                                        "layout": {"grow": 1},
                                        "props": {"label": "Reusable slots", "value": "7", "delta": "+1", "compare": "layout recipes"},
                                    },
                                ],
                            },
                        }
                    ],
                }
            ],
        }
    )

    assert deck.render(tmp_path / "layout_card_json.pptx").exists()


def test_layout_grid_python_api_renders_child_blocks(tmp_path: Path) -> None:
    deck = Deck()
    deck.add_page(
        page.blank(
            blocks=[
                layout.grid(
                    layout=layout.box(x=0.8, y=0.8, w=5.0, h=1.8),
                    columns=2,
                    rows=1,
                    gap=0.16,
                    padding=0.12,
                    children=[
                        basic.text(text="Left slot", bold=True, layout={"col": 1, "row": 1}),
                        data.metric_card(label="Right", value="42", delta="+8", compare="recursive child", layout={"col": 2, "row": 1}),
                    ],
                )
            ]
        )
    )

    assert deck.render(tmp_path / "layout_grid_api.pptx").exists()
