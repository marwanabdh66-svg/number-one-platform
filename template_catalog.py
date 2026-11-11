"""Original SVG starter templates for NUMBER ONE.

The catalog contains 400 structured starter variants (10 categories x 8 topics x 5 formats).
Previews are generated locally as SVG; no third-party stock image is redistributed.
These are starter concepts, not layered PSD/Canva source files.
"""
from __future__ import annotations

import base64
from html import escape
from itertools import product
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen



_PREVIEW_ALLOWED_HOSTS = frozenset({"upload.wikimedia.org", "thumb.wikimedia.org"})


def fetch_photo_preview_bytes(
    url: str,
    timeout: int = 8,
    max_bytes: int = 2_500_000,
) -> bytes | None:
    """Fetch a small Wikimedia photo preview safely; return None on failure.

    Only HTTPS URLs from Wikimedia's upload hosts are accepted. The response
    must have an image MIME type and stay below the byte limit so a broken or
    oversized remote asset never blocks the template catalog.
    """
    try:
        parsed = urlsplit(str(url or "").strip())
        if (
            parsed.scheme != "https"
            or parsed.hostname not in _PREVIEW_ALLOWED_HOSTS
            or parsed.port not in (None, 443)
        ):
            return None
        safe_timeout = max(1, min(int(timeout), 20))
        safe_limit = max(1, min(int(max_bytes), 5_000_000))
        request = Request(
            str(url).strip(),
            headers={
                "User-Agent": "NUMBER ONE template-preview/1.0",
                "Accept": "image/avif,image/webp,image/jpeg,image/png,image/*",
            },
        )
        with urlopen(request, timeout=safe_timeout) as response:
            content_type = response.headers.get_content_type().casefold()
            if not content_type.startswith("image/"):
                return None
            payload = response.read(safe_limit + 1)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError):
        return None

    if not payload or len(payload) > safe_limit:
        return None
    return payload


_CATEGORIES = [
    {
        "name": "المطاعم والمقاهي",
        "topics": ["برغر فاخر", "قهوة مختصة", "وجبة عائلية", "افتتاح مطعم", "حلويات شرقية", "بيتزا طازجة", "مخبوزات يومية", "عرض غداء"],
        "accent": "#F2B84B",
        "deep": "#7A3E16",
        "symbol": "☕",
    },
    {
        "name": "المتاجر والمنتجات",
        "topics": ["إطلاق منتج", "عرض متجر", "منتج إلكتروني", "عناية منزلية", "إكسسوارات", "منتجات طبيعية", "عرض نهاية الأسبوع", "تخفيض موسمي"],
        "accent": "#38BDF8",
        "deep": "#164E8A",
        "symbol": "✦",
    },
    {
        "name": "الأزياء والملابس",
        "topics": ["تشكيلة صيفية", "ملابس رجالية", "أزياء نسائية", "أحذية رياضية", "حقائب فاخرة", "أزياء أطفال", "مجموعة شتوية", "إطلالة يومية"],
        "accent": "#F472B6",
        "deep": "#831843",
        "symbol": "✧",
    },
    {
        "name": "العطور والتجميل",
        "topics": ["عطر جديد", "مجموعة عناية", "مستحضرات تجميل", "عناية بالبشرة", "صالون تجميل", "عرض عطور", "روتين يومي", "مجموعة فاخرة"],
        "accent": "#C4A7FF",
        "deep": "#542B83",
        "symbol": "❀",
    },
    {
        "name": "العقارات والإنشاءات",
        "topics": ["شقة للبيع", "فيلا فاخرة", "أرض استثمارية", "مشروع سكني", "مكتب تجاري", "وحدة للإيجار", "تصميم داخلي", "افتتاح مشروع"],
        "accent": "#34D399",
        "deep": "#065F46",
        "symbol": "⌂",
    },
    {
        "name": "التقنية والإلكترونيات",
        "topics": ["هاتف ذكي", "حاسوب محمول", "سماعات لاسلكية", "تطبيق جديد", "خدمة رقمية", "ملحقات تقنية", "عرض إلكترونيات", "حل تقني"],
        "accent": "#60A5FA",
        "deep": "#1E40AF",
        "symbol": "⌘",
    },
    {
        "name": "التعليم والدورات",
        "topics": ["دورة تدريبية", "تعلم الإنجليزية", "برنامج مهني", "منحة تعليمية", "ورشة عمل", "دروس خصوصية", "تعليم عن بعد", "تسجيل جديد"],
        "accent": "#FBBF24",
        "deep": "#92400E",
        "symbol": "✎",
    },
    {
        "name": "السفر والسياحة",
        "topics": ["رحلة سياحية", "عرض فندقي", "رحلة بحرية", "مغامرة جبلية", "عطلة عائلية", "زيارة مدينة", "باقة سفر", "تجربة استثنائية"],
        "accent": "#22D3EE",
        "deep": "#155E75",
        "symbol": "✈",
    },
    {
        "name": "الخدمات المهنية",
        "topics": ["استشارات أعمال", "خدمات محاسبة", "خدمات قانونية", "تسويق رقمي", "تصميم هوية", "خدمات صيانة", "خدمات تقنية", "حلول للشركات"],
        "accent": "#FB923C",
        "deep": "#9A3412",
        "symbol": "◇",
    },
    {
        "name": "العروض والخصومات",
        "topics": ["خصم لفترة محدودة", "عرض نهاية الأسبوع", "اشترِ واحدًا واحصل على آخر", "تخفيضات موسمية", "عرض حصري", "تصفية مخزون", "هدية مع الشراء", "سعر خاص"],
        "accent": "#FB7185",
        "deep": "#9F1239",
        "symbol": "٪",
    },
]

