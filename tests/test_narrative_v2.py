from pathlib import Path

from ppt_ui import layout, narrative, page
from ppt_ui.api import block
from ppt_ui.core.presentation import Deck
from ppt_ui.schema.parser import deck_from_dict


def test_narrative_v2_json_components_render(tmp_path: Path) -> None:
    deck = deck_from_dict(
        {
            "schema_version": "0.2",
            "pages": [
                {
                    "type": "page.blank",
                    "blocks": [
                        {
                            "type": "narrative.timeline",
                            "layout": {"mode": "absolute", "x": 0.7, "y": 0.7, "w": 7.0, "h": 2.0},
                            "props": {"items": [{"label": "Plan", "date": "May", "description": "Define scope", "status": "done"}, {"label": "Build", "date": "Jun", "description": "Implement", "status": "active"}]},
                        },
                        {
                            "type": "diagram.model",
                            "layout": {"mode": "absolute", "x": 0.7, "y": 3.0, "w": 7.0, "h": 1.6},
                            "props": {"stages": ["Input", "Encoder", "Fusion", "Output"]},
                        },
                    ],
                }
            ],
        }
    )

    assert deck.render(tmp_path / "narrative_v2_json.pptx").exists()


def test_narrative_v2_python_api_render(tmp_path: Path) -> None:
    deck = Deck()
    deck.add_page(
        page.blank(
            blocks=[
                narrative.process_flow(
                    steps=[{"title": "Design", "description": "Schema", "output": "DSL"}, {"title": "Render", "description": "PPTX", "output": "Deck"}],
                    layout=layout.box(x=0.8, y=0.8, w=6.0, h=1.6),
                ),
                narrative.roadmap(
                    items=[{"label": "Core", "start": 0, "end": 0.5, "period": "Q1"}, {"label": "Theme", "start": 0.3, "end": 1.0, "period": "Q2"}],
                    layout=layout.box(x=0.8, y=2.8, w=6.0, h=1.4),
                ),
                block.component("diagram.model", props={"nodes": [{"label": "A"}, {"label": "B"}]}, layout=layout.box(x=0.8, y=4.6, w=4.0, h=1.2)),
            ]
        )
    )

    assert deck.render(tmp_path / "narrative_v2_api.pptx").exists()
