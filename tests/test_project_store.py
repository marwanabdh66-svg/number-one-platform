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


if __name__ == "__main__":
    unittest.main()
