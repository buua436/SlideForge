from pathlib import Path

from ppt_ui import basic, layout, page
from ppt_ui.core.presentation import Deck
from ppt_ui.schema.parser import deck_from_dict


def test_basic_v2_json_components_render(tmp_path: Path) -> None:
    deck = deck_from_dict(
        {
            "schema_version": "0.2",
            "styles": {
                ".panel": {"fill": "{colors.surface_white}", "stroke": "{colors.border}", "radius": 0.05, "shadow": True},
                ".headline": {"color": "{colors.primary}", "font_size": 20, "font_weight": "bold"},
            },
            "pages": [
                {
                    "type": "page.blank",
                    "blocks": [
                        {"type": "basic.card", "class": "panel", "layout": {"mode": "absolute", "x": 0.8, "y": 0.8, "w": 4.0, "h": 1.2}},
                        {
                            "type": "basic.text",
                            "class": "headline",
                            "layout": {"mode": "absolute", "x": 1.0, "y": 1.1, "w": 3.6, "h": 0.4},
                            "props": {"text": "Basic V2"},
                        },
                        {"type": "basic.divider", "layout": {"mode": "absolute", "x": 1.0, "y": 1.7, "w": 3.6, "h": 0.1}},
                    ],
                }
            ],
        }
    )

    assert deck.render(tmp_path / "basic_v2_json.pptx").exists()


def test_basic_v2_python_api_components_render(tmp_path: Path) -> None:
    deck = Deck()
    deck.add_page(
        page.blank(
            blocks=[
                basic.card(layout=layout.box(x=0.8, y=0.8, w=3.4, h=1.0), style={"fill": "{colors.primary_soft}", "stroke": "{colors.border}", "radius": 0.05}),
                basic.text(text="Python API", layout=layout.box(x=1.0, y=1.1, w=3.0, h=0.3), color="{colors.primary}", size=18, bold=True),
                basic.divider(layout=layout.box(x=1.0, y=1.62, w=3.0, h=0.1), color="{colors.accent}", width=1.4),
            ]
        )
    )

    assert deck.render(tmp_path / "basic_v2_api.pptx").exists()
