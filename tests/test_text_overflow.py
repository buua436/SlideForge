from ppt_ui.core.layout import Box
from ppt_ui.core.text_overflow import apply_text_overflow
from ppt_ui.core.theme import get_theme
from ppt_ui.renderer.pptx_renderer import PptxRenderer


def test_apply_text_overflow_truncates() -> None:
    result = apply_text_overflow("abcdefghijklmnopqrstuvwxyz", overflow="truncate", max_chars=8)

    assert result.text == "abcde..."
    assert result.truncated is True


def test_renderer_records_truncation_diagnostic() -> None:
    renderer = PptxRenderer(get_theme("theme.tech_blue"))
    slide = renderer.prs.slides.add_slide(renderer.prs.slide_layouts[6])

    renderer.text(slide, Box(0.5, 0.5, 1.0, 0.3), "abcdefghijklmnopqrstuvwxyz", overflow="truncate", max_chars=8)

    assert renderer.diagnostics
    assert renderer.diagnostics[0].code == "TEXT_TRUNCATED"
