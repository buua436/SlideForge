from __future__ import annotations

from ppt_ui.components.blocks import (
    BarChartComponent,
    ComparisonTableComponent,
    IconComponent,
    ImageComponent,
    LineChartComponent,
    MetricCardsComponent,
    PieChartComponent,
    ProcessFlowComponent,
    ProgressBarsComponent,
    RoadmapComponent,
    TextComponent,
    TimelineComponent,
)
from ppt_ui.core.registry import ComponentRegistry


def build_default_component_registry() -> ComponentRegistry:
    registry = ComponentRegistry()
    registry.register("basic.text", TextComponent.from_props)
    registry.register("data.metric_cards", MetricCardsComponent.from_props)
    registry.register("data.progress", ProgressBarsComponent.from_props)
    registry.register("chart.line", LineChartComponent.from_props)
    registry.register("chart.bar", BarChartComponent.from_props)
    registry.register("chart.pie", PieChartComponent.from_props)
    registry.register("chart.donut", lambda props: PieChartComponent.from_props({**props, "donut": True}))
    registry.register("table.comparison", ComparisonTableComponent.from_props)
    registry.register("table.basic", ComparisonTableComponent.from_props)
    registry.register("narrative.timeline", TimelineComponent.from_props)
    registry.register("narrative.process_flow", ProcessFlowComponent.from_props)
    registry.register("narrative.roadmap", RoadmapComponent.from_props)
    registry.register("media.icon", IconComponent.from_props)
    registry.register("media.image", ImageComponent.from_props)
    return registry
