import unittest
from unittest.mock import MagicMock, patch


from template_catalog import (
    PHOTO_PREVIEW_ASSETS,
    TEMPLATE_CATALOG,
    get_template_photo_preview,
    fetch_photo_preview_bytes,
    search_templates,
    customize_template,
    render_preview_svg,
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

    def test_curated_photo_sources_have_license_and_attribution_metadata(self):
        self.assertEqual(len(PHOTO_PREVIEW_ASSETS), 8)
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

    def test_eight_topic_families_receive_photographic_previews(self):
        mapped_count = sum(
            get_template_photo_preview(item) is not None
            for item in TEMPLATE_CATALOG
        )
        # Eight selected topics x five format variants each.
        self.assertEqual(mapped_count, 40)

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


if __name__ == "__main__":
    unittest.main()
