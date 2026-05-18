"""MCP tools — registered on the FastMCP instance defined in clamol.server.

Each tool is a thin shim: validate inputs (FastMCP infers schema from type
hints), call PyMOL via the XML-RPC client, return a typed Pydantic model or
basic type. Tools that need PyMOL kwargs route through `cmd.do(...)` command
strings — XML-RPC does not speak Python kwargs.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from mcp.server.fastmcp import Image

from clamol.models import AlignResult, AtomCoord, ObjectInfo, SelectionInfo
from clamol.rpc import get_client
from clamol.server import mcp


def _object_info(name: str) -> ObjectInfo:
    c = get_client()
    return ObjectInfo(
        name=name,
        n_atoms=int(c.count_atoms(name)),
        chains=list(c.get_chains(name)),
    )


@mcp.tool()
def load_structure(path: str, object_name: str | None = None) -> ObjectInfo:
    """Load a structure file (PDB, CIF, etc.) from a local path into PyMOL.

    If `object_name` is omitted, PyMOL derives the name from the filename.
    """
    c = get_client()
    name = object_name or Path(path).stem
    c.do(f"load {path}, {name}")
    return _object_info(name)


@mcp.tool()
def fetch_pdb(pdb_id: str, object_name: str | None = None) -> ObjectInfo:
    """Fetch a structure from RCSB PDB by 4-letter code and load it into PyMOL."""
    c = get_client()
    name = object_name or pdb_id.lower()
    c.do(f"fetch {pdb_id}, {name}, async=0")
    return _object_info(name)


@mcp.tool()
def list_objects() -> list[str]:
    """List the names of all loaded objects in the current PyMOL session."""
    return list(get_client().get_names("objects"))


@mcp.tool()
def select(name: str, selection: str) -> SelectionInfo:
    """Create a named selection from a PyMOL selection expression.

    Examples of selection expressions: `chain A`, `resi 10-20 and name CA`,
    `byres (1ubq around 5)`, `polymer.protein and not resn HOH`.
    """
    c = get_client()
    c.do(f"select {name}, {selection}")
    return SelectionInfo(name=name, n_atoms=int(c.count_atoms(name)))


@mcp.tool()
def show(representation: str, selection: str = "all") -> str:
    """Show a representation (cartoon, sticks, spheres, surface, ribbon, ...) for a selection."""
    get_client().do(f"show {representation}, {selection}")
    return f"show {representation} on {selection}"


@mcp.tool()
def hide(representation: str, selection: str = "all") -> str:
    """Hide a representation for a selection. Use representation='everything' to clear all."""
    get_client().do(f"hide {representation}, {selection}")
    return f"hide {representation} on {selection}"


@mcp.tool()
def color(color: str, selection: str = "all") -> str:
    """Color a selection. Color can be a named color (red, cyan, ...), a hex code, or `spectrum`."""
    get_client().do(f"color {color}, {selection}")
    return f"color {color} on {selection}"


@mcp.tool()
def render_png(width: int = 1200, height: int = 900, ray: bool = True) -> Image:
    """Render the current PyMOL view as a PNG and return it inline.

    `ray=True` produces a ray-traced image (slower but publication-quality).
    `ray=False` is a quick OpenGL snapshot — useful for iterating on views.
    The returned image is visible inline in the chat.
    """
    c = get_client()
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    c.do(f"png {path}, {width}, {height}, ray={1 if ray else 0}")
    return Image(path=path)
