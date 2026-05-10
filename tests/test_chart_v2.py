from pathlib import Path

from ppt_ui import chart, layout, page
from ppt_ui.core.presentation import Deck
from ppt_ui.schema.parser import deck_from_dict


def test_chart_v2_json_components_render(tmp_path: Path) -> None:
    deck = deck_from_dict(
        {
            "schema_version": "0.2",
            "pages": [
                {
                    "type": "page.blank",
                    "blocks": [
                        {
                            "type": "chart.line",
                            "layout": {"mode": "absolute", "x": 0.7, "y": 0.7, "w": 5.0, "h": 2.4},
                            "props": {"title": "Trend", "categories": ["A", "B", "C"], "series": [{"name": "S1", "values": [1, 2, 3]}]},
                        },
                        {
                            "type": "chart.donut",
                            "layout": {"mode": "absolute", "x": 6.0, "y": 0.7, "w": 3.0, "h": 2.4},
                            "props": {"labels": ["A", "B"], "values": [3, 2]},
                        },
                    ],
                }
            ],
        }
    )

    assert deck.render(tmp_path / "chart_v2_json.pptx").exists()


def test_chart_v2_python_api_render(tmp_path: Path) -> None:
    deck = Deck()
    deck.add_page(
        page.blank(
            blocks=[
                chart.bar(categories=["A", "B"], series=[{"name": "S", "values": [1, 2]}], layout=layout.box(x=0.8, y=0.8, w=4.0, h=2.2)),
                chart.pie(labels=["X", "Y"], values=[4, 6], layout=layout.box(x=5.2, y=0.8, w=3.0, h=2.2)),
            ]
        )
    )

    assert deck.render(tmp_path / "chart_v2_api.pptx").exists()
