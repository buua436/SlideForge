from pathlib import Path

from ppt_ui import layout, page, table
from ppt_ui.core.presentation import Deck
from ppt_ui.schema.parser import deck_from_dict


def test_table_v2_json_components_render(tmp_path: Path) -> None:
    deck = deck_from_dict(
        {
            "schema_version": "0.2",
            "pages": [
                {
                    "type": "page.blank",
                    "blocks": [
                        {
                            "type": "table.comparison",
                            "layout": {"mode": "absolute", "x": 0.8, "y": 0.8, "w": 6.0, "h": 2.2},
                            "props": {
                                "headers": ["Metric", "A", "B"],
                                "rows": [["Accuracy", "92%", "89%"], ["AUC", "0.948", "0.931"]],
                                "conclusion": "Recommend A.",
                            },
                        }
                    ],
                }
            ],
        }
    )

    assert deck.render(tmp_path / "table_v2_json.pptx").exists()


def test_table_v2_python_api_render(tmp_path: Path) -> None:
    deck = Deck()
    deck.add_page(
        page.blank(
            blocks=[
                table.comparison(
                    headers=["Plan", "Score"],
                    rows=[["A", "4.8"], ["B", "4.1"]],
                    conclusion="A has the best balance.",
                    layout=layout.box(x=0.8, y=0.8, w=4.8, h=2.0),
                )
            ]
        )
    )

    assert deck.render(tmp_path / "table_v2_api.pptx").exists()
