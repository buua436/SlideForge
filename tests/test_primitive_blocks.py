from pathlib import Path

from ppt_ui.schema.parser import deck_from_dict


def test_primitive_json_blocks_render(tmp_path: Path) -> None:
    deck = deck_from_dict(
        {
            "schema_version": "0.2",
            "theme": "theme.tech_blue",
            "styles": {
                ".hero-text": {"color": "{colors.primary}", "font_size": 22},
                ".panel": {"fill": "{colors.surface_white}", "stroke": "{colors.border}", "radius": 0.05},
            },
            "pages": [
                {
                    "type": "page.blank",
                    "blocks": [
                        {
                            "type": "primitive.rect",
                            "class": "panel",
                            "layout": {"mode": "absolute", "x": 0.8, "y": 0.8, "w": 4.0, "h": 1.2},
                            "props": {},
                        },
                        {
                            "type": "primitive.text",
                            "class": "hero-text",
                            "layout": {"mode": "absolute", "x": 1.0, "y": 1.1, "w": 3.6, "h": 0.4},
                            "props": {"text": "Primitive JSON Block"},
                        },
                        {
                            "type": "primitive.line",
                            "layout": {"mode": "absolute", "x": 1.0, "y": 1.75, "w": 3.6, "h": 0.1},
                            "props": {"stroke": "{colors.accent}", "stroke_width": 1.5},
                        },
                    ],
                }
            ],
        }
    )

    output = deck.render(tmp_path / "primitive_blocks.pptx")

    assert output.exists()
