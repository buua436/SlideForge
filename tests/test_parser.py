from pathlib import Path

from ppt_ui import Deck, block, chart, data, layout, page
from ppt_ui.core.diagnostics import DiagnosticError
from ppt_ui.core.page import Block, Page
from ppt_ui.schema.parser import block_from_dict, deck_from_dict, deck_from_json
from ppt_ui.styles import StyleTarget


def test_deck_from_dict_builds_pages_and_blocks() -> None:
    deck = deck_from_dict(
        {
            "schema_version": "0.2",
            "theme": "default_blue",
            "pages": [
                {
                    "type": "page.standard",
                    "title": "Metrics",
                    "blocks": [
                        {
                            "type": "data.metric_cards",
                            "props": {"cards": [{"label": "AUC", "value": "0.948"}]},
                            "layout": {"mode": "grid", "col": 1, "span": 4, "row": 1},
                        }
                    ],
                }
            ],
        }
    )

    assert len(deck.pages) == 1
    assert deck.pages[0].title == "Metrics"
    assert deck.pages[0].blocks[0].type == "data.metric_cards"


def test_block_from_dict_keeps_props_layout_and_id() -> None:
    item = block_from_dict(
        {
            "id": "trend",
            "type": "chart.line",
            "props": {"categories": ["A"], "series": []},
            "layout": {"mode": "grid", "col": 2, "span": 6},
        }
    )

    assert item.id == "trend"
    assert item.props["categories"] == ["A"]
    assert item.layout["span"] == 6


def test_sample_deck_uses_page_block_dsl() -> None:
    sample = Path(__file__).resolve().parents[1] / "examples" / "sample_deck.json"
    deck = deck_from_json(sample)

    assert len(deck.pages) >= 8
    assert any(len(page.blocks) > 1 for page in deck.pages)
    assert not [item for item in deck.diagnostics if item.level == "error"]


def test_namespace_api_factories_create_pages_and_blocks() -> None:
    metric_block = data.metric_cards(
        cards=[data.metric_card(label="Accuracy", value="92.3%")],
        layout=layout.grid_item(col=1, span=4, row=1),
    )
    trend_block = chart.line(
        categories=["A", "B"],
        series=[{"name": "S", "values": [1, 2]}],
        layout=layout.grid_item(col=5, span=8, row=1),
    )
    bar_block = chart.bar(
        categories=["A", "B"],
        series=[{"name": "S", "values": [1, 2]}],
        layout=layout.grid_item(col=1, span=4, row=2),
    )
    donut_block = chart.donut(labels=["A", "B"], values=[3, 2], layout=layout.grid_item(col=5, span=4, row=2))
    progress_block = data.progress(items=[{"label": "Done", "value": 80}], layout=layout.grid_item(col=9, span=4, row=2))
    custom_block = block.component("basic.text", props={"text": "Hello"})
    report_page = page.standard(title="Report", blocks=[metric_block, trend_block, bar_block, donut_block, progress_block, custom_block])

    assert isinstance(metric_block, Block)
    assert isinstance(report_page, Page)
    assert report_page.blocks[1].type == "chart.line"
    assert report_page.blocks[2].type == "chart.bar"
    assert report_page.blocks[3].type == "chart.donut"
    assert report_page.blocks[4].type == "data.progress"


def test_deck_python_api_add_page_and_render(tmp_path: Path) -> None:
    deck = Deck()
    deck.add_page(page.blank(blocks=[block.component("basic.text", props={"text": "Blank"}, layout=layout.box(x=1, y=1, w=4, h=1))]))
    output = tmp_path / "api_deck.pptx"
    deck.render(output)

    assert len(deck.pages) == 1
    assert deck.pages[0].use_master is False
    assert output.exists()


def test_unknown_component_type_raises_diagnostic_error() -> None:
    try:
        deck_from_dict(
            {
                "schema_version": "0.2",
                "pages": [
                    {
                        "type": "page.standard",
                        "blocks": [{"type": "chart.scatter", "props": {}}],
                    }
                ],
            }
        )
    except DiagnosticError as exc:
        assert exc.diagnostics[0].code == "UNKNOWN_COMPONENT_TYPE"
    else:
        raise AssertionError("Expected DiagnosticError")


def test_validation_warnings_are_kept_on_deck() -> None:
    deck = deck_from_dict(
        {
            "schema_version": "0.2",
            "pages": [
                {
                    "type": "page.standard",
                    "blocks": [
                        {
                            "type": "chart.line",
                            "props": {
                                "categories": ["A", "B"],
                                "series": [{"name": "S", "values": [1]}],
                            },
                        }
                    ],
                }
            ],
        }
    )

    assert any(item.code == "CHART_SERIES_LENGTH_MISMATCH" for item in deck.diagnostics)


def test_deck_parser_keeps_styles_and_block_classes() -> None:
    deck = deck_from_dict(
        {
            "schema_version": "0.2",
            "styles": {
                ".hero": {"fill": "{colors.primary}"},
                "#trend": {"stroke_width": 3},
            },
            "pages": [
                {
                    "type": "page.standard",
                    "blocks": [
                        {
                            "id": "trend",
                            "class": "hero chart-card",
                            "type": "chart.line",
                            "props": {"categories": ["A"], "series": [{"name": "S", "values": [1]}]},
                        }
                    ],
                }
            ],
        }
    )

    block_item = deck.pages[0].blocks[0]
    style = deck.styles.resolve(StyleTarget(type_name=block_item.type, id=block_item.id, class_names=block_item.class_names))

    assert block_item.class_names == ("hero", "chart-card")
    assert style.fill == "{colors.primary}"
    assert style.stroke_width == 3
