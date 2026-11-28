"""Local Streamlit component for mouse and touch editing of SVG template layers."""
from pathlib import Path

import streamlit.components.v1 as components

from template_catalog import DEFAULT_LAYER_POSITIONS, DEFAULT_SHAPE_LAYERS


_EDITABLE_LAYERS = frozenset(
    {"image", *DEFAULT_LAYER_POSITIONS, *DEFAULT_SHAPE_LAYERS}
)


_FRONTEND = (Path(__file__).parent / "canvas_editor_frontend").resolve()
_component = components.declare_component(
    "number_one_canvas_editor",
    path=str(_FRONTEND),
)


def render_canvas_editor(
    svg: str,
    template_id: str,
    key: str | None = None,
    selected_layer: str | None = None,
):
    """Render an interactive SVG canvas and return the last validated drag event."""
    if not isinstance(svg, str) or not svg.lstrip().startswith("<svg"):
        raise ValueError("The canvas editor requires a generated SVG document.")
    if selected_layer is not None and selected_layer not in _EDITABLE_LAYERS:
        raise ValueError("The selected canvas layer is not editable.")
    return _component(
        svg=svg,
        template_id=str(template_id or ""),
        selected_layer=selected_layer,
        key=key,
        default=None,
    )
