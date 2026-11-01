"""Search and normalize openly licensed media from Wikimedia Commons.

Only files with an explicit license that permits commercial reuse are returned.
The source file page and license details are kept with every result so the UI
can show attribution requirements beside each preview.
"""
from __future__ import annotations

import html
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = (
    "NUMBER ONE Platform media-library/1.0 "
    "(https://github.com/marwanabdh66-svg/number-one-platform)"
)


class MediaLibraryError(RuntimeError):
    """Raised when Wikimedia Commons cannot be queried safely."""


def _clean_text(value: object) -> str:
    """Remove HTML from Commons metadata and decode entities."""
    if isinstance(value, dict):
        value = value.get("value", "")
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]*>", " ", text)
    return re.sub(r"\\s+", " ", text).strip()


def _metadata_value(metadata: dict, key: str) -> str:
    return _clean_text(metadata.get(key, ""))


def _license_details(metadata: dict) -> tuple[str, str, str] | None:
    """Return (label, license URL, notice), or None for unsafe/unknown terms."""
    license_name = _metadata_value(metadata, "LicenseShortName")
    license_url = _metadata_value(metadata, "LicenseUrl")
    usage_terms = _metadata_value(metadata, "UsageTerms")
    restrictions = _metadata_value(metadata, "Restrictions")
    combined = " ".join((license_name, usage_terms, restrictions, license_url)).casefold()

    # Exclude licenses that prohibit commercial use or derivative adaptations.
    restricted = re.search(
        r"\\bNC\\b|\\bND\\b|non[ -]?commercial|no[ -]?derivatives?|fair use|all rights reserved",
        combined,
        flags=re.IGNORECASE,
    )
    if restricted:
        return None

    if "cc0" in combined or "public domain" in combined or "/publicdomain/" in license_url.casefold():
        return (
            license_name or "CC0 / الملكية العامة",
            license_url,
            "مسموح بالاستخدام التجاري مبدئيًا؛ يُستحسن إبقاء بيانات المصدر.",
        )

    if "by-sa" in combined or "by_sa" in combined:
        if "creativecommons.org/licenses/by-sa/" not in license_url.casefold() and "cc by-sa" not in license_name.casefold():
            return None
        return (
            license_name or "CC BY-SA",
            license_url,
            "يسمح بالاستخدام التجاري مع نسب المؤلف ومراعاة شرط المشاركة بالمثل عند إنشاء عمل مشتق.",
        )

    if (
        "creativecommons.org/licenses/by/" in license_url.casefold()
        or re.search(r"\\bcc[ -]?by(?:\\s|$)", license_name.casefold())
    ):
        return (
            license_name or "CC BY",
            license_url,
            "يسمح بالاستخدام التجاري مع نسب العمل إلى صاحبه ورابط الترخيص.",
        )

    # Unknown, custom, or incomplete licenses are not presented as reusable.
    return None


def normalize_media_pages(pages: list[dict], media_type: str) -> list[dict]:
    """Normalize Commons API pages and keep only explicitly reusable media."""
    if media_type not in {"image", "video"}:
        raise ValueError("media_type must be 'image' or 'video'")

    expected_prefix = "image/" if media_type == "image" else "video/"
    results = []
    for page in pages or []:
        imageinfo = page.get("imageinfo") or []
        if not imageinfo:
            continue
        info = imageinfo[0]
        mime = str(info.get("mime", "")).casefold()
        if not mime.startswith(expected_prefix):
            continue

        metadata = info.get("extmetadata") or {}
        license_data = _license_details(metadata)
        if not license_data:
            continue

        license_name, license_url, license_notice = license_data
        title = str(page.get("title", "")).removeprefix("File:").strip()
        media_url = str(info.get("url", "")).strip()
        preview_url = str(info.get("thumburl") or media_url).strip()
        page_url = str(info.get("descriptionurl", "")).strip()
        if not media_url or not page_url:
            continue

        artist = _metadata_value(metadata, "Artist")
        credit = _metadata_value(metadata, "Credit")
        description = _metadata_value(metadata, "ImageDescription")
        attribution_required = license_name.casefold().startswith("cc by")
        results.append(
            {
                "title": title or "ملف وسائط من ويكيميديا",
                "media_type": media_type,
                "mime": mime,
                "media_url": media_url,
                "preview_url": preview_url,
                "page_url": page_url,
                "license_name": license_name,
                "license_url": license_url,
                "license_notice": license_notice,
                "artist": artist,
                "credit": credit,
                "description": description,
                "attribution_required": attribution_required,
            }
        )
    return results


def search_commons_media(query: str, media_type: str = "image", limit: int = 9) -> list[dict]:
    """Search Commons for images or videos with commercial-friendly licenses.

    Results are external previews/links; files are not downloaded or re-hosted.
    """
    clean_query = str(query or "").strip()
    if len(clean_query) < 2:
        raise ValueError("أدخل حرفين على الأقل للبحث.")
    if len(clean_query) > 100:
        raise ValueError("اجعل عبارة البحث أقصر من 100 حرف.")
    if media_type not in {"image", "video"}:
        raise ValueError("media_type must be 'image' or 'video'")

    safe_limit = max(1, min(int(limit), 12))
    file_type = "bitmap" if media_type == "image" else "video"
    params = {
        "action": "query",
        "generator": "search",
        "gsrnamespace": 6,
        "gsrsearch": f"{clean_query} filetype:{file_type}",
        "gsrlimit": safe_limit,
        "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata",
        "iiurlwidth": 720,
        "iiextmetadatafilter": (
            "LicenseShortName|LicenseUrl|UsageTerms|Artist|Credit|"
            "AttributionRequired|ImageDescription|Restrictions"
        ),
        "format": "json",
        "formatversion": 2,
    }
    request = Request(
        f"{API_URL}?{urlencode(params)}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )

    try:
        with urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MediaLibraryError("تعذر الاتصال بمكتبة ويكيميديا الآن. حاول مرة أخرى لاحقًا.") from exc

    pages = (payload.get("query") or {}).get("pages") or []
    if isinstance(pages, dict):
        pages = list(pages.values())
    return normalize_media_pages(pages, media_type)[:safe_limit]
