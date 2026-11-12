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


_TEMPLATE_STRING_FIELDS = (
    "id", "category", "topic", "format", "style", "title",
    "description", "accent", "deep", "symbol", "source", "asset_type",
)
_TEMPLATE_PHOTO_FIELDS = (
    "title", "preview_url", "page_url", "artist",
    "license_name", "license_url", "license_notice", "attribution_required",
)


def _serialize_template_photo(photo):
    """Keep only curated preview and license fields from a selected template."""
    if photo is None:
        return None
    if not isinstance(photo, dict):
        raise ValueError("Template photo metadata must be an object.")

    clean = {}
    for field in _TEMPLATE_PHOTO_FIELDS:
        value = photo.get(field)
        if field == "attribution_required":
            clean[field] = bool(value)
        elif value is not None:
            clean[field] = str(value).strip()[:2048]

    for required in ("title", "preview_url", "page_url", "artist", "license_name", "license_url"):
        if not clean.get(required):
            raise ValueError(f"Template photo metadata is missing {required}.")

    allowed_hosts = {
        "preview_url": {"upload.wikimedia.org", "thumb.wikimedia.org"},
        "page_url": {"commons.wikimedia.org"},
        "license_url": {"creativecommons.org"},
    }
    for field, hosts in allowed_hosts.items():
        parsed = urlparse(clean[field])
        if (
            parsed.scheme != "https"
            or parsed.hostname not in hosts
            or parsed.port not in (None, 443)
            or parsed.username
            or parsed.password
        ):
            raise ValueError("Template photo links must use approved HTTPS hosts.")

    return clean


def _serialize_template_metadata(template):
    """Validate and serialize the selected catalog entry and its photo license."""
    if template is None:
        return None
    if not isinstance(template, dict):
        raise ValueError("Template metadata must be an object.")

    clean = {}
    for field in _TEMPLATE_STRING_FIELDS:
        value = template.get(field)
        if value is not None:
            clean[field] = str(value).strip()[:2048]

    for required in ("id", "category", "topic", "format", "style", "title", "description"):
        if not clean.get(required):
            raise ValueError(f"Template metadata is missing {required}.")

    if template.get("layout") is not None:
        try:
            layout = int(template["layout"])
        except (TypeError, ValueError):
            raise ValueError("Template layout must be an integer.") from None
        if layout < 0 or layout > 4:
            raise ValueError("Template layout is outside the supported range.")
        clean["layout"] = layout

    photo = _serialize_template_photo(template.get("photo_preview"))
    if photo is not None:
        clean["photo_preview"] = photo

    payload = json.dumps(clean, ensure_ascii=False, separators=(",", ":"))
    if len(payload) > 12000:
        raise ValueError("Template metadata is too large to save.")
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
            media_json TEXT,
            template_json TEXT
        )
        """
    )

    # Existing installations may already have projects without media_json.
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(projects)").fetchall()
    }
    if "media_json" not in columns:
        connection.execute("ALTER TABLE projects ADD COLUMN media_json TEXT")
    if "template_json" not in columns:
        connection.execute("ALTER TABLE projects ADD COLUMN template_json TEXT")

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
    template=None,
):
    """Save an advertising brief, selected catalog metadata, and optional media attribution."""
    safe_username = str(username or "").strip()
    safe_title = str(title or "").strip()
    safe_prompt = str(prompt or "").strip()

    if not safe_username:
        raise ValueError("A signed-in username is required.")
    if not safe_title or not safe_prompt:
        raise ValueError("Project title and prompt are required.")

    media_json = _serialize_media_asset(media)
    template_json = _serialize_template_metadata(template)
    metadata_template_id = str(template.get("id") or "").strip() if template else ""
    safe_template_id = str(template_id or metadata_template_id or "").strip() or None
    if metadata_template_id and safe_template_id != metadata_template_id:
        raise ValueError("Template ID does not match the saved template metadata.")

    cursor = connection.execute(
        """
        INSERT INTO projects
            (username, title, template_id, prompt, created, media_json, template_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            safe_username,
            safe_title,
            safe_template_id,
            safe_prompt,
            created or datetime.now().strftime("%Y-%m-%d %H:%M"),
            media_json,
            template_json,
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
        SELECT id, title, template_id, prompt, created, media_json, template_json
        FROM projects
        WHERE username = ?
        ORDER BY id DESC
        """,
        (safe_username,),
    ).fetchall()
