"""Validated pointer-drag updates for NUMBER ONE template layers."""
from __future__ import annotations

import math

from template_catalog import (
    DEFAULT_LAYER_POSITIONS,
    _LAYER_POSITION_BOUNDS,
    customize_template,
    normalize_image_layer,
    normalize_shape_layers,
)

_TEXT_LAYERS = frozenset(DEFAULT_LAYER_POSITIONS)
_SHAPE_LAYERS = frozenset(("rectangle", "circle", "line"))


def _finite_delta(value, axis: str) -> float:
    """Accept finite SVG-space deltas within the 900 x 600 design canvas."""
    maximum = 900 if axis == "x" else 600
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Drag delta {axis} must be numeric.")
    candidate = float(value)
    if not math.isfinite(candidate) or abs(candidate) > maximum:
        raise ValueError(f"Drag delta {axis} is outside the supported canvas.")
    return candidate


def _percent(value: float) -> int:
    return max(0, min(100, int(round(value))))


def apply_canvas_drag(template: dict, payload: dict) -> dict:
    """Apply a pointer drag to one editable layer and return a validated template.

    Pointer deltas are expressed in the SVG viewBox coordinate system (900 x 600).
    The returned data uses the existing percentage-based project schema.
    """
    if not isinstance(template, dict):
        raise ValueError("A template object is required.")
    if not isinstance(payload, dict):
        raise ValueError("A drag event object is required.")

    layer = payload.get("layer")
    if not isinstance(layer, str):
        raise ValueError("The dragged layer name is invalid.")
    if layer != "image" and layer not in _TEXT_LAYERS and layer not in _SHAPE_LAYERS:
        raise ValueError("The dragged layer is not editable.")

    dx = _finite_delta(payload.get("dx"), "x")
    dy = _finite_delta(payload.get("dy"), "y")

    if layer in _TEXT_LAYERS:
        normalized = customize_template(template)
        positions = {
            name: dict(position)
            for name, position in normalized["layer_positions"].items()
        }
        x_start, x_end = _LAYER_POSITION_BOUNDS[layer]["x"]
        y_start, y_end = _LAYER_POSITION_BOUNDS[layer]["y"]
        positions[layer]["x"] = _percent(
            positions[layer]["x"] + dx * 100 / (x_end - x_start)
        )
        positions[layer]["y"] = _percent(
            positions[layer]["y"] + dy * 100 / (y_end - y_start)
        )
        return customize_template(template, layer_positions=positions)

    if layer == "image":
        image_layer = normalize_image_layer(template.get("image_layer"))
        image_layer["x"] = _percent(image_layer["x"] + dx * 100 / 900)
        image_layer["y"] = _percent(image_layer["y"] + dy * 100 / 600)
        return customize_template(template, image_layer=image_layer)

    shape_layers = normalize_shape_layers(template.get("shape_layers"))
    shape_layers[layer]["x"] = _percent(shape_layers[layer]["x"] + dx * 100 / 900)
    shape_layers[layer]["y"] = _percent(shape_layers[layer]["y"] + dy * 100 / 600)
    return customize_template(template, shape_layers=shape_layers)