_FORMATS = [
    "منشور مربع",
    "قصة عمودية",
    "غلاف أفقي",
    "إعلان عرض",
    "بطاقة منتج",
]

_STYLES = [
    "فاخر",
    "عصري",
    "هادئ",
    "جريء",
    "بسيط",
]


def _build_catalog() -> list[dict]:
    catalog = []
    number = 1
    for category_index, category in enumerate(_CATEGORIES):
        for topic_index, (topic, format_name) in enumerate(
            product(category["topics"], _FORMATS)
        ):
            style_index = (category_index + topic_index) % len(_STYLES)
            catalog.append(
                {
                    "id": f"NO-{number:04d}",
                    "category": category["name"],
                    "topic": topic,
                    "format": format_name,
                    "style": _STYLES[style_index],
                    "title": f"{topic} — {format_name}",
                    "description": (
                        f"تصميم {format_name} بأسلوب {_STYLES[style_index]} "
                        f"لمجال {category['name']}. عدّل النص والتفاصيل "
                        "لتناسب نشاطك قبل نشر الإعلان."
                    ),
                    "accent": category["accent"],
                    "deep": category["deep"],
                    "symbol": category["symbol"],
                    "layout": (number - 1) % 5,
                    "source": "NUMBER ONE — SVG أصلي",
                    "asset_type": "معاينة متجهية أصلية",
                }
            )
            number += 1
    return catalog


TEMPLATE_CATALOG = _build_catalog()

def search_templates(
    templates: list[dict] | None = None,
    query: str = "",
    category: str | None = None,
    format_name: str | None = None,
) -> list[dict]:
    """Search template metadata and apply optional category/format filters.

    The search includes the template ID and description as well as the visible
    title, topic, category, format, style, and source fields.
    """
    source = TEMPLATE_CATALOG if templates is None else templates
    normalized_query = str(query or "").strip().casefold()
    selected_category = str(category or "").strip()
    selected_format = str(format_name or "").strip()
    searchable_fields = (
        "id", "title", "category", "topic", "format",
        "style", "description", "source", "asset_type",
    )

    results = []
    for item in source:
        if selected_category and item.get("category") != selected_category:
            continue
        if selected_format and item.get("format") != selected_format:
            continue
        if normalized_query:
            searchable_text = " ".join(
                str(item.get(field, "")) for field in searchable_fields
            ).casefold()
            if normalized_query not in searchable_text:
                continue
        results.append(item)
    return results



