from ppt_ui.core.diagnostics import DiagnosticError
from ppt_ui.schema.parser import deck_from_dict


def test_parser_reports_invalid_styles_path() -> None:
    try:
        deck_from_dict({"schema_version": "0.2", "styles": "bad", "pages": []})
    except DiagnosticError as exc:
        assert exc.diagnostics[0].code == "INVALID_STYLES"
        assert exc.diagnostics[0].path == "$.styles"
    else:
        raise AssertionError("Expected DiagnosticError")


def test_parser_reports_invalid_block_style_path() -> None:
    try:
        deck_from_dict(
            {
                "schema_version": "0.2",
                "pages": [
                    {
                        "type": "page.blank",
                        "blocks": [{"type": "basic.text", "props": {"text": "x"}, "style": "bad"}],
                    }
                ],
            }
        )
    except DiagnosticError as exc:
        assert any(item.code == "INVALID_STYLE" and item.path == "$.pages[0].blocks[0].style" for item in exc.diagnostics)
    else:
        raise AssertionError("Expected DiagnosticError")


def test_parser_keeps_invalid_class_warning_in_non_strict_mode() -> None:
    deck = deck_from_dict(
        {
            "schema_version": "0.2",
            "pages": [{"type": "page.blank", "blocks": [{"type": "basic.text", "props": {"text": "x"}, "class": {"bad": True}}]}],
        },
        strict=False,
    )

    assert any(item.code == "INVALID_CLASS_NAMES" for item in deck.diagnostics)
