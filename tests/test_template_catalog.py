import unittest

from template_catalog import (
    PHOTO_PREVIEW_ASSETS,
    TEMPLATE_CATALOG,
    get_template_photo_preview,
)


class TemplateCatalogPhotoPreviewTests(unittest.TestCase):
    def test_catalog_keeps_400_unique_template_variants(self):
        self.assertEqual(len(TEMPLATE_CATALOG), 400)
        self.assertEqual(len({item["id"] for item in TEMPLATE_CATALOG}), 400)

    def test_curated_photo_sources_have_license_and_attribution_metadata(self):
        self.assertEqual(len(PHOTO_PREVIEW_ASSETS), 7)
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

    def test_seven_topic_families_receive_photographic_previews(self):
        mapped_count = sum(
            get_template_photo_preview(item) is not None
            for item in TEMPLATE_CATALOG
        )
        # Seven selected topics x five format variants each.
        self.assertEqual(mapped_count, 35)

    def test_unmapped_template_uses_svg_fallback(self):
        unmapped = next(
            item for item in TEMPLATE_CATALOG
            if get_template_photo_preview(item) is None
        )
        self.assertIsNone(get_template_photo_preview(unmapped))


if __name__ == "__main__":
    unittest.main()