# Small curated set of real, externally hosted Wikimedia Commons photographs.
# Eight topic families use these photos (5 format variants each); other
# templates continue to use locally generated SVG previews.
# The file page is the authoritative source for attribution/license details.
PHOTO_PREVIEW_ASSETS = {
    ("المطاعم والمقاهي", "قهوة مختصة"): {
        "title": "Coffee Cup.jpg — صورة فنجان قهوة",
        "preview_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Coffee_Cup.jpg/500px-Coffee_Cup.jpg",
        "page_url": "https://commons.wikimedia.org/wiki/File:Coffee_Cup.jpg",
        "artist": "Mickey Đại Phát",
        "license_name": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "license_notice": "نسب المؤلف ورابط الترخيص؛ وأي تعديل للصورة يخضع لشرط المشاركة بالمثل.",
        "attribution_required": True,
    },
    ("العطور والتجميل", "عطر جديد"): {
        "title": "Perfume glass bottle.jpg — صورة زجاجة عطر",
        "preview_url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/7/79/Perfume_glass_bottle.jpg/960px-Perfume_glass_bottle.jpg",
        "page_url": "https://commons.wikimedia.org/wiki/File:Perfume_glass_bottle.jpg",
        "artist": "Santeri Viinamäki",
        "license_name": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "license_notice": "نسب المؤلف ورابط الترخيص؛ وأي تعديل للصورة يخضع لشرط المشاركة بالمثل.",
        "attribution_required": True,
    },
    ("العقارات والإنشاءات", "فيلا فاخرة"): {
        "title": "Yemeni House (10053201645).jpg — صورة بيت يمني",
        "preview_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Yemeni_House_%2810053201645%29.jpg/960px-Yemeni_House_%2810053201645%29.jpg",
        "page_url": "https://commons.wikimedia.org/wiki/File:Yemeni_House_(10053201645).jpg",
        "artist": "Rod Waddington",
        "license_name": "CC BY-SA 2.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/2.0/",
        "license_notice": "نسب المؤلف ورابط الترخيص؛ وأي تعديل للصورة يخضع لشرط المشاركة بالمثل.",
        "attribution_required": True,
    },
    ("التقنية والإلكترونيات", "هاتف ذكي"): {
        "title": "Galaxy Nexus smartphone.jpg — صورة هاتف",
        "preview_url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ad/Galaxy_Nexus_smartphone.jpg/500px-Galaxy_Nexus_smartphone.jpg",
        "page_url": "https://commons.wikimedia.org/wiki/File:Galaxy_Nexus_smartphone.jpg",
        "artist": "Laihiu",
        "license_name": "CC BY 2.5",
        "license_url": "https://creativecommons.org/licenses/by/2.5/",
        "license_notice": "نسب المؤلف ورابط الترخيص؛ اذكر أي تعديل أجريته على الصورة.",
        "attribution_required": True,
    },

    ("الأزياء والملابس", "تشكيلة صيفية"): {
        "title": "Clothing Rack of Jeans.jpg — صورة ملابس",
        "preview_url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/3/33/Clothing_Rack_of_Jeans.jpg/960px-Clothing_Rack_of_Jeans.jpg",
        "page_url": "https://commons.wikimedia.org/wiki/File:Clothing_Rack_of_Jeans.jpg",
        "artist": "Peter Griffin",
        "license_name": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "license_notice": "الملف مخصص للملكية العامة بموجب CC0؛ يُستحسن الاحتفاظ باسم المؤلف ورابط المصدر.",
        "attribution_required": False,
    },
    ("التعليم والدورات", "دورة تدريبية"): {
        "title": "Classroom ed.jpg — صورة قاعة تعليم",
        "preview_url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/69/Classroom_ed.jpg/960px-Classroom_ed.jpg",
        "page_url": "https://commons.wikimedia.org/wiki/File:Classroom_ed.jpg",
        "artist": "Rzcortes",
        "license_name": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "license_notice": "يجب نسب الصورة إلى المؤلف وإضافة رابط الترخيص؛ وأي تعديل يخضع لشرط المشاركة بالمثل.",
        "attribution_required": True,
    },
    ("السفر والسياحة", "رحلة سياحية"): {
        "title": "Zaamin Mountain Landscape.jpg — صورة طبيعة وجبال",
        "preview_url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/3/3f/Zaamin_Mountain_Landscape.jpg/960px-Zaamin_Mountain_Landscape.jpg",
        "page_url": "https://commons.wikimedia.org/wiki/File:Zaamin_Mountain_Landscape.jpg",
        "artist": "Humoyun Mehridinov",
        "license_name": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "license_notice": "يجب نسب الصورة إلى المؤلف وإضافة رابط الترخيص؛ وأي تعديل يخضع لشرط المشاركة بالمثل.",
        "attribution_required": True,
    },
    ("المتاجر والمنتجات", "عرض متجر"): {
        "title": "Fruits and vegetables at a grocery store.jpg — صورة متجر منتجات",
        "preview_url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/cd/Fruits_and_vegetables_at_a_grocery_store.jpg/960px-Fruits_and_vegetables_at_a_grocery_store.jpg",
        "page_url": "https://commons.wikimedia.org/wiki/File:Fruits_and_vegetables_at_a_grocery_store.jpg",
        "artist": "Kurt Kaiser",
        "license_name": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "license_notice": "الملف مخصص للملكية العامة بموجب CC0؛ يُستحسن الاحتفاظ باسم المؤلف ورابط المصدر.",
        "attribution_required": False,
    },
}


