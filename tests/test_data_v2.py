from pathlib import Path

from ppt_ui import data, layout, page
from ppt_ui.components.data_v2 import DataMetricCardComponent, DataMetricCardsComponent
from ppt_ui.core.component import RenderContext
from ppt_ui.core.layout import Box
from ppt_ui.core.presentation import Deck
from ppt_ui.core.theme import get_theme
from ppt_ui.schema.parser import deck_from_dict


def test_data_v2_json_components_render(tmp_path: Path) -> None:
    deck = deck_from_dict(
        {
            "schema_version": "0.2",
            "styles": {
                ".kpi": {"fill": "{colors.surface_white}", "stroke": "{colors.border}", "radius": 0.05},
            },
            "pages": [
                {
                    "type": "page.blank",
                    "blocks": [
                        {
                            "type": "data.metric_cards",
                            "class": "kpi",
                            "layout": {"mode": "absolute", "x": 0.8, "y": 0.8, "w": 5.8, "h": 1.4},
                            "props": {
                                "cards": [
                                    {"label": "Accuracy", "value": "92.3%", "delta": "+3.1%", "compare": "vs previous", "icon": "target"},
                                    {"label": "AUC", "value": "0.948", "delta": "+0.026", "compare": "validation set", "icon": "chart"},
                                ]
                            },
                        },
                        {
                            "type": "data.progress",
                            "layout": {"mode": "absolute", "x": 0.8, "y": 2.5, "w": 5.8, "h": 1.4},
                            "props": {"items": [{"label": "Parser", "value": 80}, {"label": "Renderer", "value": 60}]},
                        },
                    ],
                }
            ],
        }
    )

    assert deck.render(tmp_path / "data_v2_json.pptx").exists()


def test_data_v2_python_api_single_metric_card_block(tmp_path: Path) -> None:
    deck = Deck()
    deck.add_page(
        page.blank(
            blocks=[
                data.metric_card(label="Pages", value="12", delta="+2", compare="demo pages", layout=layout.box(x=0.8, y=0.8, w=2.4, h=1.4)),
                data.progress(items=[{"label": "Done", "value": 75}], layout=layout.box(x=0.8, y=2.5, w=4.2, h=0.8)),
            ]
        )
    )

    assert deck.render(tmp_path / "data_v2_api.pptx").exists()


def test_metric_card_bare_mode_removes_card_surface() -> None:
    ctx = RenderContext(slide=None, theme=get_theme("theme.tech_blue"), renderer=object())
    tree = DataMetricCardComponent.from_props({"label": "Accuracy", "value": "92.3%", "bare": True}).render_to_primitives(ctx, Box(0, 0, 2, 1))

    class_names = [item.class_names for item in tree.children]
    assert ("metric-card-surface",) not in class_names
    assert "metric-card-bare" in tree.class_names


def test_metric_cards_propagates_bare_mode_to_items() -> None:
    ctx = RenderContext(slide=None, theme=get_theme("theme.tech_blue"), renderer=object())
    tree = DataMetricCardsComponent.from_props({"bare": True, "cards": [{"label": "A", "value": "1"}, {"label": "B", "value": "2"}]}).render_to_primitives(ctx, Box(0, 0, 4, 1))

    assert all("metric-card-bare" in child.class_names for child in tree.children)
