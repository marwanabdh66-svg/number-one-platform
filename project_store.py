"""Small, testable SQLite helpers for NUMBER ONE saved projects."""
import json
from datetime import datetime
from urllib.parse import urlparse


_MEDIA_FIELDS = (
    "title",
    "media_type",
    "mime",
    "media_url",
    "preview_url",
    "page_url",
    "license_name",
    "license_url",
    "license_notice",
    "artist",
    "credit",
    "description",
    "attribution_required",
)


def _serialize_media_asset(media):
    """Validate and serialize source/license metadata without downloading media."""
    if media is None:
        return None
    if not isinstance(media, dict):
        raise ValueError("Media metadata must be an object.")

    media_type = str(media.get("media_type") or "").strip().lower()
    if media_type not in {"image", "video"}:
        raise ValueError("Media type must be image or video.")

    clean = {}
    for field in _MEDIA_FIELDS:
        value = media.get(field)
        if field == "attribution_required":
            clean[field] = bool(value)
        elif value is not None:
            clean[field] = str(value).strip()[:2048]

    for required in ("title", "media_url", "page_url", "license_name"):
        if not clean.get(required):
            raise ValueError(f"Media metadata is missing {required}.")

    clean["media_type"] = media_type
    for field in ("media_url", "preview_url", "page_url", "license_url"):
        value = clean.get(field)
        if not value:
            continue
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("Media links must be valid HTTPS URLs.")

    payload = json.dumps(clean, ensure_ascii=False, separators=(",", ":"))
    if len(payload) > 12000:
        raise ValueError("Media metadata is too large to save.")
    return payload


def format_media_attribution(media):
    """Build a reusable attribution block from saved media/license metadata."""
    if not isinstance(media, dict):
        return "بيانات الإسناد غير متاحة."

    author = str(
        media.get("artist") or media.get("credit") or media.get("title") or "غير مذكور"
    ).strip()
    license_name = str(media.get("license_name") or "ترخيص غير محدد").strip()
    source_url = str(media.get("page_url") or "غير متاح").strip()
    lines = [
        f"المؤلف: {author}",
        f"الترخيص: {license_name}",
        f"المصدر: {source_url}",
    ]

    license_url = str(media.get("license_url") or "").strip()
    if license_url:
        lines.append(f"رابط الترخيص: {license_url}")

    license_notice = str(media.get("license_notice") or "").strip()
    if license_notice:
        lines.append(f"ملاحظة الترخيص: {license_notice}")

    return "\n".join(lines)


def initialize_projects_table(connection):
    """Create the saved-projects table and safely migrate older local databases."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            title TEXT NOT NULL,
            template_id TEXT,
            prompt TEXT NOT NULL,
            created TEXT NOT NULL,
            media_json TEXT
        )
        """
    )

    # Existing installations may already have projects without media_json.
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(projects)").fetchall()
    }
    if "media_json" not in columns:
        connection.execute("ALTER TABLE projects ADD COLUMN media_json TEXT")

    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_projects_username_id "
        "ON projects(username, id DESC)"
    )
    connection.commit()


def save_project(
    connection,
    username,
    title,
    prompt,
    template_id=None,
    created=None,
    media=None,
):
    """Save one advertising brief and optional licensed-media attribution metadata."""
    safe_username = str(username or "").strip()
    safe_title = str(title or "").strip()
    safe_prompt = str(prompt or "").strip()

    if not safe_username:
        raise ValueError("A signed-in username is required.")
    if not safe_title or not safe_prompt:
        raise ValueError("Project title and prompt are required.")

    media_json = _serialize_media_asset(media)
    cursor = connection.execute(
        """
        INSERT INTO projects
            (username, title, template_id, prompt, created, media_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            safe_username,
            safe_title,
            str(template_id).strip() if template_id else None,
            safe_prompt,
            created or datetime.now().strftime("%Y-%m-%d %H:%M"),
            media_json,
        ),
    )
    connection.commit()
    return cursor.lastrowid


def list_projects(connection, username):
    """Return only the saved projects owned by the requested username."""
    safe_username = str(username or "").strip()
    if not safe_username:
        return []

    return connection.execute(
        """
        SELECT id, title, template_id, prompt, created, media_json
        FROM projects
        WHERE username = ?
        ORDER BY id DESC
        """,
        (safe_username,),
    ).fetchall()
