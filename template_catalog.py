"""Original SVG starter templates for NUMBER ONE.

The catalog contains 400 structured starter variants (10 categories x 8 topics x 5 formats).
Previews are generated locally as SVG; no third-party stock image is redistributed.
These are starter concepts, not layered PSD/Canva source files.
"""
from __future__ import annotations

import base64
import hashlib
import re
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


def template_page_state_key(templates, page_size: int) -> str:
    """Build a stable Streamlit page selector key for the current filtered results.

    Fingerprint template IDs rather than only the result count so a different
    same-sized search result set starts pagination at page 1.
    """
    if isinstance(page_size, bool) or not isinstance(page_size, int) or page_size < 1:
        raise ValueError("page_size must be a positive integer.")
    template_ids = []
    for item in templates or []:
        if not isinstance(item, dict):
            raise ValueError("Template results must contain dictionaries.")
        template_ids.append(str(item.get("id") or ""))
    fingerprint = hashlib.sha256("|".join(template_ids).encode("utf-8")).hexdigest()[:16]
    return f"template_page_{fingerprint}_{page_size}"



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
    ("المطاعم والمقاهي", "برغر فاخر"): {
        "title": "Hamburger (black bg).jpg — صورة همبرغر",
        "preview_url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/47/Hamburger_%28black_bg%29.jpg/960px-Hamburger_%28black_bg%29.jpg",
        "page_url": "https://commons.wikimedia.org/wiki/File:Hamburger_(black_bg).jpg",
        "artist": "Len Rizzi (photographer), reprocessed by Off-shell",
        "license_name": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "license_notice": "الصورة المشتقة مخصصة للملكية العامة بموجب CC0 1.0؛ وتذكر صفحة الملف أن الصورة الأصلية من المعاهد الوطنية للصحة ضمن الملكية العامة.",
        "attribution_required": False,
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





def _safe_template_color(value, fallback="#F0CC70"):
    """Accept only six-digit hex colors before embedding values in SVG."""
    candidate = str(value or "").strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", candidate):
        return candidate.upper()
    fallback_value = str(fallback or "#F0CC70").strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", fallback_value):
        return fallback_value.upper()
    return "#F0CC70"


_LAYER_VISIBILITY_KEYS = (
    "headline",
    "subtitle",
    "price",
    "call_to_action",
    "symbol",
)

# مواضع افتراضية كنسب مئوية داخل مساحة آمنة لكل عنصر، حتى تبقى القوالب القديمة كما هي.
DEFAULT_LAYER_POSITIONS = {
    "headline": {"x": 100, "y": 57},
    "subtitle": {"x": 100, "y": 50},
    "price": {"x": 100, "y": 50},
    "call_to_action": {"x": 75, "y": 50},
    "symbol": {"x": 42, "y": 100},
}

# إعدادات طبقة الصورة كنسب من مساحة SVG (900 × 600).
DEFAULT_IMAGE_LAYER = {
    "visible": True,
    "x": 6,
    "y": 24,
    "width": 40,
    "height": 57,
    "rotation": 0,
}
_IMAGE_LAYER_BOUNDS = {
    "x": (0, 100),
    "y": (0, 100),
    "width": (10, 80),
    "height": (10, 80),
    "rotation": (-180, 180),
}

# طبقات هندسية مستقلة، مخفية افتراضيًا حتى لا يتغير شكل القوالب القديمة.
DEFAULT_SHAPE_LAYERS = {
    "rectangle": {
        "visible": False, "x": 8, "y": 12, "width": 24, "height": 18,
        "color": "#F0CC70", "stroke_width": 2, "rotation": 0,
    },
    "circle": {
        "visible": False, "x": 30, "y": 18, "width": 16, "height": 16,
        "color": "#243B53", "stroke_width": 2, "rotation": 0,
    },
    "line": {
        "visible": False, "x": 8, "y": 48, "width": 28, "height": 0,
        "color": "#F0CC70", "stroke_width": 5, "rotation": 0,
    },
}
_SHAPE_LAYER_BOUNDS = {
    "rectangle": {
        "x": (0, 100), "y": (0, 100), "width": (2, 80),
        "height": (2, 80), "stroke_width": (0, 12), "rotation": (-180, 180),
    },
    "circle": {
        "x": (0, 100), "y": (0, 100), "width": (2, 80),
        "height": (2, 80), "stroke_width": (0, 12), "rotation": (-180, 180),
    },
    "line": {
        "x": (0, 100), "y": (0, 100), "width": (1, 80),
        "height": (0, 80), "stroke_width": (1, 12), "rotation": (-180, 180),
    },
}

# ترتيب الطبقات من الخلف إلى الأمام، مع الحفاظ على ترتيب القوالب القديمة.
DEFAULT_LAYER_ORDER = (
    "image", "rectangle", "circle", "line",
    "headline", "subtitle", "price", "call_to_action", "symbol",
)


def normalize_layer_order(value=None) -> list:
    """Validate a partial or complete back-to-front order for editable layers."""
    if value is None:
        return list(DEFAULT_LAYER_ORDER)
    if not isinstance(value, (list, tuple)):
        raise ValueError("Layer order must be a list.")

    allowed = set(DEFAULT_LAYER_ORDER)
    normalized = []
    for layer_name in value:
        if not isinstance(layer_name, str) or layer_name not in allowed:
            raise ValueError("Layer order contains an unknown layer.")
        if layer_name in normalized:
            raise ValueError("Layer order cannot contain duplicate layers.")
        normalized.append(layer_name)

    normalized.extend(
        layer_name for layer_name in DEFAULT_LAYER_ORDER
        if layer_name not in normalized
    )
    return normalized


_LAYER_POSITION_BOUNDS = {
    "headline": {"x": (500, 835), "y": (180, 320)},
    "subtitle": {"x": (500, 835), "y": (250, 380)},
    "price": {"x": (500, 835), "y": (320, 420)},
    "call_to_action": {"x": (550, 790), "y": (370, 502)},
    "symbol": {"x": (80, 437), "y": (160, 520)},
}


def _normalize_layer_visibility(value) -> dict:
    """Return safe visibility flags for the editable SVG text layers."""
    visibility = {name: True for name in _LAYER_VISIBILITY_KEYS}
    if value is None:
        return visibility
    if not isinstance(value, dict):
        raise ValueError("Layer visibility must be an object.")
    for name in _LAYER_VISIBILITY_KEYS:
        candidate = value.get(name, True)
        if not isinstance(candidate, bool):
            raise ValueError(f"Layer visibility for {name} must be boolean.")
        visibility[name] = candidate
    return visibility


def _normalize_layer_positions(value) -> dict:
    """Validate percentage-based positions and fill missing values with legacy defaults."""
    positions = {
        name: dict(position)
        for name, position in DEFAULT_LAYER_POSITIONS.items()
    }
    if value is None:
        return positions
    if not isinstance(value, dict):
        raise ValueError("Layer positions must be an object.")

    for layer_name, coordinates in value.items():
        if layer_name not in DEFAULT_LAYER_POSITIONS:
            raise ValueError(f"Unknown template layer: {layer_name}.")
        if not isinstance(coordinates, dict):
            raise ValueError(f"Layer position for {layer_name} must be an object.")
        if set(coordinates) - {"x", "y"}:
            raise ValueError(f"Layer position for {layer_name} has unsupported axes.")

        normalized = {}
        for axis in ("x", "y"):
            candidate = coordinates.get(axis, DEFAULT_LAYER_POSITIONS[layer_name][axis])
            if (
                isinstance(candidate, bool)
                or not isinstance(candidate, int)
                or candidate < 0
                or candidate > 100
            ):
                raise ValueError(
                    f"Layer position {axis} for {layer_name} must be an integer from 0 to 100."
                )
            normalized[axis] = candidate
        positions[layer_name] = normalized

    return positions


def _layer_canvas_coordinate(layer_name: str, axis: str, positions: dict) -> int:
    """Map a normalized slider value to a safe SVG canvas coordinate."""
    start, end = _LAYER_POSITION_BOUNDS[layer_name][axis]
    percentage = positions[layer_name][axis]
    return int(round(start + (end - start) * percentage / 100))


def normalize_image_layer(value=None) -> dict:
    """Validate image visibility, position, and size as bounded percentages."""
    layer = dict(DEFAULT_IMAGE_LAYER)
    if value is None:
        return layer
    if not isinstance(value, dict):
        raise ValueError("Image layer settings must be an object.")
    unknown = set(value) - set(DEFAULT_IMAGE_LAYER)
    if unknown:
        raise ValueError("Image layer settings contain unsupported fields.")

    visible = value.get("visible", layer["visible"])
    if not isinstance(visible, bool):
        raise ValueError("Image layer visibility must be boolean.")
    layer["visible"] = visible

    for field, (minimum, maximum) in _IMAGE_LAYER_BOUNDS.items():
        candidate = value.get(field, layer[field])
        if (
            isinstance(candidate, bool)
            or not isinstance(candidate, int)
            or candidate < minimum
            or candidate > maximum
        ):
            raise ValueError(
                f"Image layer {field} must be an integer from {minimum} to {maximum}."
            )
        layer[field] = candidate
    return layer


def normalize_shape_layers(value=None) -> dict:
    """Validate the three independent geometric SVG layers."""
    layers = {
        name: dict(settings)
        for name, settings in DEFAULT_SHAPE_LAYERS.items()
    }
    if value is None:
        return layers
    if not isinstance(value, dict):
        raise ValueError("Shape layers must be an object.")
    if set(value) - set(DEFAULT_SHAPE_LAYERS):
        raise ValueError("Shape layers contain an unknown layer.")

    for layer_name, settings in value.items():
        if not isinstance(settings, dict):
            raise ValueError(f"Shape layer {layer_name} must be an object.")
        if set(settings) - set(DEFAULT_SHAPE_LAYERS[layer_name]):
            raise ValueError(f"Shape layer {layer_name} contains unsupported fields.")

        normalized = dict(DEFAULT_SHAPE_LAYERS[layer_name])
        visible = settings.get("visible", normalized["visible"])
        if not isinstance(visible, bool):
            raise ValueError(f"Shape layer {layer_name} visibility must be boolean.")
        normalized["visible"] = visible

        for field, (minimum, maximum) in _SHAPE_LAYER_BOUNDS[layer_name].items():
            candidate = settings.get(field, normalized[field])
            if (
                isinstance(candidate, bool)
                or not isinstance(candidate, int)
                or candidate < minimum
                or candidate > maximum
            ):
                raise ValueError(
                    f"Shape layer {layer_name} {field} must be an integer from {minimum} to {maximum}."
                )
            normalized[field] = candidate

        color = str(settings.get("color", normalized["color"]) or "").strip()
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            raise ValueError(f"Shape layer {layer_name} color must be a six-digit hex color.")
        normalized["color"] = color.upper()
        layers[layer_name] = normalized

    return layers


def customize_template(
    template: dict,
    *,
    headline=None,
    subtitle=None,
    price=None,
    call_to_action=None,
    accent=None,
    deep=None,
    symbol=None,
    layer_visibility=None,
    layer_positions=None,
    image_layer=None,
    shape_layers=None,
    layer_order=None,
) -> dict:
    """Return a safe editable copy of a catalog template without mutating its source."""
    if not isinstance(template, dict):
        raise ValueError("Template metadata must be an object.")

    result = dict(template)
    topic = str(result.get("topic") or "تصميم إعلان").strip()
    format_name = str(result.get("format") or "").strip()
    style_name = str(result.get("style") or "").strip()
    default_subtitle = " · ".join(part for part in (format_name, style_name) if part)

    text_values = {
        "headline": (headline, result.get("headline") or topic, 44),
        "subtitle": (subtitle, result.get("subtitle") or default_subtitle, 70),
        "price": (price, result.get("price") or "", 28),
        "call_to_action": (call_to_action, result.get("call_to_action") or "اكتشف العرض", 28),
        "symbol": (symbol, result.get("symbol") or "✦", 8),
    }
    for field, (provided, fallback, limit) in text_values.items():
        raw_value = provided if provided is not None else fallback
        cleaned = str(raw_value or "").strip()
        if not cleaned and fallback and field != "price":
            cleaned = str(fallback).strip()
        result[field] = cleaned[:limit]

    result["accent"] = _safe_template_color(
        accent if accent is not None else result.get("accent"),
        result.get("accent") or "#F0CC70",
    )
    result["deep"] = _safe_template_color(
        deep if deep is not None else result.get("deep"),
        result.get("deep") or "#243B53",
    )
    visibility_source = (
        layer_visibility
        if layer_visibility is not None
        else result.get("layer_visibility")
    )
    result["layer_visibility"] = _normalize_layer_visibility(visibility_source)
    position_source = (
        layer_positions
        if layer_positions is not None
        else result.get("layer_positions")
    )
    result["layer_positions"] = _normalize_layer_positions(position_source)
    image_layer_source = (
        image_layer if image_layer is not None else result.get("image_layer")
    )
    result["image_layer"] = normalize_image_layer(image_layer_source)
    shape_source = shape_layers if shape_layers is not None else result.get("shape_layers")
    result["shape_layers"] = normalize_shape_layers(shape_source)
    order_source = layer_order if layer_order is not None else result.get("layer_order")
    result["layer_order"] = normalize_layer_order(order_source)
    return result


def _photo_layer_markup(
    photo_bytes: bytes | None,
    image_layer=None,
) -> str:
    """Embed a bounded raster image as an independently positioned SVG layer."""
    if not isinstance(photo_bytes, (bytes, bytearray)):
        return ""
    payload = bytes(photo_bytes)
    if not payload or len(payload) > 900_000:
        return ""

    layer = normalize_image_layer(image_layer)
    if not layer["visible"]:
        return ""

    if payload.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif payload.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif len(payload) >= 12 and payload[:4] == b"RIFF" and payload[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        return ""

    x = int(round(900 * layer["x"] / 100))
    y = int(round(600 * layer["y"] / 100))
    width = int(round(900 * layer["width"] / 100))
    height = int(round(600 * layer["height"] / 100))
    center_x = x + width // 2
    center_y = y + height // 2
    rotation = layer["rotation"]
    transform = (
        f' transform="rotate({rotation} {center_x} {center_y})"'
        if rotation else ""
    )
    encoded = base64.b64encode(payload).decode("ascii")
    return (
        '<defs><clipPath id="mediaPhotoClip">'
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="20"/>'
        '</clipPath></defs>'
        f'<image href="data:{mime};base64,{encoded}"{transform} '
        f'x="{x}" y="{y}" width="{width}" height="{height}" '
        'preserveAspectRatio="xMidYMid slice" '
        'clip-path="url(#mediaPhotoClip)" '
        'aria-label="صورة مضافة من مكتبة الوسائط"/>'
    )


def _shape_layer_markups(value=None) -> dict:
    """Render each safe geometric layer separately so its z-order is editable."""
    layers = normalize_shape_layers(value)
    fragments = {name: "" for name in layers}
    for layer_name, layer in layers.items():
        if not layer["visible"]:
            continue
        x = int(round(900 * layer["x"] / 100))
        y = int(round(600 * layer["y"] / 100))
        width = int(round(900 * layer["width"] / 100))
        height = int(round(600 * layer["height"] / 100))
        color = layer["color"]
        stroke_width = layer["stroke_width"]
        rotation = layer["rotation"]

        if layer_name in {"rectangle", "circle"}:
            width = min(width, 900 - x)
            height = min(height, 600 - y)
            if width <= 0 or height <= 0:
                continue
            center_x = x + width // 2
            center_y = y + height // 2
            transform = (
                f' transform="rotate({rotation} {center_x} {center_y})"'
                if rotation else ""
            )
            if layer_name == "rectangle":
                fragments[layer_name] = (
                    f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
                    f'rx="12" fill="{color}" fill-opacity=".18" stroke="{color}" '
                    f'stroke-width="{stroke_width}"{transform} aria-label="طبقة المستطيل"/>'
                )
            else:
                fragments[layer_name] = (
                    f'<ellipse cx="{center_x}" cy="{center_y}" rx="{max(1, width // 2)}" '
                    f'ry="{max(1, height // 2)}" fill="{color}" fill-opacity=".18" '
                    f'stroke="{color}" stroke-width="{stroke_width}"{transform} '
                    'aria-label="طبقة الدائرة"/>'
                )
        else:
            end_x = min(900, x + width)
            end_y = min(600, y + height)
            center_x = (x + end_x) // 2
            center_y = (y + end_y) // 2
            transform = (
                f' transform="rotate({rotation} {center_x} {center_y})"'
                if rotation else ""
            )
            fragments[layer_name] = (
                f'<line x1="{x}" y1="{y}" x2="{end_x}" y2="{end_y}" '
                f'stroke="{color}" stroke-width="{stroke_width}"{transform} '
                'stroke-linecap="round" aria-label="طبقة الخط"/>'
            )
    return fragments


def _shape_layers_markup(value=None) -> str:
    """Backward-compatible combined markup in the original geometric order."""
    fragments = _shape_layer_markups(value)
    return "".join(fragments[name] for name in DEFAULT_SHAPE_LAYERS)


def render_preview_svg(template: dict, photo_bytes: bytes | None = None) -> str:
    """Return an original SVG preview, optionally with a safe raster image layer."""
    raw_format = str(template["format"])
    raw_style = str(template["style"])
    title = escape(str(template.get("headline") or template["topic"]))
    category = escape(str(template["category"]))
    format_name = escape(raw_format)
    style = escape(raw_style)
    subtitle = escape(str(
        template.get("subtitle") or " · ".join(part for part in (raw_format, raw_style) if part)
    ))
    price = escape(str(template.get("price") or "").strip())
    call_to_action = escape(str(template.get("call_to_action") or "اكتشف العرض"))
    accent = _safe_template_color(template.get("accent"), "#F0CC70")
    deep = _safe_template_color(template.get("deep"), "#243B53")
    symbol = escape(str(template.get("symbol") or "✦"))
    layout = int(template["layout"]) % 5
    layer_positions = _normalize_layer_positions(template.get("layer_positions"))
    headline_x = _layer_canvas_coordinate("headline", "x", layer_positions)
    headline_y = _layer_canvas_coordinate("headline", "y", layer_positions)
    subtitle_x = _layer_canvas_coordinate("subtitle", "x", layer_positions)
    subtitle_y = _layer_canvas_coordinate("subtitle", "y", layer_positions)
    price_x = _layer_canvas_coordinate("price", "x", layer_positions)
    price_y = _layer_canvas_coordinate("price", "y", layer_positions)
    cta_x = _layer_canvas_coordinate("call_to_action", "x", layer_positions)
    cta_y = _layer_canvas_coordinate("call_to_action", "y", layer_positions)
    symbol_x = _layer_canvas_coordinate("symbol", "x", layer_positions)
    symbol_y = _layer_canvas_coordinate("symbol", "y", layer_positions)

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
    photo_markup = _photo_layer_markup(photo_bytes, template.get("image_layer"))
    shape_markups = _shape_layer_markups(template.get("shape_layers"))
    layer_visibility = _normalize_layer_visibility(template.get("layer_visibility"))
    accessible_label = title if layer_visibility["headline"] else category
    headline_markup = (
        f'<text x="{headline_x}" y="{headline_y}" fill="#FFFFFF" font-size="43" font-weight="800" text-anchor="end" textLength="360" lengthAdjust="spacingAndGlyphs" font-family="Cairo, Arial, sans-serif" direction="rtl">{title}</text>'
        if layer_visibility["headline"] else ""
    )
    subtitle_markup = (
        f'<text x="{subtitle_x}" y="{subtitle_y}" fill="#C7D2E5" font-size="22" text-anchor="end" textLength="360" lengthAdjust="spacingAndGlyphs" font-family="Cairo, Arial, sans-serif" direction="rtl">{subtitle}</text>'
        if layer_visibility["subtitle"] else ""
    )
    price_markup = (
        f'<text x="{price_x}" y="{price_y}" fill="{accent}" font-size="31" font-weight="800" text-anchor="end" font-family="Cairo, Arial, sans-serif" direction="rtl">{price}</text>'
        if price and layer_visibility["price"] else ""
    )
    cta_markup = (
        f'<rect x="{cta_x - 105}" y="{cta_y - 31}" width="210" height="62" rx="18" fill="{accent}"/>'
        f'<text x="{cta_x}" y="{cta_y + 9}" fill="#101827" font-size="23" font-weight="800" text-anchor="middle" font-family="Cairo, Arial, sans-serif" direction="rtl">{call_to_action}</text>'
        if layer_visibility["call_to_action"] else ""
    )
    symbol_markup = (
        f'<text x="{symbol_x}" y="{symbol_y}" fill="{accent}" font-size="64" text-anchor="middle" font-family="Arial, sans-serif">{symbol}</text>'
        if layer_visibility["symbol"] else ""
    )
    editable_layer_markups = {
        "image": photo_markup,
        "rectangle": shape_markups["rectangle"],
        "circle": shape_markups["circle"],
        "line": shape_markups["line"],
        "headline": headline_markup,
        "subtitle": subtitle_markup,
        "price": price_markup,
        "call_to_action": cta_markup,
        "symbol": symbol_markup,
    }
    editable_layer_markup = "".join(
        editable_layer_markups[name]
        for name in normalize_layer_order(template.get("layer_order"))
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="600" viewBox="0 0 900 600" role="img" aria-label="{accessible_label}">
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
      <text x="835" y="520" fill="#9AAAC3" font-size="16" text-anchor="end" font-family="Cairo, Arial, sans-serif" direction="rtl">معاينة SVG أصلية قابلة للتطوير</text>
      <g id="editable-layer-stack">
        {editable_layer_markup}
      </g>
    </svg>"""


def render_preview_data_uri(
    template: dict,
    photo_bytes: bytes | None = None,
) -> str:
    """Return a data URI for the SVG preview, including an optional photo layer."""
    svg = render_preview_svg(template, photo_bytes=photo_bytes)
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"
