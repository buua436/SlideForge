# SlideForge

SlideForge is a Python PPT UI component library for agent-generated presentation decks. Agents describe pages and reusable blocks with JSON DSL, while SlideForge renders themed, editable `.pptx` files with `python-pptx`.

## Documentation

- 中文文档：[docs/zh.md](docs/zh.md)
- English docs: [docs/en.md](docs/en.md)

## Quick Start

```bash
uv sync --dev
uv run python examples/demo_deck.py
```

This generates:

- `examples/demo.pptx`
- `examples/demo_screenshots/slide_01.png`, `slide_02.png`, ...
- `examples/demo_showcase.png`
- `examples/theme_demos/<theme>/demo.pptx`

Screenshot export uses Microsoft PowerPoint COM automation on Windows.

## What It Includes

- Theme tokens for colors, typography, spacing, radius, shadows, and component styles.
- A registry-based JSON DSL parser for page/block component families and variants.
- Reusable block components for layout, data visualization, narrative analysis, media, and tables.
- A `python-pptx` renderer that keeps generated slides editable.

## Namespace API

```python
from ppt_ui import Deck, chart, data, layout, page

deck = Deck()
deck.add_page(page.standard(
    title="Metrics And Trend",
    blocks=[
        data.metric_cards(
            cards=[data.metric_card(label="AUC", value="0.948", delta="+0.026")],
            layout=layout.grid_item(col=1, span=4, row=1, row_span=2),
        ),
        chart.line(
            categories=["Jan", "Feb"],
            series=[{"name": "A", "values": [10, 20]}],
            layout=layout.grid_item(col=5, span=8, row=1, row_span=2),
        ),
    ],
))
deck.render("examples/api_demo.pptx")
```

JSON DSL uses the same namespace style:

```json
{
  "type": "page.standard",
  "title": "Metrics And Trend",
  "blocks": [
    {"type": "chart.line", "props": {"categories": ["Jan", "Feb"], "series": [{"name": "A", "values": [10, 20]}]}}
  ]
}
```
