from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class ShowcaseItem:
    label: str
    caption: str


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], *, fill: str, outline: str = "#E4ECF7", radius: int = 14) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=1)


def build_demo_showcase(
    screenshots: Sequence[str | Path],
    output: str | Path,
    *,
    title: str = "SlideForge Component Gallery",
    subtitle: str = "Agent-driven PPT UI framework demo deck",
    items: Sequence[ShowcaseItem] | None = None,
) -> Path:
    """Compose slide screenshots into one gallery image for quick visual review."""

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", (1920, 1080), "#FFFFFF")
    draw = ImageDraw.Draw(canvas)

    title_font = _font(52, bold=True)
    subtitle_font = _font(27)
    h2_font = _font(25, bold=True)
    body_font = _font(18)
    small_font = _font(15)

    draw.rounded_rectangle((38, 58, 52, 154), radius=7, fill="#2563EB")
    draw.rounded_rectangle((38, 106, 52, 154), radius=7, fill="#7C3AED")
    draw.text((78, 58), title, fill="#08112F", font=title_font)
    draw.text((80, 126), subtitle, fill="#5B6B86", font=subtitle_font)

    sidebar = (1540, 28, 1888, 1038)
    _rounded_rect(draw, sidebar, fill="#FBFDFF", outline="#DDE7F5", radius=18)
    draw.rounded_rectangle((1572, 60, 1582, 90), radius=5, fill="#2563EB")
    draw.rounded_rectangle((1572, 76, 1582, 90), radius=5, fill="#7C3AED")
    draw.text((1600, 55), "Completed Components", fill="#08112F", font=h2_font)

    component_items = list(items or [])
    y = 112
    for index, item in enumerate(component_items, start=1):
        card = (1570, y, 1856, y + 52)
        fill = "#F8FAFF" if index % 2 else "#FFFFFF"
        _rounded_rect(draw, card, fill=fill, outline="#E7EEF9", radius=12)
        draw.rounded_rectangle((1586, y + 11, 1618, y + 43), radius=8, fill="#EEF5FF", outline="#DBEAFE")
        draw.text((1594, y + 18), f"{index:02d}", fill="#2563EB", font=small_font)
        draw.text((1636, y + 8), item.label, fill="#08112F", font=small_font)
        draw.text((1636, y + 29), item.caption, fill="#5B6B86", font=small_font)
        y += 61

    note_y = min(888, y + 10)
    draw.line((1570, note_y, 1856, note_y), fill="#E4ECF7", width=1)
    draw.text((1570, note_y + 22), "Review Focus", fill="#08112F", font=h2_font)
    for offset, text in enumerate(["page/block composition", "master chrome", "theme tokens", "editable PPTX output"]):
        yy = note_y + 70 + offset * 28
        draw.ellipse((1572, yy + 7, 1580, yy + 15), fill="#2563EB")
        draw.text((1592, yy), text, fill="#5B6B86", font=small_font)

    paths = [Path(item) for item in screenshots]
    grid_x, grid_y = 80, 214
    if len(paths) <= 6:
        columns = 3
        thumb_w, thumb_h = 445, 250
        gap_x, gap_y = 36, 68
    elif len(paths) <= 9:
        columns = 3
        thumb_w, thumb_h = 360, 203
        gap_x, gap_y = 44, 48
    else:
        columns = 4
        thumb_w, thumb_h = 330, 186
        gap_x, gap_y = 26, 62
    for index, path in enumerate(paths[:12]):
        row, col = divmod(index, columns)
        x = grid_x + col * (thumb_w + gap_x)
        y = grid_y + row * (thumb_h + gap_y)
        _rounded_rect(draw, (x - 1, y - 1, x + thumb_w + 1, y + thumb_h + 1), fill="#FFFFFF", outline="#DCE7F5", radius=13)
        with Image.open(path) as slide_image:
            slide_image = slide_image.convert("RGB")
            slide_image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            paste_x = x + (thumb_w - slide_image.width) // 2
            paste_y = y + (thumb_h - slide_image.height) // 2
            canvas.paste(slide_image, (paste_x, paste_y))
        badge_x = x + thumb_w // 2 - 22
        badge_y = y + thumb_h + 13
        draw.rounded_rectangle((badge_x, badge_y, badge_x + 44, badge_y + 28), radius=7, fill="#2563EB")
        draw.rounded_rectangle((badge_x + 26, badge_y, badge_x + 44, badge_y + 28), radius=7, fill="#7C3AED")
        draw.text((badge_x + 11, badge_y + 5), f"{index + 1:02d}", fill="#FFFFFF", font=small_font)
        draw.text((badge_x + 58, badge_y + 4), path.stem.replace("slide_", "Slide "), fill="#08112F", font=body_font)

    draw.rounded_rectangle((80, 1000, 420, 1005), radius=3, fill="#2563EB")
    draw.rounded_rectangle((260, 1000, 420, 1005), radius=3, fill="#7C3AED")
    draw.text((80, 1018), "Generated from examples/demo.pptx screenshots", fill="#8A97AD", font=small_font)
    canvas.save(output_path)
    return output_path
