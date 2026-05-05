# SlideForge

SlideForge is a Python PPT UI component library for agent-generated presentation decks. Agents describe slides with JSON DSL, while SlideForge renders reusable, themed, editable `.pptx` files with `python-pptx`.

## Documentation

- 中文文档：[docs/zh/index.md](docs/zh/index.md)
- English docs: [docs/en/index.md](docs/en/index.md)

## Quick Start

```bash
uv sync --dev
uv run python examples/demo_deck.py
```

This generates:

- `examples/demo.pptx`
- `examples/demo_screenshots/slide_01.png`, `slide_02.png`, ...

Screenshot export uses Microsoft PowerPoint COM automation on Windows.

## What It Includes

- Theme tokens for colors, typography, spacing, radius, shadows, and component styles.
- A registry-based JSON DSL parser for component families and variants.
- Reusable slide and block components for layout, data visualization, and narrative analysis.
- A `python-pptx` renderer that keeps generated slides editable.

## Namespace API

```python
from ppt_ui import Deck, chart, data, slide

deck = Deck()
deck.add_slide(slide.title(title="SlideForge"))
deck.add_slide(data.metric_cards(title="Metrics", cards=[
    data.metric_card(label="AUC", value="0.948", delta="+0.026"),
]))
deck.add_slide(chart.line(
    title="Trend",
    categories=["Jan", "Feb"],
    series=[{"name": "A", "values": [10, 20]}],
))
deck.render("examples/api_demo.pptx")
```

JSON DSL uses the same namespace style:

```json
{"type": "chart.line", "title": "Trend"}
```
