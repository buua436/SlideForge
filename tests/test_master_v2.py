from pathlib import Path

from ppt_ui.schema.parser import deck_from_dict


def test_master_can_render_primitive_chrome(tmp_path: Path) -> None:
    deck = deck_from_dict(
        {
            "schema_version": "0.2",
            "default_master": "custom",
            "masters": {
                "custom": {
                    "type": "master.tech_blue",
                    "chrome": {"accent_bar": {"visible": False}, "footer": {"visible": False}, "page_number": {"visible": False}},
                    "back_primitives": [
                        {
                            "type": "primitive.rect",
                            "layout": {"mode": "absolute", "x": 0.5, "y": 0.4, "w": 0.08, "h": 0.7},
                            "style": {"fill": "{colors.primary}", "radius": 0.04},
                        }
                    ],
                    "fore_primitives": [
                        {
                            "type": "primitive.text",
                            "layout": {"mode": "absolute", "x": 10.5, "y": 7.05, "w": 1.8, "h": 0.18},
                            "props": {"text": "{current} / {total}", "color": "{colors.text_tertiary}", "font_size": 8, "align": "right"},
                        }
                    ],
                }
            },
            "pages": [{"type": "page.standard", "title": "Primitive Master", "blocks": []}],
        }
    )

    assert deck.masters.get("custom").back_primitives
    assert deck.render(tmp_path / "primitive_master.pptx").exists()
