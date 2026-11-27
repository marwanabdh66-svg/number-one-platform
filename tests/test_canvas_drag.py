import math
import unittest

from canvas_drag import apply_canvas_drag
from template_catalog import TEMPLATE_CATALOG, customize_template


class CanvasDragTests(unittest.TestCase):
    def setUp(self):
        self.template = customize_template(
            TEMPLATE_CATALOG[0],
            layer_positions={
                "headline": {"x": 50, "y": 50},
                "subtitle": {"x": 50, "y": 50},
                "price": {"x": 50, "y": 50},
                "call_to_action": {"x": 50, "y": 50},
                "symbol": {"x": 50, "y": 50},
            },
        )

    def test_text_drag_converts_svg_pixels_to_safe_layer_percentages(self):
        moved = apply_canvas_drag(
            self.template,
            {"layer": "headline", "dx": 67, "dy": 35, "token": "drag-1"},
        )
        self.assertEqual(moved["layer_positions"]["headline"], {"x": 70, "y": 75})
        self.assertEqual(moved["layer_positions"]["subtitle"], {"x": 50, "y": 50})

    def test_image_drag_updates_only_image_position(self):
        moved = apply_canvas_drag(
            self.template,
            {"layer": "image", "dx": 90, "dy": 60},
        )
        self.assertEqual(moved["image_layer"]["x"], 16)
        self.assertEqual(moved["image_layer"]["y"], 34)
        self.assertEqual(moved["image_layer"]["width"], self.template["image_layer"]["width"])

    def test_shape_drag_updates_selected_shape_only(self):
        moved = apply_canvas_drag(
            self.template,
            {"layer": "rectangle", "dx": 90, "dy": 60},
        )
        self.assertEqual(moved["shape_layers"]["rectangle"]["x"], 18)
        self.assertEqual(moved["shape_layers"]["rectangle"]["y"], 22)
        self.assertEqual(moved["shape_layers"]["circle"], self.template["shape_layers"]["circle"])

    def test_drag_clamps_text_layer_to_its_safe_percentage_range(self):
        edge_template = customize_template(
            self.template,
            layer_positions={"headline": {"x": 100, "y": 0}},
        )
        moved = apply_canvas_drag(
            edge_template,
            {"layer": "headline", "dx": 900, "dy": -600},
        )
        self.assertEqual(moved["layer_positions"]["headline"], {"x": 100, "y": 0})

    def test_drag_rejects_unknown_layers_and_invalid_deltas(self):
        invalid_payloads = (
            {"layer": "background", "dx": 1, "dy": 1},
            {"layer": "headline", "dx": True, "dy": 1},
            {"layer": "headline", "dx": math.nan, "dy": 1},
            {"layer": "headline", "dx": 901, "dy": 1},
            {"layer": "headline", "dx": 1, "dy": 601},
            {"layer": "headline", "dx": 1},
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    apply_canvas_drag(self.template, payload)

    def test_drag_requires_template_and_payload_objects(self):
        with self.assertRaises(ValueError):
            apply_canvas_drag(None, {"layer": "headline", "dx": 1, "dy": 1})
        with self.assertRaises(ValueError):
            apply_canvas_drag(self.template, None)


if __name__ == "__main__":
    unittest.main()
