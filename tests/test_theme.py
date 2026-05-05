import json
from pathlib import Path

from ppt_ui import theme
from ppt_ui.core.theme import ThemeLoader, builtin_theme_names, default_theme_registry, get_theme
from ppt_ui.schema.parser import deck_from_json


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_builtin_theme_aliases() -> None:
    assert get_theme("default").name == "tech_blue"
    assert get_theme("default_blue").name == "tech_blue"
    assert get_theme("theme.tech_blue").name == "tech_blue"
    assert get_theme("default_blue").colors.primary == "2563EB"


def test_builtin_theme_catalog() -> None:
    expected = {
        "theme.tech_blue",
        "theme.glassmorphism",
        "theme.claude",
        "theme.glitch_art",
        "theme.paper_cut",
        "theme.neon_cyberpunk",
        "theme.apple",
        "theme.google",
    }

    assert expected.issubset(set(builtin_theme_names()))
    assert get_theme("theme.tech_blue").colors.primary == "2563EB"
    assert get_theme("theme.glassmorphism").colors.primary == "6366F1"
    assert get_theme("theme.claude").fonts.family == "Noto Serif SC"
    assert get_theme("theme.glitch_art").background_pattern == "scanlines"
    assert get_theme("theme.paper_cut").shadow.blur_radius == 0.14
    assert get_theme("theme.neon_cyberpunk").decorations.get("card_top_border") == "00FF41"
    assert get_theme("theme.apple").fonts.family == "SF Pro Display"
    assert get_theme("theme.google").fonts.family == "Google Sans"


def test_theme_namespace_api() -> None:
    assert theme.tech_blue().name == "tech_blue"
    assert theme.glassmorphism().colors.primary == "6366F1"
    assert theme.claude().fonts.family == "Noto Serif SC"
    assert theme.glitch_art().background_pattern == "scanlines"
    assert theme.paper_cut().shadow.blur_radius == 0.14
    assert theme.neon_cyberpunk().decorations.get("card_top_border") == "00FF41"
    assert theme.apple().fonts.family == "SF Pro Display"
    assert theme.google().fonts.family == "Google Sans"


def test_loads_external_single_file_theme(tmp_path: Path) -> None:
    theme_path = tmp_path / "company_blue.json"
    write_json(
        theme_path,
        {
            "name": "company_blue",
            "extends": "default_blue",
            "tokens": {
                "colors": {
                    "primary": "#0052CC",
                    "accent": "6554C0",
                    "surface": "F7F9FC",
                },
                "fonts": {
                    "family": "Aptos",
                    "title_size": 34,
                },
            },
            "components": {
                "data.metric_cards": {
                    "default": {
                        "fill": "{colors.surface}",
                        "border": "{colors.border}",
                        "accent": "{colors.primary}",
                    },
                    "hero": {
                        "fill": "{colors.primary_soft}",
                        "accent": "{colors.accent}",
                    },
                }
            },
        },
    )

    theme = ThemeLoader().load(theme_path)

    assert theme.name == "company_blue"
    assert theme.colors.primary == "0052CC"
    assert theme.fonts.family == "Aptos"
    assert theme.component_default_style("data.metric_cards")["fill"] == "F7F9FC"
    assert theme.component_default_style("data.metric_cards", "hero")["accent"] == "6554C0"


def test_loads_flat_external_theme_fields(tmp_path: Path) -> None:
    theme_path = tmp_path / "flat_warm.json"
    write_json(
        theme_path,
        {
            "name": "flat_warm",
            "extends": "theme.tech_blue",
            "background": "#F7F3EA",
            "surface": "#FFFCF5",
            "primary": "#8B5E34",
            "accent": "#D97706",
            "text_primary": "#2B2118",
            "text_muted": "#9A8A78",
            "font_family": "Aptos",
            "title_size": 40,
            "page_margin": 0.6,
            "card_radius": 0.16,
            "chart_palette": ["#8B5E34", "#D97706"],
        },
    )

    theme_obj = ThemeLoader().load(theme_path)

    assert theme_obj.colors.background == "F7F3EA"
    assert theme_obj.colors.text_tertiary == "9A8A78"
    assert theme_obj.fonts.family == "Aptos"
    assert theme_obj.spacing.page_margin == 0.6
    assert theme_obj.radius_tokens.md == 0.16
    assert theme_obj.chart_palette == ["8B5E34", "D97706"]


def test_loads_external_directory_theme(tmp_path: Path) -> None:
    theme_dir = tmp_path / "themes" / "company"
    write_json(
        theme_dir / "theme.json",
        {
            "name": "company",
            "extends": "default_blue",
            "tokens": "./tokens.json",
            "components": ["./components/data.json", "./components/chart.json"],
        },
    )
    write_json(
        theme_dir / "tokens.json",
        {
            "colors": {
                "primary": "0F766E",
                "primary_soft": "ECFDF5",
            },
            "spacing": {
                "gutter": 0.28,
            },
        },
    )
    write_json(
        theme_dir / "components" / "data.json",
        {
            "data.metric_cards": {
                "default": {
                    "fill": "{colors.primary_soft}",
                    "accent": "{colors.primary}",
                }
            }
        },
    )
    write_json(
        theme_dir / "components" / "chart.json",
        {
            "chart.line": {
                "default": {
                    "accent": "{colors.primary}",
                    "line_width": 2.4,
                }
            }
        },
    )

    theme = ThemeLoader().load(theme_dir)

    assert theme.name == "company"
    assert theme.colors.primary == "0F766E"
    assert theme.spacing.gutter == 0.28
    assert theme.component_default_style("data.metric_cards")["fill"] == "ECFDF5"
    assert theme.component_default_style("chart.line")["line_width"] == 2.4


def test_deck_json_resolves_theme_relative_to_deck_file(tmp_path: Path) -> None:
    write_json(
        tmp_path / "themes" / "warm.json",
        {
            "name": "warm",
            "extends": "default_blue",
            "tokens": {
                "colors": {
                    "primary": "EA580C",
                }
            },
        },
    )
    deck_path = tmp_path / "deck.json"
    write_json(
        deck_path,
        {
            "schema_version": "0.2",
            "title": "External Theme Deck",
            "theme": "./themes/warm.json",
            "pages": [{"type": "page.blank", "blocks": []}],
        },
    )

    deck = deck_from_json(deck_path)

    assert deck.theme.name == "warm"
    assert deck.theme.colors.primary == "EA580C"
