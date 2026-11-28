import base64
import re
import unittest

from png_export import build_png_export_html


class PngExportTests(unittest.TestCase):
    SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="600"><rect width="900" height="600" fill="#112233"/><text x="20" y="40">NUMBER ONE</text></svg>'

    def test_export_component_embeds_svg_and_uses_two_times_scale(self):
        document = build_png_export_html(self.SVG)
        match = re.search(r'const svgBase64 = "([A-Za-z0-9+/=]+)";', document)
        self.assertIsNotNone(match)
        self.assertEqual(base64.b64decode(match.group(1)).decode("utf-8"), self.SVG)
        self.assertIn("const scale = 2;", document)
        self.assertIn('canvas.toBlob(resolve, "image/png")', document)
        self.assertIn("canvas.width = Math.round(sourceWidth * scale)", document)

    def test_export_filename_removes_paths_and_unsafe_characters(self):
        document = build_png_export_html(self.SVG, filename="../../bad:name?.png")
        self.assertIn('const filename = "bad_name_.png";', document)
        self.assertNotIn("../../bad:name?", document)

    def test_export_adds_png_extension_when_missing(self):
        document = build_png_export_html(self.SVG, filename="NUMBER_ONE_001")
        self.assertIn('const filename = "NUMBER_ONE_001.png";', document)

    def test_export_accepts_only_integer_scale_from_one_to_three(self):
        for scale in (0, 4, True, 1.5, "2"):
            with self.subTest(scale=scale):
                with self.assertRaises(ValueError):
                    build_png_export_html(self.SVG, scale=scale)

    def test_export_rejects_empty_malformed_and_non_svg_documents(self):
        for invalid in ("", "not svg", "<html></html>", "<svg><broken></svg>"):
            with self.subTest(svg=invalid):
                with self.assertRaises(ValueError):
                    build_png_export_html(invalid)

    def test_export_rejects_active_or_external_svg_content(self):
        unsafe_svgs = (
            '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><rect onload="alert(1)"/></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><image href="https://example.com/a.png"/></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><rect style="fill:url(https://example.com/a)"/></svg>',
            '<!DOCTYPE svg [<!ENTITY x "bad">]><svg>&x;</svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><foreignObject/></svg>',
        )
        for svg in unsafe_svgs:
            with self.subTest(svg=svg):
                with self.assertRaises(ValueError):
                    build_png_export_html(svg)

    def test_export_rejects_css_imports_and_relative_resource_urls(self):
        unsafe_svgs = (
            '<svg xmlns="http://www.w3.org/2000/svg"><style>@import "https://example.com/theme.css";</style></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><rect style="filter:url(/assets/filter.svg#blur)"/></svg>',
        )
        for svg in unsafe_svgs:
            with self.subTest(svg=svg):
                with self.assertRaises(ValueError):
                    build_png_export_html(svg)

    def test_export_allows_raster_data_images_but_rejects_nested_svg_data(self):
        raster_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<image href="data:image/jpeg;base64,/9j/2Q=="/>'
            '</svg>'
        )
        self.assertIn("number-one-png-export", build_png_export_html(raster_svg))

        nested_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<image href="data:image/svg+xml;base64,PHN2Zy8+"/>'
            '</svg>'
        )
        with self.assertRaises(ValueError):
            build_png_export_html(nested_svg)

    def test_export_rejects_payloads_above_size_limit(self):
        large_svg = '<svg xmlns="http://www.w3.org/2000/svg">' + (" " * 4_000_001) + "</svg>"
        with self.assertRaises(ValueError):
            build_png_export_html(large_svg)


if __name__ == "__main__":
    unittest.main()
