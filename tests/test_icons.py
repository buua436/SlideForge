from ppt_ui.icons.provider import IconRegistry, IconRequest, IconifyJsonProvider, icon_request_from_props, normalize_icon_name


def test_normalize_icon_name_accepts_frontend_dot_style() -> None:
    assert normalize_icon_name("lucide.sparkles") == ("lucide", "sparkles")
    assert normalize_icon_name("lucide:sparkles") == ("lucide", "sparkles")
    assert normalize_icon_name("remix.rocket-line") == ("ri", "rocket-line")
    assert normalize_icon_name("bootstrap.alarm") == ("bi", "alarm")
    assert normalize_icon_name("fa.user") == ("fa6-solid", "user")
    assert normalize_icon_name("material.auto-awesome") == ("material-symbols", "auto-awesome")


def test_icon_request_keeps_rendering_options() -> None:
    request = icon_request_from_props(
        "heroicons.bolt",
        color="#7C3AED",
        size=128,
        rotate=1,
        flip="horizontal",
        stroke_width=1.5,
    )

    assert request is not None
    assert request.icon_id == "heroicons:bolt"
    assert request.width == 128
    assert request.height == 128
    assert request.rotate == "1"
    assert request.flip == "horizontal"
    assert request.stroke_width == 1.5


def test_iconify_json_provider_resolves_normalized_request() -> None:
    provider = IconifyJsonProvider(
        prefix="lucide",
        icon_set={
            "width": 24,
            "height": 24,
            "icons": {
                "sparkles": {
                    "body": '<path d="M12 3v18"/>',
                }
            },
        },
    )
    registry = IconRegistry([provider])
    svg = registry.resolve_svg(IconRequest(prefix="lucide", name="sparkles", color="#2563EB", stroke_width=1.8))

    assert svg is not None
    assert 'stroke="#2563EB"' in svg
    assert 'stroke-width="1.8"' in svg


def test_icon_registry_supports_custom_alias_and_provider() -> None:
    class BrandProvider:
        def resolve_svg(self, request: IconRequest) -> str | None:
            if request.prefix != "brand":
                return None
            return f'<svg xmlns="http://www.w3.org/2000/svg"><text fill="{request.color}">{request.name}</text></svg>'

    registry = IconRegistry()
    registry.register_alias("company", "brand")
    registry.register(BrandProvider())
    request = registry.create_request("company.logo", color="#08112F")

    assert request is not None
    assert request.icon_id == "brand:logo"
    assert registry.resolve_svg(request) == '<svg xmlns="http://www.w3.org/2000/svg"><text fill="#08112F">logo</text></svg>'
