---
name: pymol
description: Use when the user asks to manipulate molecular structures, align/superpose proteins, fetch from PDB, render structural images, or otherwise drive PyMOL. Activates the `clamol` MCP server's tools (`mcp__clamol__*`). Requires `pymol -R` running on localhost:9123.
---

# pymol skill

Drive PyMOL through the `clamol` MCP server. Tools are typed and return structured data — prefer them over building PML strings.

## Preflight (first call each session)

Call `mcp__clamol__list_objects` before anything else. If it errors, PyMOL isn't running with the RPC server. Tell the user:

> Start PyMOL with `clamol-launch-pymol &` (or `clamol-launch-pymol --headless &` if they don't need the GUI).

## Quick tool reference

| Tool | Most common shape | Returns |
| --- | --- | --- |
| `fetch_pdb` | `pdb_id="1ubq"` | `ObjectInfo{name, n_atoms, chains}` |
| `load_structure` | `path="/x.pdb"` | `ObjectInfo` |
| `list_objects` | — | `list[str]` |
| `get_chains` | `object="1ubq"` | `list[str]` |
| `select` | `name="binding", selection="byres (lig around 5)"` | `SelectionInfo{name, n_atoms}` |
| `show`/`hide` | `representation="cartoon", selection="all"` | str |
| `color` | `color="spectrum", selection="ss h"` | str |
| `align` | `mobile="a", target="b"` | `AlignResult{rmsd, n_atoms, n_cycles, ...}` — best ≥30% seq identity |
| `super_align` | `mobile="a", target="b"` | `AlignResult` — best for divergent pairs |
| `cealign` | `target="a", mobile="b"` (**swapped!**) | `AlignResult` — CE; strongest for distant homologs |
| `get_atom_coords` | `selection="1ubq and name CA"` | `list[AtomCoord{chain, resi, resn, name, element, x, y, z}]` |
| `render_png` | `width=1200, height=900, ray=True` | inline image (you see it) |
| `run_pml` | `script="bg_color white\nset cartoon_transparency, 0.3"` | str (no captured output) |

Full per-tool reference with examples: [references/tools.md](references/tools.md).

## Selection syntax in one paragraph

PyMOL selections use space-separated keywords joined by `and`/`or`/`not`. Common ones: `chain A`, `resi 10-20`, `resn ALA`, `name CA`, `byres (X around 5)` (residues with any atom within 5Å of `X`), `polymer.protein`, `not resn HOH`. Combine: `chain A and resi 23-34 and name CA`. Full cheatsheet: [references/selection_syntax.md](references/selection_syntax.md).

## Canonical workflows

Worked end-to-end recipes in [references/workflows.md](references/workflows.md):

1. **Compare prediction vs ground truth** — fetch + super_align + color-by-RMSD + render
2. **Find a binding site** — load complex + select `byres (ligand around N)` + render
3. **Per-residue analysis** — get_atom_coords on `name CA` + analyze locally
4. **Multi-state model** — load + iterate states + render each

## Gotchas

Common surprises and their fixes in [references/gotchas.md](references/gotchas.md). Highlights:

- XML-RPC doesn't speak Python kwargs — tools route kwargs through `cmd.do` strings internally.
- `cealign(target, mobile)` reverses arg order from `align`/`super_align` — match PyMOL's docs.
- `get_atom_coords` is `cmd.get_pdbstr` + parsing (no numpy on the wire). Narrow selections to keep returns small.
- `render_png` with `ray=True` is slow (~seconds per render). Use `ray=False` while iterating.
- `run_pml` doesn't return PyMOL's stdout. Use `list_objects` / `get_atom_coords` to confirm effects.

## Escape hatch

For anything not covered by a typed tool, use `run_pml`. Prefer typed tools when available — they return data the model can reason over.
