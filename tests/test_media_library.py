import unittest

from media_library import normalize_media_pages


class MediaLibraryNormalizationTests(unittest.TestCase):
    def make_page(
        self,
        mime="image/jpeg",
        license_name="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        artist="<a>Creator</a>",
    ):
        return {
            "title": "File:Sample media.jpg",
            "imageinfo": [{
                "url": "https://upload.wikimedia.org/sample-media",
                "thumburl": "https://upload.wikimedia.org/sample-thumb",
                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Sample_media.jpg",
                "mime": mime,
                "extmetadata": {
                    "LicenseShortName": {"value": license_name},
                    "LicenseUrl": {"value": license_url},
                    "Artist": {"value": artist},
                    "Credit": {"value": "Test credit"},
                },
            }],
        }

    def test_cc_by_image_is_returned_with_attribution(self):
        results = normalize_media_pages([self.make_page()], "image")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Sample media.jpg")
        self.assertEqual(results[0]["artist"], "Creator")
        self.assertTrue(results[0]["attribution_required"])
        self.assertEqual(
            results[0]["page_url"],
            "https://commons.wikimedia.org/wiki/File:Sample_media.jpg",
        )

    def test_noncommercial_and_no_derivatives_are_excluded(self):
        noncommercial = self.make_page(
            license_name="CC BY-NC 4.0",
            license_url="https://creativecommons.org/licenses/by-nc/4.0/",
        )
        no_derivatives = self.make_page(
            license_name="CC BY-ND 4.0",
            license_url="https://creativecommons.org/licenses/by-nd/4.0/",
        )
        self.assertEqual(
            normalize_media_pages([noncommercial, no_derivatives], "image"),
            [],
        )

    def test_restrictions_override_an_otherwise_allowed_license(self):
        restricted = self.make_page()
        restricted["imageinfo"][0]["extmetadata"]["Restrictions"] = {
            "value": "Non-commercial use only"
        }
        self.assertEqual(normalize_media_pages([restricted], "image"), [])

    def test_unknown_license_is_excluded(self):
        page = self.make_page(license_name="Unknown", license_url="")
        self.assertEqual(normalize_media_pages([page], "image"), [])

    def test_video_results_keep_direct_video_and_preview_urls(self):
        page = self.make_page(
            mime="video/webm",
            license_name="CC0",
            license_url="https://creativecommons.org/publicdomain/zero/1.0/",
        )
        results = normalize_media_pages([page], "video")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["mime"], "video/webm")
        self.assertEqual(
            results[0]["media_url"],
            "https://upload.wikimedia.org/sample-media",
        )
        self.assertEqual(
            results[0]["preview_url"],
            "https://upload.wikimedia.org/sample-thumb",
        )

    def test_wrong_media_type_is_excluded(self):
        self.assertEqual(
            normalize_media_pages([self.make_page()], "video"),
            [],
        )


if __name__ == "__main__":
    unittest.main()
