import json
import sqlite3
import unittest

from project_store import initialize_projects_table, list_projects, save_project, format_media_attribution


class ProjectStoreMediaTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        initialize_projects_table(self.connection)

    def tearDown(self):
        self.connection.close()

    def sample_media(self):
        return {
            "title": "Sample photo",
            "media_type": "image",
            "mime": "image/jpeg",
            "media_url": "https://upload.wikimedia.org/sample.jpg",
            "preview_url": "https://upload.wikimedia.org/sample-thumb.jpg",
            "page_url": "https://commons.wikimedia.org/wiki/File:Sample.jpg",
            "license_name": "CC BY 4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "license_notice": "Credit the author.",
            "artist": "Sample author",
            "credit": "",
            "description": "A test image",
            "attribution_required": True,
        }

    def test_project_keeps_media_and_attribution_metadata(self):
        project_id = save_project(
            self.connection,
            username="user-a",
            title="Campaign",
            prompt="Ad prompt",
            template_id="NO-0001",
            media=self.sample_media(),
        )

        projects = list_projects(self.connection, "user-a")
        self.assertEqual(project_id, 1)
        self.assertEqual(len(projects), 1)
        saved_media = json.loads(projects[0]["media_json"])
        self.assertEqual(saved_media["title"], "Sample photo")
        self.assertEqual(saved_media["license_name"], "CC BY 4.0")
        self.assertTrue(saved_media["attribution_required"])
        self.assertEqual(saved_media["artist"], "Sample author")
        self.assertEqual(
            saved_media["page_url"],
            "https://commons.wikimedia.org/wiki/File:Sample.jpg",
        )
        attribution_text = format_media_attribution(saved_media)
        self.assertIn("المؤلف: Sample author", attribution_text)
        self.assertIn("الترخيص: CC BY 4.0", attribution_text)
        self.assertIn("المصدر: https://commons.wikimedia.org/wiki/File:Sample.jpg", attribution_text)
        self.assertIn("رابط الترخيص: https://creativecommons.org/licenses/by/4.0/", attribution_text)
        self.assertIn("ملاحظة الترخيص: Credit the author.", attribution_text)
        self.assertEqual(list_projects(self.connection, "user-b"), [])

    def test_cc_by_sa_notice_survives_save_and_attribution_formatting(self):
        media = self.sample_media()
        media["license_name"] = "CC BY-SA 4.0"
        media["license_url"] = "https://creativecommons.org/licenses/by-sa/4.0/"
        media["license_notice"] = (
            "يسمح بالاستخدام التجاري مع نسب المؤلف ومراعاة المشاركة بالمثل."
        )

        save_project(
            self.connection,
            username="user-a",
            title="Share-alike campaign",
            prompt="Ad prompt",
            media=media,
        )
        saved_media = json.loads(list_projects(self.connection, "user-a")[0]["media_json"])
        attribution_text = format_media_attribution(saved_media)

        self.assertIn("CC BY-SA 4.0", attribution_text)
        self.assertIn("المشاركة بالمثل", attribution_text)
        self.assertIn("https://creativecommons.org/licenses/by-sa/4.0/", attribution_text)


    def sample_template(self):
        return {
            "id": "NO-0001",
            "category": "المطاعم والمقاهي",
            "topic": "قهوة مختصة",
            "format": "منشور مربع",
            "style": "فاخر",
            "title": "قهوة مختصة — منشور مربع",
            "description": "تصميم إعلان تجريبي.",
            "headline": "قهوة اليوم",
            "subtitle": "عرض خاص لفترة محدودة",
            "price": "2,500 ريال",
            "call_to_action": "اطلب الآن",
            "accent": "#F2B84B",
            "deep": "#7A3E16",
            "symbol": "☕",
            "layout": 0,
            "source": "NUMBER ONE — SVG أصلي",
            "asset_type": "معاينة متجهية أصلية",
            "photo_preview": {
                "title": "Coffee Cup.jpg",
                "preview_url": "https://upload.wikimedia.org/example/coffee.jpg",
                "page_url": "https://commons.wikimedia.org/wiki/File:Coffee_Cup.jpg",
                "artist": "Sample author",
                "license_name": "CC BY-SA 4.0",
                "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
                "license_notice": "Credit the author and share adaptations alike.",
                "attribution_required": True,
            },
        }

    def test_project_keeps_full_template_and_photo_license_metadata(self):
        template = self.sample_template()
        project_id = save_project(
            self.connection,
            username="user-a",
            title="Coffee campaign",
            prompt="Ad prompt",
            template=template,
        )

        saved = list_projects(self.connection, "user-a")[0]
        saved_template = json.loads(saved["template_json"])
        self.assertEqual(project_id, 1)
        self.assertEqual(saved["template_id"], "NO-0001")
        self.assertEqual(saved_template["id"], "NO-0001")
        self.assertEqual(saved_template["topic"], "قهوة مختصة")
        self.assertEqual(saved_template["format"], "منشور مربع")
        self.assertEqual(saved_template["layout"], 0)
        self.assertEqual(saved_template["headline"], "قهوة اليوم")
        self.assertEqual(saved_template["subtitle"], "عرض خاص لفترة محدودة")
        self.assertEqual(saved_template["price"], "2,500 ريال")
        self.assertEqual(saved_template["call_to_action"], "اطلب الآن")
        self.assertEqual(saved_template["photo_preview"]["artist"], "Sample author")
        self.assertEqual(saved_template["photo_preview"]["license_name"], "CC BY-SA 4.0")
        self.assertEqual(
            saved_template["photo_preview"]["license_url"],
            "https://creativecommons.org/licenses/by-sa/4.0/",
        )
        self.assertNotIn("unlisted_field", saved_template)

    def test_template_id_must_match_saved_template_metadata(self):
        with self.assertRaises(ValueError):
            save_project(
                self.connection,
                username="user-a",
                title="Mismatch",
                prompt="Ad prompt",
                template_id="NO-0002",
                template=self.sample_template(),
            )

    def test_template_photo_rejects_unapproved_preview_hosts(self):
        template = self.sample_template()
        template["photo_preview"]["preview_url"] = "https://example.com/photo.jpg"
        with self.assertRaises(ValueError):
            save_project(
                self.connection,
                username="user-a",
                title="Untrusted preview",
                prompt="Ad prompt",
                template=template,
            )

    def test_old_projects_table_is_migrated_without_losing_rows(self):
        self.connection.execute("DROP TABLE projects")
        self.connection.execute(
            """
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                title TEXT NOT NULL,
                template_id TEXT,
                prompt TEXT NOT NULL,
                created TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            INSERT INTO projects (username, title, prompt, created)
            VALUES ('legacy-user', 'Old project', 'Old prompt', '2026-11-01')
            """
        )
        self.connection.commit()

        initialize_projects_table(self.connection)
        legacy_projects = list_projects(self.connection, "legacy-user")
        self.assertEqual(len(legacy_projects), 1)
        self.assertEqual(legacy_projects[0]["title"], "Old project")
        self.assertIsNone(legacy_projects[0]["media_json"])
        self.assertIsNone(legacy_projects[0]["template_json"])

    def test_non_https_media_links_are_rejected(self):
        media = self.sample_media()
        media["media_url"] = "http://example.com/photo.jpg"
        with self.assertRaises(ValueError):
            save_project(
                self.connection,
                username="user-a",
                title="Campaign",
                prompt="Ad prompt",
                media=media,
            )

    def test_media_type_is_validated(self):
        media = self.sample_media()
        media["media_type"] = "document"
        with self.assertRaises(ValueError):
            save_project(
                self.connection,
                username="user-a",
                title="Campaign",
                prompt="Ad prompt",
                media=media,
            )

    def test_cc0_source_metadata_is_preserved_without_required_attribution(self):
        media = self.sample_media()
        media["license_name"] = "CC0 1.0"
        media["license_url"] = "https://creativecommons.org/publicdomain/zero/1.0/"
        media["license_notice"] = "Public domain dedication."
        media["attribution_required"] = False

        save_project(
            self.connection,
            username="user-a",
            title="CC0 campaign",
            prompt="Ad prompt",
            media=media,
        )
        saved_media = json.loads(list_projects(self.connection, "user-a")[0]["media_json"])
        source_details = format_media_attribution(saved_media)

        self.assertFalse(saved_media["attribution_required"])
        self.assertIn("Sample author", source_details)
        self.assertIn("CC0 1.0", source_details)
        self.assertIn("https://commons.wikimedia.org/wiki/File:Sample.jpg", source_details)
        self.assertIn("https://creativecommons.org/publicdomain/zero/1.0/", source_details)


    def test_template_rejects_invalid_editor_colors(self):
        template = self.sample_template()
        template["accent"] = "#fff;fill:url(javascript:alert(1))"
        with self.assertRaises(ValueError):
            save_project(
                self.connection,
                username="user-a",
                title="Unsafe editor colors",
                prompt="Ad prompt",
                template=template,
            )


if __name__ == "__main__":
    unittest.main()
