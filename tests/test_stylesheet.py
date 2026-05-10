from ppt_ui.styles import Style, StyleSheet, StyleTarget


def test_stylesheet_matches_type_id_and_class() -> None:
    sheet = StyleSheet.from_value(
        {
            "*": {"font_size": 10},
            "chart.line": {"color": "64748B"},
            ".hero": {"color": "7C3AED"},
            "#trend": {"color": "2563EB"},
        }
    )

    target = StyleTarget(type_name="chart.line", id="trend", class_names=("hero",))
    style = sheet.resolve(target)

    assert style.font_size == 10
    assert style.color == "2563EB"


def test_stylesheet_later_rule_wins_at_same_specificity() -> None:
    sheet = StyleSheet.from_value(
        [
            {"selector": ".card", "style": {"fill": "FFFFFF"}},
            {"selector": ".card", "style": {"fill": "F8FAFC"}},
        ]
    )

    style = sheet.resolve(StyleTarget(type_name="rect", class_names=("card",)))

    assert style.fill == "F8FAFC"


def test_stylesheet_supports_compound_type_id_selector() -> None:
    sheet = StyleSheet.from_value(
        [
            {"selector": "chart.line#trend", "style": {"stroke_width": 3}},
            {"selector": "chart.line#other", "style": {"stroke_width": 1}},
        ]
    )

    style = sheet.resolve(StyleTarget(type_name="chart.line", id="trend"), base=Style(stroke_width=2))

    assert style.stroke_width == 3


def test_stylesheet_keeps_namespaced_type_selector_unambiguous() -> None:
    sheet = StyleSheet.from_value({"data.metric_cards": {"fill": "FFFFFF"}})

    assert sheet.resolve(StyleTarget(type_name="data.metric_cards")).fill == "FFFFFF"
    assert sheet.resolve(StyleTarget(type_name="data", class_names=("metric_cards",))).fill is None


def test_stylesheet_supports_component_slot_selector() -> None:
    sheet = StyleSheet.from_value(
        {
            "data.metric_card": {"color": "111111"},
            "data.metric_card::value": {"color": "7C3AED", "font_size": 28},
            "data.metric_card::label": {"color": "64748B"},
        }
    )

    value_style = sheet.resolve(StyleTarget(type_name="data.metric_card", slot_name="value"))
    label_style = sheet.resolve(StyleTarget(type_name="data.metric_card", slot_name="label"))

    assert value_style.color == "7C3AED"
    assert value_style.font_size == 28
    assert label_style.color == "64748B"
