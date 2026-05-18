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


@mcp.tool()
def get_chains(object: str) -> list[str]:
    """Return the chain identifiers present in an object (e.g. ['A', 'B'])."""
    return list(get_client().get_chains(object))


def _align_tuple(result: list) -> AlignResult:
    """PyMOL align/super return: [rmsd, n_atoms, n_cycles, rmsd_init, n_init, raw_rmsd, n_raw]."""
    return AlignResult(
        rmsd=float(result[0]),
        n_atoms=int(result[1]),
        n_cycles=int(result[2]),
        rmsd_initial=float(result[3]),
        n_atoms_initial=int(result[4]),
    )


@mcp.tool()
def align(mobile: str, target: str) -> AlignResult:
    """Sequence-then-structure alignment via cmd.align. Moves `mobile` onto `target`.

    Best when sequences are similar (>30% identity). For more distant pairs,
    prefer `super_align` (structure-only) or `cealign` (combinatorial extension).
    """
    return _align_tuple(get_client().align(mobile, target))


@mcp.tool()
def super_align(mobile: str, target: str) -> AlignResult:
    """Structure-only superposition via cmd.super. Better than `align` for low-identity pairs."""
    return _align_tuple(get_client().super(mobile, target))


@mcp.tool()
def cealign(target: str, mobile: str) -> AlignResult:
    """CE (Combinatorial Extension) alignment via cmd.cealign. Strongest for divergent structures.

    Note the argument order: target first, then mobile (matches PyMOL's signature).
    Returns RMSD and aligned-length; CE does not report refinement cycles.
    """
    d = get_client().cealign(target, mobile)
    return AlignResult(
        rmsd=float(d["RMSD"]),
        n_atoms=int(d["alignment_length"]),
        n_cycles=0,
        rmsd_initial=float(d["RMSD"]),
        n_atoms_initial=int(d["alignment_length"]),
    )


def _parse_pdb_atom_line(line: str) -> AtomCoord | None:
    """Parse one ATOM/HETATM line from a PDB string into an AtomCoord."""
    if not (line.startswith("ATOM") or line.startswith("HETATM")):
        return None
    try:
        return AtomCoord(
            name=line[12:16].strip(),
            resn=line[17:20].strip(),
            chain=line[21:22].strip(),
            resi=line[22:26].strip(),
            x=float(line[30:38]),
            y=float(line[38:46]),
            z=float(line[46:54]),
            element=line[76:78].strip() or line[12:14].strip(),
        )
    except (ValueError, IndexError):
        return None


@mcp.tool()
def get_atom_coords(selection: str) -> list[AtomCoord]:
    """Return atom records (x/y/z + chain/resi/resn/name/element) for a selection.

    Backed by `cmd.get_pdbstr` and PDB-line parsing — XML-RPC-safe, no numpy
    on the wire. For very large selections, consider narrowing first
    (e.g. `name CA and chain A`) to keep returns tractable.
    """
    pdb = get_client().get_pdbstr(selection)
    atoms = [a for a in (_parse_pdb_atom_line(ln) for ln in pdb.splitlines()) if a]
    return atoms


@mcp.tool()
def run_pml(script: str) -> str:
    """Escape hatch: run an arbitrary PyMOL command (PML) script.

    Use a typed tool when one fits — they return structured data. Use `run_pml`
    for the long tail (settings, ray-tracing tweaks, complex iterate, scripts).
    Output goes to PyMOL's console; this tool returns a brief confirmation,
    not captured stdout. Call `list_objects` or `get_atom_coords` afterward
    to inspect effects.
    """
    c = get_client()
    c.do(script)
    line_count = len([ln for ln in script.splitlines() if ln.strip()])
    return f"executed {line_count} PML line(s)"
