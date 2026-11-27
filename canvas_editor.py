"""Local Streamlit component for mouse and touch editing of SVG template layers."""
from pathlib import Path

import streamlit.components.v1 as components


_FRONTEND = Path(__file__).parent / "canvas_editor_frontend"
_component = components.declare_component(
    "number_one_canvas_editor",
    path=str(_FRONTEND),
)


def render_canvas_editor(svg: str, template_id: str, key: str | None = None):
    """Render an interactive SVG canvas and return the last validated drag event."""
    if not isinstance(svg, str) or not svg.lstrip().startswith("<svg"):
        raise ValueError("The canvas editor requires a generated SVG document.")
    return _component(
        svg=svg,
        template_id=str(template_id or ""),
        key=key,
        default=None,
    )
