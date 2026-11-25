"""Client-side PNG export for trusted, locally generated NUMBER ONE SVG previews."""
from __future__ import annotations

import base64
import json
import re
import xml.etree.ElementTree as ET


_MAX_SVG_BYTES = 4_000_000
_EXTERNAL_RESOURCE = re.compile(r"url\(\s*['\"]?(?:https?:)?//", re.IGNORECASE)


def _safe_png_filename(value: str) -> str:
    """Strip path components and characters unsafe in a download filename."""
    candidate = str(value or "number_one_design.png").replace("\\", "/").split("/")[-1]
    candidate = re.sub(r"[\x00-\x1f\x7f\"'<>|:*?]+", "_", candidate).strip(" ._")
    if not candidate:
        candidate = "number_one_design"
    if not candidate.casefold().endswith(".png"):
        candidate += ".png"
    return candidate


def build_png_export_html(
    svg: str,
    filename: str = "number_one_design.png",
    scale: int = 2,
) -> str:
    """Build a self-contained browser-side SVG-to-PNG download component.

    The SVG is embedded as base64, so the browser does not need to fetch a
    remote asset. Only a well-formed SVG without scripts, event attributes,
    foreign objects, or external resources is accepted.
    """
    if not isinstance(svg, str) or not svg.strip():
        raise ValueError("SVG content must be a non-empty string.")
    payload = svg.encode("utf-8")
    if len(payload) > _MAX_SVG_BYTES:
        raise ValueError("SVG content exceeds the PNG export size limit.")
    if "<!DOCTYPE" in svg.upper() or "<!ENTITY" in svg.upper():
        raise ValueError("SVG document types and entities are not supported.")
    if isinstance(scale, bool) or not isinstance(scale, int) or not 1 <= scale <= 3:
        raise ValueError("PNG export scale must be an integer from 1 to 3.")

    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ValueError("SVG content is not well-formed XML.") from exc
    if root.tag.rsplit("}", 1)[-1].casefold() != "svg":
        raise ValueError("PNG export accepts SVG documents only.")

    for element in root.iter():
        tag_name = element.tag.rsplit("}", 1)[-1].casefold()
        if tag_name in {"script", "foreignobject"}:
            raise ValueError("SVG contains an unsupported active element.")
        for attribute, value in element.attrib.items():
            attribute_name = attribute.rsplit("}", 1)[-1].casefold()
            if attribute_name.startswith("on"):
                raise ValueError("SVG event attributes are not supported.")
            if attribute_name in {"href", "src"}:
                resource = str(value).strip()
                if resource and not (
                    resource.startswith("#") or resource.startswith("data:image/")
                ):
                    raise ValueError("SVG external resources are not supported.")
    if _EXTERNAL_RESOURCE.search(svg):
        raise ValueError("SVG external CSS resources are not supported.")

    encoded_svg = base64.b64encode(payload).decode("ascii")
    safe_filename = json.dumps(_safe_png_filename(filename))
    script = r"""
<script>
(() => {
  const button = document.getElementById("number-one-png-export");
  const status = document.getElementById("number-one-png-status");
  const svgBase64 = "__SVG_BASE64__";
  const filename = __PNG_FILENAME__;
  const scale = __PNG_SCALE__;

  button.addEventListener("click", () => {
    button.disabled = true;
    status.textContent = "جارٍ تجهيز ملف PNG...";
    let svgUrl = "";
    const restoreButton = () => { button.disabled = false; };
    try {
      const binary = atob(svgBase64);
      const bytes = new Uint8Array(binary.length);
      for (let index = 0; index < binary.length; index += 1) {
        bytes[index] = binary.charCodeAt(index);
      }
      const svgBlob = new Blob([bytes], { type: "image/svg+xml;charset=utf-8" });
      svgUrl = URL.createObjectURL(svgBlob);
      const image = new Image();
      image.onload = async () => {
        try {
          const sourceWidth = image.naturalWidth || 900;
          const sourceHeight = image.naturalHeight || 600;
          const canvas = document.createElement("canvas");
          canvas.width = Math.round(sourceWidth * scale);
          canvas.height = Math.round(sourceHeight * scale);
          const context = canvas.getContext("2d");
          if (!context) throw new Error("تعذر إنشاء مساحة تحويل الصورة.");
          context.drawImage(image, 0, 0, canvas.width, canvas.height);
          const pngBlob = await new Promise(resolve => canvas.toBlob(resolve, "image/png"));
          if (!pngBlob) throw new Error("لم يتمكن المتصفح من إنشاء ملف PNG.");
          const pngUrl = URL.createObjectURL(pngBlob);
          const link = document.createElement("a");
          link.href = pngUrl;
          link.download = filename;
          link.rel = "noopener";
          document.body.appendChild(link);
          link.click();
          link.remove();
          window.setTimeout(() => URL.revokeObjectURL(pngUrl), 1500);
          status.textContent = "تم تجهيز PNG بدقة " + canvas.width + " × " + canvas.height + ".";
        } catch (error) {
          status.textContent = error && error.message ? error.message : "تعذر إنشاء PNG في هذا المتصفح.";
        } finally {
          URL.revokeObjectURL(svgUrl);
          restoreButton();
        }
      };
      image.onerror = () => {
        status.textContent = "تعذر قراءة معاينة SVG لتحويلها إلى PNG.";
        URL.revokeObjectURL(svgUrl);
        restoreButton();
      };
      image.src = svgUrl;
    } catch (error) {
      status.textContent = error && error.message ? error.message : "تعذر بدء تحويل PNG.";
      if (svgUrl) URL.revokeObjectURL(svgUrl);
      restoreButton();
    }
  });
})();
</script>
"""
    script = (
        script.replace("__SVG_BASE64__", encoded_svg)
        .replace("__PNG_FILENAME__", safe_filename)
        .replace("__PNG_SCALE__", str(scale))
    )
    return """<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  html, body { margin: 0; padding: 0; background: transparent; font-family: Arial, sans-serif; }
  .export-row { display: flex; align-items: center; gap: 10px; min-height: 64px; }
  button { border: 0; border-radius: 10px; padding: 12px 18px; min-height: 44px;
    width: 100%; color: #111827; background: linear-gradient(135deg,#f0cc70,#b78a35);
    font-size: 14px; font-weight: 700; cursor: pointer; }
  button:disabled { opacity: .65; cursor: wait; }
  #number-one-png-status { color: #d7dfef; font-size: 11px; line-height: 1.5; }
</style>
</head>
<body>
  <div class="export-row">
    <button id="number-one-png-export" type="button">تنزيل التصميم بصيغة PNG (جودة 2×)</button>
  </div>
  <div id="number-one-png-status" role="status" aria-live="polite"></div>
""" + script + """
</body>
</html>
"""
