import unittest
from pathlib import Path
from unittest.mock import patch

from canvas_editor import render_canvas_editor


class CanvasEditorTests(unittest.TestCase):
    SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="600"></svg>'

    @patch("canvas_editor._component")
    def test_passes_selected_layer_to_component(self, component):
        component.return_value = None
        render_canvas_editor(
            self.SVG,
            template_id="NO-0001",
            key="canvas-test",
            selected_layer="headline",
        )
        component.assert_called_once()
        self.assertEqual(component.call_args.kwargs["selected_layer"], "headline")
        self.assertEqual(component.call_args.kwargs["template_id"], "NO-0001")

    @patch("canvas_editor._component")
    def test_allows_no_selected_layer(self, component):
        component.return_value = None
        render_canvas_editor(self.SVG, template_id="NO-0001")
        self.assertIsNone(component.call_args.kwargs["selected_layer"])

    def test_rejects_unknown_selected_layer(self):
        with self.assertRaises(ValueError):
            render_canvas_editor(
                self.SVG,
                template_id="NO-0001",
                selected_layer="background",
            )

    def test_rejects_invalid_svg(self):
        with self.assertRaises(ValueError):
            render_canvas_editor("not-svg", template_id="NO-0001")

    def test_frontend_keeps_selection_overlay_and_reports_selection_events(self):
        frontend = (
            Path(__file__).parents[1] / "canvas_editor_frontend" / "index.html"
        ).read_text(encoding="utf-8")
        self.assertIn("function updateSelection()", frontend)
        self.assertIn('action: "select"', frontend)
        self.assertIn('event.key !== "Escape"', frontend)
        self.assertIn('data-editor-overlay', frontend)


if __name__ == "__main__":
    unittest.main()