def get_template_photo_preview(template: dict) -> dict | None:
    """Return a licensed photo preview for selected topic variants, if curated."""
    if not isinstance(template, dict):
        return None
    key = (str(template.get("category", "")), str(template.get("topic", "")))
    asset = PHOTO_PREVIEW_ASSETS.get(key)
    return dict(asset) if asset else None




def render_preview_svg(template: dict) -> str:
    """Return an original, lightweight SVG preview for a catalog item."""
    title = escape(str(template["topic"]))
    category = escape(str(template["category"]))
    format_name = escape(str(template["format"]))
    style = escape(str(template["style"]))
    accent = template["accent"]
    deep = template["deep"]
    symbol = escape(str(template["symbol"]))
    layout = int(template["layout"]) % 5

    art_by_layout = [
        f"""
        <circle cx="180" cy="300" r="142" fill="{accent}" opacity=".16"/>
        <circle cx="180" cy="300" r="104" fill="none" stroke="{accent}" stroke-width="3" opacity=".8"/>
        <rect x="105" y="205" width="150" height="190" rx="28" fill="{deep}" stroke="{accent}" stroke-width="3"/>
        <path d="M135 250 Q180 210 225 250 L210 330 Q180 360 150 330 Z" fill="{accent}" opacity=".82"/>
        <circle cx="180" cy="292" r="28" fill="#0B1220" opacity=".72"/>
        """,
        f"""
        <rect x="70" y="125" width="300" height="350" rx="34" fill="{deep}" opacity=".88" stroke="{accent}" stroke-width="3"/>
        <rect x="105" y="165" width="230" height="18" rx="9" fill="{accent}" opacity=".8"/>
        <rect x="105" y="210" width="180" height="120" rx="20" fill="{accent}" opacity=".22"/>
        <circle cx="195" cy="270" r="44" fill="{accent}" opacity=".85"/>
        <rect x="105" y="365" width="190" height="14" rx="7" fill="#FFFFFF" opacity=".55"/>
        """,
        f"""
        <path d="M30 430 L260 115 L450 430 Z" fill="{accent}" opacity=".18"/>
        <path d="M90 450 L275 190 L455 450 Z" fill="{deep}" stroke="{accent}" stroke-width="3"/>
        <circle cx="270" cy="305" r="66" fill="{accent}" opacity=".9"/>
        <path d="M220 305 H320 M270 255 V355" stroke="#0B1220" stroke-width="12" stroke-linecap="round"/>
        """,
        f"""
        <rect x="70" y="165" width="320" height="250" rx="34" fill="{deep}" stroke="{accent}" stroke-width="3"/>
        <path d="M70 230 H390" stroke="{accent}" stroke-width="3" opacity=".8"/>
        <circle cx="230" cy="320" r="76" fill="{accent}" opacity=".82"/>
        <circle cx="230" cy="320" r="44" fill="{deep}" opacity=".72"/>
        <path d="M170 390 L290 250" stroke="#FFFFFF" stroke-width="10" opacity=".25"/>
        """,
        f"""
        <rect x="80" y="145" width="300" height="310" rx="28" fill="{deep}" stroke="{accent}" stroke-width="3"/>
        <rect x="112" y="178" width="236" height="120" rx="18" fill="{accent}" opacity=".2"/>
        <path d="M145 360 Q230 245 315 360" fill="none" stroke="{accent}" stroke-width="18" stroke-linecap="round"/>
        <circle cx="230" cy="340" r="34" fill="{accent}"/>
        """,
    ]
    art = art_by_layout[layout]

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="600" viewBox="0 0 900 600" role="img" aria-label="{title}">
      <defs>
        <linearGradient id="background" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#182842"/>
          <stop offset="100%" stop-color="#080E1B"/>
        </linearGradient>
        <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="{deep}" stop-opacity=".55"/>
          <stop offset="100%" stop-color="#0B1220" stop-opacity=".96"/>
        </linearGradient>
      </defs>
      <rect width="900" height="600" rx="28" fill="url(#background)"/>
      <rect x="20" y="20" width="860" height="560" rx="26" fill="none" stroke="{accent}" stroke-opacity=".45" stroke-width="2"/>
      <circle cx="785" cy="105" r="118" fill="{accent}" opacity=".08"/>
      <circle cx="70" cy="540" r="130" fill="{accent}" opacity=".06"/>
      <rect x="42" y="42" width="400" height="516" rx="24" fill="url(#panel)" opacity=".9"/>
      {art}
      <text x="835" y="90" fill="{accent}" font-size="25" font-weight="800" text-anchor="end" font-family="Cairo, Arial, sans-serif">NUMBER ONE</text>
      <text x="835" y="142" fill="#C7D2E5" font-size="19" text-anchor="end" font-family="Cairo, Arial, sans-serif" direction="rtl">{category}</text>
      <text x="835" y="260" fill="#FFFFFF" font-size="43" font-weight="800" text-anchor="end" font-family="Cairo, Arial, sans-serif" direction="rtl">{title}</text>
      <text x="835" y="315" fill="#C7D2E5" font-size="22" text-anchor="end" font-family="Cairo, Arial, sans-serif" direction="rtl">{format_name} · {style}</text>
      <rect x="625" y="390" width="210" height="62" rx="18" fill="{accent}"/>
      <text x="730" y="430" fill="#101827" font-size="23" font-weight="800" text-anchor="middle" font-family="Cairo, Arial, sans-serif" direction="rtl">اكتشف العرض</text>
      <text x="835" y="520" fill="#9AAAC3" font-size="16" text-anchor="end" font-family="Cairo, Arial, sans-serif" direction="rtl">معاينة SVG أصلية قابلة للتطوير</text>
      <text x="230" y="520" fill="{accent}" font-size="64" text-anchor="middle" font-family="Arial, sans-serif">{symbol}</text>
    </svg>"""


def render_preview_data_uri(template: dict) -> str:
    """Return a data URI so Streamlit can display the SVG without extra packages."""
    svg = render_preview_svg(template)
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"
