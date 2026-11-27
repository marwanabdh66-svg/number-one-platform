import base64
import unittest
from unittest.mock import MagicMock, patch


from template_catalog import (
    PHOTO_PREVIEW_ASSETS,
    TEMPLATE_CATALOG,
    DEFAULT_SHAPE_LAYERS,
    DEFAULT_LAYER_ORDER,
    normalize_shape_layers,
    normalize_layer_order,
    get_template_photo_preview,
    fetch_photo_preview_bytes,
    search_templates,
    customize_template,
    render_preview_svg,
    render_preview_data_uri,
    template_page_state_key,
)


class TemplateCatalogPhotoPreviewTests(unittest.TestCase):
    def test_catalog_keeps_400_unique_template_variants(self):
        self.assertEqual(len(TEMPLATE_CATALOG), 400)
        self.assertEqual(len({item["id"] for item in TEMPLATE_CATALOG}), 400)

    def test_search_matches_template_id_and_description(self):
        first = TEMPLATE_CATALOG[0]
        self.assertEqual(search_templates(query=first["id"]), [first])

        custom = dict(first)
        custom["id"] = "CUSTOM-SEARCH-01"
        custom["description"] = "عبارة اختبار فريدة للبحث"
        self.assertEqual(
            search_templates([custom], query="اختبار فريدة"),
            [custom],
        )

    def test_search_combines_category_and_format_filters(self):
        chosen = TEMPLATE_CATALOG[0]
        results = search_templates(
            query=chosen["topic"],
            category=chosen["category"],
            format_name=chosen["format"],
        )
        self.assertEqual(results, [chosen])

    def test_template_page_key_is_stable_and_includes_page_size(self):
        results = [{"id": "NO-0001"}, {"id": "NO-0002"}]
        self.assertEqual(
            template_page_state_key(results, 9),
            template_page_state_key(list(results), 9),
        )
        self.assertNotEqual(
            template_page_state_key(results, 9),
            template_page_state_key(results, 6),
        )

    def test_template_page_key_resets_for_same_count_different_results(self):
        first_results = [{"id": "NO-0001"}, {"id": "NO-0002"}]
        second_results = [{"id": "NO-0101"}, {"id": "NO-0102"}]
        self.assertEqual(len(first_results), len(second_results))
        self.assertNotEqual(
            template_page_state_key(first_results, 9),
            template_page_state_key(second_results, 9),
        )

    def test_template_page_key_rejects_invalid_page_size_or_entries(self):
        for invalid_size in (0, -1, True, 1.5):
            with self.subTest(page_size=invalid_size):
                with self.assertRaises(ValueError):
                    template_page_state_key([], invalid_size)
        with self.assertRaises(ValueError):
            template_page_state_key([None], 9)

    def test_curated_photo_sources_have_license_and_attribution_metadata(self):
        self.assertEqual(len(PHOTO_PREVIEW_ASSETS), 9)
        for asset in PHOTO_PREVIEW_ASSETS.values():
            self.assertTrue(asset["preview_url"].startswith("https://"))
            self.assertTrue(asset["page_url"].startswith("https://commons.wikimedia.org/wiki/File:"))
            self.assertTrue(asset["license_url"].startswith("https://creativecommons.org/"))
            self.assertTrue(asset["artist"])
            self.assertTrue(asset["license_name"])
            if asset["license_name"].startswith("CC BY"):
                self.assertTrue(asset["attribution_required"])
            else:
                self.assertFalse(asset["attribution_required"])
                self.assertIn("CC0", asset["license_name"])

    def test_burger_topic_uses_verified_cc0_photo_preview(self):
        asset = PHOTO_PREVIEW_ASSETS[("المطاعم والمقاهي", "برغر فاخر")]
        self.assertEqual(asset["license_name"], "CC0 1.0")
        self.assertFalse(asset["attribution_required"])
        self.assertEqual(
            asset["artist"],
            "Len Rizzi (photographer), reprocessed by Off-shell",
        )
        self.assertIn("Hamburger_%28black_bg%29.jpg", asset["preview_url"])

        variants = [
            item for item in TEMPLATE_CATALOG
            if item["category"] == "المطاعم والمقاهي"
            and item["topic"] == "برغر فاخر"
        ]
        self.assertEqual(len(variants), 5)
        self.assertTrue(
            all(
                get_template_photo_preview(item)["title"] == asset["title"]
                for item in variants
            )
        )

    def test_nine_topic_families_receive_photographic_previews(self):
        mapped_count = sum(
            get_template_photo_preview(item) is not None
            for item in TEMPLATE_CATALOG
        )
        # Nine selected topics x five format variants each.
        self.assertEqual(mapped_count, 45)

    def test_unmapped_template_uses_svg_fallback(self):
        unmapped = next(
            item for item in TEMPLATE_CATALOG
            if get_template_photo_preview(item) is None
        )
        self.assertIsNone(get_template_photo_preview(unmapped))

    def test_photo_fetch_rejects_non_https_and_non_wikimedia_hosts(self):
        with patch("template_catalog.urlopen") as mocked_open:
            self.assertIsNone(
                fetch_photo_preview_bytes("http://upload.wikimedia.org/photo.jpg")
            )
            self.assertIsNone(
                fetch_photo_preview_bytes("https://example.com/photo.jpg")
            )
            mocked_open.assert_not_called()

    def test_photo_fetch_accepts_small_image_response(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.headers.get_content_type.return_value = "image/jpeg"
        response.read.return_value = b"small-image-bytes"

        with patch("template_catalog.urlopen", return_value=response) as mocked_open:
            payload = fetch_photo_preview_bytes(
                "https://upload.wikimedia.org/example/photo.jpg"
            )

        self.assertEqual(payload, b"small-image-bytes")
        mocked_open.assert_called_once()

    def test_photo_fetch_rejects_non_image_and_oversized_responses(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.headers.get_content_type.return_value = "text/html"
        response.read.return_value = b"<html>error</html>"

        with patch("template_catalog.urlopen", return_value=response):
            self.assertIsNone(
                fetch_photo_preview_bytes(
                    "https://upload.wikimedia.org/example/error",
                    max_bytes=1024,
                )
            )

        response.headers.get_content_type.return_value = "image/jpeg"
        response.read.return_value = b"12345"
        with patch("template_catalog.urlopen", return_value=response):
            self.assertIsNone(
                fetch_photo_preview_bytes(
                    "https://upload.wikimedia.org/example/large.jpg",
                    max_bytes=4,
                )
            )


    def test_customized_template_renders_escaped_text_and_user_price(self):
        original = dict(TEMPLATE_CATALOG[0])
        customized = customize_template(
            original,
            headline="<script>alert(1)</script>",
            subtitle="حملة موسمية",
            price="5,000 ريال",
            call_to_action="اطلب الآن",
            accent="#12abef",
            deep="#223344",
            symbol="⭐",
        )

        self.assertNotIn("headline", original)
        self.assertEqual(customized["headline"], "<script>alert(1)</script>")
        self.assertEqual(customized["accent"], "#12ABEF")
        self.assertEqual(customized["deep"], "#223344")

        svg = render_preview_svg(customized)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", svg)
        self.assertNotIn("<script>", svg)
        self.assertIn("حملة موسمية", svg)
        self.assertIn("5,000 ريال", svg)
        self.assertIn("اطلب الآن", svg)

    def test_custom_template_rejects_unsafe_color_values(self):
        original = TEMPLATE_CATALOG[0]
        customized = customize_template(
            original,
            accent='red" onload="alert(1)',
            deep="url(javascript:alert(1))",
        )

        self.assertEqual(customized["accent"], original["accent"].upper())
        self.assertEqual(customized["deep"], original["deep"].upper())
        svg = render_preview_svg(customized)
        self.assertNotIn("javascript:", svg)
        self.assertNotIn("onload=", svg)

    def test_custom_template_text_fields_are_length_limited(self):
        customized = customize_template(
            TEMPLATE_CATALOG[0],
            headline="ع" * 100,
            subtitle="و" * 100,
            price="س" * 100,
            call_to_action="ط" * 100,
            symbol="★" * 20,
        )

        self.assertEqual(len(customized["headline"]), 44)
        self.assertEqual(len(customized["subtitle"]), 70)
        self.assertEqual(len(customized["price"]), 28)
        self.assertEqual(len(customized["call_to_action"]), 28)
        self.assertEqual(len(customized["symbol"]), 8)


    def test_customized_preview_data_uri_contains_exportable_svg(self):
        customized = customize_template(
            TEMPLATE_CATALOG[0],
            headline="عنوان قابل للتصدير",
            price="3,000 ريال",
        )
        data_uri = render_preview_data_uri(customized)
        self.assertTrue(data_uri.startswith("data:image/svg+xml;base64,"))
        encoded = data_uri.split(",", 1)[1]
        svg = base64.b64decode(encoded).decode("utf-8")
        self.assertIn("عنوان قابل للتصدير", svg)
        self.assertIn("3,000 ريال", svg)


    def test_optional_price_can_be_cleared_from_template_preview(self):
        template = dict(TEMPLATE_CATALOG[0])
        template["price"] = "5,000 ريال"
        customized = customize_template(template, price="")
        self.assertEqual(customized["price"], "")
        self.assertNotIn("5,000 ريال", render_preview_svg(customized))

    def test_legacy_template_layers_default_to_visible(self):
        svg = render_preview_svg(TEMPLATE_CATALOG[0])
        self.assertIn("NUMBER ONE", svg)
        self.assertIn(TEMPLATE_CATALOG[0]["topic"], svg)
        self.assertIn("معاينة SVG أصلية قابلة للتطوير", svg)

    def test_visibility_controls_hide_individual_layers_without_erasing_values(self):
        customized = customize_template(
            TEMPLATE_CATALOG[0],
            headline="عنوان طبقة مخفية",
            subtitle="نص طبقة ظاهرة",
            price="سعر محفوظ مخفي",
            call_to_action="زر مخفي",
            symbol="★",
            layer_visibility={
                "headline": False,
                "subtitle": True,
                "price": False,
                "call_to_action": False,
                "symbol": False,
            },
        )
        svg = render_preview_svg(customized)
        self.assertEqual(customized["headline"], "عنوان طبقة مخفية")
        self.assertEqual(customized["price"], "سعر محفوظ مخفي")
        self.assertFalse(customized["layer_visibility"]["headline"])
        self.assertIn('aria-label="المطاعم والمقاهي"', svg)
        self.assertIn("نص طبقة ظاهرة", svg)
        self.assertNotIn("عنوان طبقة مخفية", svg)
        self.assertNotIn("سعر محفوظ مخفي", svg)
        self.assertNotIn("زر مخفي", svg)
        self.assertNotIn(">★</text>", svg)

    def test_visibility_flags_must_be_boolean(self):
        with self.assertRaises(ValueError):
            customize_template(
                TEMPLATE_CATALOG[0],
                layer_visibility={"headline": "false"},
            )


    def test_default_layer_positions_preserve_legacy_svg_layout(self):
        template = dict(TEMPLATE_CATALOG[0])
        template["price"] = "سعر تجريبي"
        svg = render_preview_svg(template)
        self.assertIn('x="835" y="260"', svg)
        self.assertIn('x="835" y="315"', svg)
        self.assertIn('x="835" y="370"', svg)
        self.assertIn('x="730" y="445"', svg)
        self.assertIn('x="230" y="520"', svg)

    def test_custom_layer_positions_move_selected_elements(self):
        customized = customize_template(
            TEMPLATE_CATALOG[0],
            layer_positions={
                "headline": {"x": 50, "y": 50},
                "call_to_action": {"x": 25, "y": 25},
            },
        )
        svg = render_preview_svg(customized)
        self.assertIn('x="668" y="250"', svg)
        self.assertIn('x="610" y="412"', svg)
        self.assertEqual(customized["layer_positions"]["subtitle"], {"x": 100, "y": 50})

    def test_layer_positions_reject_unknown_layers_and_out_of_range_values(self):
        with self.assertRaises(ValueError):
            customize_template(
                TEMPLATE_CATALOG[0],
                layer_positions={"unknown": {"x": 50, "y": 50}},
            )
        with self.assertRaises(ValueError):
            customize_template(
                TEMPLATE_CATALOG[0],
                layer_positions={"headline": {"x": 101, "y": 50}},
            )
        with self.assertRaises(ValueError):
            customize_template(
                TEMPLATE_CATALOG[0],
                layer_positions={"headline": {"x": True, "y": 50}},
            )


    def test_renderer_embeds_supported_jpeg_as_a_separate_image_layer(self):
        photo_bytes = b"\xff\xd8\xff\xe0sample-jpeg-data"
        svg = render_preview_svg(TEMPLATE_CATALOG[0], photo_bytes=photo_bytes)

        self.assertIn('<image href="data:image/jpeg;base64,', svg)
        self.assertIn('clip-path="url(#mediaPhotoClip)"', svg)
        self.assertIn('x="54" y="144" width="360" height="342"', svg)
        self.assertIn('aria-label="صورة مضافة من مكتبة الوسائط"', svg)

    def test_photo_layer_position_and_size_are_editable(self):
        photo_bytes = b"\xff\xd8\xff\xe0sample-jpeg-data"
        customized = customize_template(
            TEMPLATE_CATALOG[0],
            image_layer={
                "visible": True,
                "x": 20,
                "y": 10,
                "width": 50,
                "height": 30,
            },
        )
        svg = render_preview_svg(customized, photo_bytes=photo_bytes)

        self.assertIn('x="180" y="60" width="450" height="180"', svg)
        self.assertEqual(
            customized["image_layer"],
            {"visible": True, "x": 20, "y": 10, "width": 50, "height": 30, "rotation": 0},
        )

    def test_photo_layer_rotation_is_rendered_around_its_center(self):
        photo_bytes = b"\xff\xd8\xff\xe0sample-jpeg-data"
        customized = customize_template(
            TEMPLATE_CATALOG[0],
            image_layer={"rotation": 45},
        )
        svg = render_preview_svg(customized, photo_bytes=photo_bytes)

        self.assertIn('transform="rotate(45 234 315)"', svg)
        self.assertEqual(customized["image_layer"]["rotation"], 45)

    def test_photo_layer_can_be_hidden_without_removing_its_settings(self):
        photo_bytes = b"\xff\xd8\xff\xe0sample-jpeg-data"
        customized = customize_template(
            TEMPLATE_CATALOG[0],
            image_layer={
                "visible": False,
                "x": 12,
                "y": 18,
                "width": 35,
                "height": 42,
            },
        )
        svg = render_preview_svg(customized, photo_bytes=photo_bytes)

        self.assertNotIn("<image href=", svg)
        self.assertFalse(customized["image_layer"]["visible"])
        self.assertEqual(customized["image_layer"]["x"], 12)

    def test_image_layer_rejects_invalid_settings(self):
        invalid_settings = [
            {"unknown": 1},
            {"visible": "false"},
            {"x": True},
            {"width": 9},
            {"height": 81},
            {"rotation": 181},
            {"rotation": -181},
            {"rotation": True},
        ]
        for settings in invalid_settings:
            with self.subTest(settings=settings):
                with self.assertRaises(ValueError):
                    customize_template(TEMPLATE_CATALOG[0], image_layer=settings)


    def test_renderer_ignores_unsupported_or_oversized_photo_payloads(self):
        unsupported_svg = render_preview_svg(
            TEMPLATE_CATALOG[0],
            photo_bytes=b"<svg xmlns='http://www.w3.org/2000/svg'></svg>",
        )
        oversized_png = render_preview_svg(
            TEMPLATE_CATALOG[0],
            photo_bytes=b"\x89PNG\r\n\x1a\n" + (b"x" * 900_001),
        )

        self.assertNotIn("<image href=", unsupported_svg)
        self.assertNotIn("<image href=", oversized_png)
        self.assertNotIn("data:image/svg+xml;base64,", unsupported_svg)

    def test_data_uri_preserves_embedded_image_layer(self):
        photo_bytes = b"\x89PNG\r\n\x1a\nsmall-png-data"
        data_uri = render_preview_data_uri(
            TEMPLATE_CATALOG[0],
            photo_bytes=photo_bytes,
        )
        svg = base64.b64decode(data_uri.split(",", 1)[1]).decode("utf-8")

        self.assertTrue(data_uri.startswith("data:image/svg+xml;base64,"))
        self.assertIn('href="data:image/png;base64,', svg)


    def test_shape_layers_are_hidden_by_default_and_have_three_types(self):
        layers = normalize_shape_layers()
        self.assertEqual(set(layers), {"rectangle", "circle", "line"})
        self.assertTrue(all(not layer["visible"] for layer in layers.values()))
        self.assertTrue(all(layer["opacity"] == 100 for layer in layers.values()))
        self.assertEqual(layers["line"]["height"], 0)

    def test_renderer_draws_independent_rectangle_circle_and_line_layers(self):
        customized = customize_template(
            TEMPLATE_CATALOG[0],
            shape_layers={
                "rectangle": {
                    "visible": True, "x": 10, "y": 10, "width": 20,
                    "height": 15, "color": "#ff0000", "stroke_width": 3,
                    "opacity": 80,
                },
                "circle": {
                    "visible": True, "x": 40, "y": 20, "width": 10,
                    "height": 10, "color": "#00ff00", "stroke_width": 2,
                    "opacity": 55,
                },
                "line": {
                    "visible": True, "x": 10, "y": 70, "width": 20,
                    "height": 0, "color": "#0000ff", "stroke_width": 4,
                    "opacity": 25,
                },
            },
        )
        svg = render_preview_svg(customized)
        self.assertIn('<rect x="90" y="60" width="180" height="90" rx="12" fill="#FF0000"', svg)
        self.assertIn('<ellipse cx="405" cy="150" rx="45" ry="30" fill="#00FF00"', svg)
        self.assertIn('<line x1="90" y1="420" x2="270" y2="420" stroke="#0000FF" stroke-width="4" opacity="0.25"', svg)
        self.assertIn('stroke-width="3" opacity="0.80"', svg)
        self.assertIn('stroke-width="2" opacity="0.55"', svg)

    def test_shape_layer_visibility_can_be_toggled_without_losing_settings(self):
        customized = customize_template(
            TEMPLATE_CATALOG[0],
            shape_layers={
                "rectangle": {
                    "visible": False, "x": 15, "y": 22, "width": 30,
                    "height": 25, "color": "#123456", "stroke_width": 4,
                }
            },
        )
        svg = render_preview_svg(customized)
        self.assertNotIn('aria-label="طبقة المستطيل"', svg)
        self.assertFalse(customized["shape_layers"]["rectangle"]["visible"])
        self.assertEqual(customized["shape_layers"]["rectangle"]["x"], 15)
        self.assertEqual(customized["shape_layers"]["rectangle"]["color"], "#123456")

    def test_shape_layers_reject_unknown_names_fields_and_unsafe_values(self):
        invalid_values = [
            {"unknown": {"visible": True}},
            {"rectangle": {"visible": "yes"}},
            {"rectangle": {"x": True}},
            {"rectangle": {"width": 81}},
            {"rectangle": {"height": 1}},
            {"circle": {"color": "red"}},
            {"line": {"height": -1}},
            {"line": {"stroke_width": 13}},
            {"rectangle": {"rotation": 181}},
            {"circle": {"rotation": -181}},
            {"line": {"rotation": True}},
            {"rectangle": {"opacity": -1}},
            {"circle": {"opacity": 101}},
            {"line": {"opacity": True}},
            {"circle": {"opacity": 50.5}},
            {"circle": {"onclick": "alert(1)"}},
        ]
        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_shape_layers(value)

    def test_shape_layers_default_rotation_is_zero_and_valid_rotation_is_normalized(self):
        defaults = normalize_shape_layers()
        self.assertTrue(all(layer["rotation"] == 0 for layer in defaults.values()))

        rotated = normalize_shape_layers({
            "rectangle": {"rotation": 45},
            "circle": {"rotation": -90},
            "line": {"rotation": 180},
        })
        self.assertEqual(rotated["rectangle"]["rotation"], 45)
        self.assertEqual(rotated["circle"]["rotation"], -90)
        self.assertEqual(rotated["line"]["rotation"], 180)

    def test_renderer_rotates_each_geometric_layer_around_its_center(self):
        customized = customize_template(
            TEMPLATE_CATALOG[0],
            shape_layers={
                "rectangle": {
                    "visible": True, "x": 10, "y": 20, "width": 20,
                    "height": 10, "color": "#FF0000", "stroke_width": 3,
                    "rotation": 45,
                },
                "circle": {
                    "visible": True, "x": 40, "y": 30, "width": 20,
                    "height": 20, "color": "#00FF00", "stroke_width": 2,
                    "rotation": -30,
                },
                "line": {
                    "visible": True, "x": 5, "y": 70, "width": 40,
                    "height": 0, "color": "#0000FF", "stroke_width": 4,
                    "rotation": 90,
                },
            },
        )
        svg = render_preview_svg(customized)
        self.assertIn('transform="rotate(45 180 150)"', svg)
        self.assertIn('transform="rotate(-30 450 240)"', svg)
        self.assertIn('transform="rotate(90 225 420)"', svg)

    def test_shape_layer_opacity_defaults_and_partial_updates(self):
        defaults = normalize_shape_layers()
        self.assertTrue(all(layer["opacity"] == 100 for layer in defaults.values()))
        customized = normalize_shape_layers({"circle": {"opacity": 35}})
        self.assertEqual(customized["circle"]["opacity"], 35)
        self.assertEqual(customized["rectangle"]["opacity"], 100)
        self.assertEqual(customized["line"]["opacity"], 100)

    def test_shape_layer_partial_updates_keep_other_default_layers(self):
        layers = normalize_shape_layers({
            "circle": {"visible": True, "color": "#ABCDEF"}
        })
        self.assertTrue(layers["circle"]["visible"])
        self.assertEqual(layers["circle"]["color"], "#ABCDEF")
        self.assertFalse(layers["rectangle"]["visible"])
        self.assertFalse(layers["line"]["visible"])


    def test_layer_order_defaults_and_completes_partial_orders(self):
        self.assertEqual(normalize_layer_order(), list(DEFAULT_LAYER_ORDER))
        partial = normalize_layer_order(["headline", "image", "rectangle"])
        self.assertEqual(
            partial,
            ["headline", "image", "rectangle", "circle", "line",
             "subtitle", "price", "call_to_action", "symbol"],
        )

    def test_layer_order_rejects_unknown_duplicate_and_non_list_values(self):
        for invalid in ("headline", {"headline": 1}, ["headline", "headline"], ["unknown"]):
            with self.subTest(order=invalid):
                with self.assertRaises(ValueError):
                    normalize_layer_order(invalid)

    def test_custom_template_preserves_requested_layer_order(self):
        order = ["symbol", "headline", "image"]
        customized = customize_template(TEMPLATE_CATALOG[0], layer_order=order)
        self.assertEqual(
            customized["layer_order"],
            order + [name for name in DEFAULT_LAYER_ORDER if name not in order],
        )

    def test_renderer_respects_layer_order_across_image_shapes_and_text(self):
        order = [
            "symbol", "call_to_action", "price", "subtitle", "headline",
            "line", "circle", "rectangle", "image",
        ]
        customized = customize_template(
            TEMPLATE_CATALOG[0],
            headline="HEADLINE_ORDER_MARK",
            subtitle="SUBTITLE_ORDER_MARK",
            price="PRICE_ORDER_MARK",
            call_to_action="CTA_ORDER_MARK",
            symbol="SYMORDER",
            image_layer={
                "visible": True, "x": 5, "y": 5, "width": 20,
                "height": 20, "rotation": 0,
            },
            shape_layers={
                "rectangle": {"visible": True},
                "circle": {"visible": True},
                "line": {"visible": True},
            },
            layer_order=order,
        )
        svg = render_preview_svg(customized, photo_bytes=bytes((255, 216, 255)) + b"sample-jpeg")
        markers = [
            ">SYMORDER</text>",
            ">CTA_ORDER_MARK</text>",
            ">PRICE_ORDER_MARK</text>",
            ">SUBTITLE_ORDER_MARK</text>",
            ">HEADLINE_ORDER_MARK</text>",
            'aria-label="طبقة الخط"',
            'aria-label="طبقة الدائرة"',
            'aria-label="طبقة المستطيل"',
            'aria-label="صورة مضافة من مكتبة الوسائط"',
        ]
        positions = [svg.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))

    def test_renderer_uses_legacy_layer_order_when_metadata_is_missing(self):
        customized = customize_template(
            TEMPLATE_CATALOG[0],
            headline="DEFAULT_HEAD_MARK",
            subtitle="DEFAULT_SUBTITLE_MARK",
            price="DEFAULT_PRICE_MARK",
            call_to_action="DEFAULT_CTA_MARK",
            symbol="SYMBOL8",
            image_layer={"visible": True},
            shape_layers={
                "rectangle": {"visible": True},
                "circle": {"visible": True},
                "line": {"visible": True},
            },
        )
        self.assertEqual(customized["layer_order"], list(DEFAULT_LAYER_ORDER))
        svg = render_preview_svg(
            customized,
            photo_bytes=bytes((255, 216, 255)) + b"sample-jpeg",
        )
        markers = [
            'aria-label="صورة مضافة من مكتبة الوسائط"',
            'aria-label="طبقة المستطيل"',
            'aria-label="طبقة الدائرة"',
            'aria-label="طبقة الخط"',
            ">DEFAULT_HEAD_MARK</text>",
            ">DEFAULT_SUBTITLE_MARK</text>",
            ">DEFAULT_PRICE_MARK</text>",
            ">DEFAULT_CTA_MARK</text>",
            ">SYMBOL8</text>",
        ]
        positions = [svg.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))

    def test_renderer_wraps_editable_layers_with_pointer_drag_targets(self):
        template = customize_template(
            TEMPLATE_CATALOG[0],
            price="100 ريال",
            layer_visibility={
                "headline": True,
                "subtitle": True,
                "price": True,
                "call_to_action": True,
                "symbol": True,
            },
            shape_layers={
                "rectangle": {"visible": True},
                "circle": {"visible": True},
                "line": {"visible": True},
            },
        )
        svg = render_preview_svg(template, photo_bytes=b"\\xff\\xd8\\xffphoto")
        for layer_name in (
            "image", "rectangle", "circle", "line",
            "headline", "subtitle", "price", "call_to_action", "symbol",
        ):
            with self.subTest(layer=layer_name):
                self.assertIn(f'<g data-layer="{layer_name}">', svg)


if __name__ == "__main__":
    unittest.main()
