from pathlib import Path

from PIL import Image

from ppt_ui.export import ShowcaseItem, build_screenshot_review


def test_build_screenshot_review_from_existing_images(tmp_path: Path) -> None:
    screenshots = []
    for index in range(3):
        path = tmp_path / f"slide_{index + 1:02d}.png"
        Image.new("RGB", (320, 180), "#FFFFFF").save(path)
        screenshots.append(path)

    result = build_screenshot_review(
        screenshots,
        tmp_path / "showcase.png",
        items=[ShowcaseItem("primitive", "rendered component")],
    )

    assert result.showcase.exists()
    assert len(result.screenshots) == 3
