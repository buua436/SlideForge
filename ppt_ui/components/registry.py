from __future__ import annotations

from ppt_ui.components.basic_v2 import BasicCardComponent, BasicDividerComponent, BasicTextComponent
from ppt_ui.components.blocks import (
    ComparisonTableComponent,
    IconComponent,
    ImageComponent,
)
from ppt_ui.components.chart_v2 import ChartComponent
from ppt_ui.components.data_v2 import DataMetricCardComponent, DataMetricCardsComponent, DataProgressComponent
from ppt_ui.components.layout_v2 import LayoutContainerComponent
from ppt_ui.components.narrative_v2 import (
    ModelDiagramComponentV2,
    ProcessFlowComponentV2,
    RoadmapComponentV2,
    TimelineComponentV2,
)
from ppt_ui.components.primitives import (
    PrimitiveChartComponent,
    PrimitiveIconComponent,
    PrimitiveImageComponent,
    PrimitiveLineComponent,
    PrimitiveRectComponent,
    PrimitiveTableComponent,
    PrimitiveTextComponent,
)
from ppt_ui.components.table_v2 import TableComponent
from ppt_ui.core.registry import ComponentRegistry


def build_default_component_registry() -> ComponentRegistry:
    registry = ComponentRegistry()
    registry.register("basic.text", BasicTextComponent.from_props)
    registry.register("basic.card", BasicCardComponent.from_props)
    registry.register("basic.divider", BasicDividerComponent.from_props)
    registry.register("data.metric_card", DataMetricCardComponent.from_props)
    registry.register("data.metric_cards", DataMetricCardsComponent.from_props)
    registry.register("data.progress", DataProgressComponent.from_props)
    registry.register("layout.container", lambda props: LayoutContainerComponent.from_props(props, kind="container"))
    registry.register("layout.card", lambda props: LayoutContainerComponent.from_props(props, kind="card"))
    registry.register("layout.stack", lambda props: LayoutContainerComponent.from_props(props, kind="stack"))
    registry.register("layout.grid", lambda props: LayoutContainerComponent.from_props(props, kind="grid"))
    registry.register("chart.line", lambda props: ChartComponent.from_props(props, chart_type="line"))
    registry.register("chart.bar", lambda props: ChartComponent.from_props(props, chart_type="bar"))
    registry.register("chart.pie", lambda props: ChartComponent.from_props(props, chart_type="pie"))
    registry.register("chart.donut", lambda props: ChartComponent.from_props(props, chart_type="donut"))
    registry.register("diagram.model", ModelDiagramComponentV2.from_props)
    registry.register("table.comparison", lambda props: TableComponent.from_props(props, variant="comparison"))
    registry.register("table.basic", lambda props: TableComponent.from_props(props, variant="basic"))
    registry.register("narrative.timeline", TimelineComponentV2.from_props)
    registry.register("narrative.process_flow", ProcessFlowComponentV2.from_props)
    registry.register("narrative.roadmap", RoadmapComponentV2.from_props)
    registry.register("media.icon", IconComponent.from_props)
    registry.register("media.image", ImageComponent.from_props)
    registry.register("primitive.text", PrimitiveTextComponent.from_props)
    registry.register("primitive.rect", PrimitiveRectComponent.from_props)
    registry.register("primitive.line", PrimitiveLineComponent.from_props)
    registry.register("primitive.image", PrimitiveImageComponent.from_props)
    registry.register("primitive.icon", PrimitiveIconComponent.from_props)
    registry.register("primitive.table", PrimitiveTableComponent.from_props)
    registry.register("primitive.chart", PrimitiveChartComponent.from_props)
    return registry
