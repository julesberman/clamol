# clamol tool reference

Every tool surfaced by the `clamol` MCP server, with a representative call and the structured return the model receives.

All examples assume PyMOL is running with `clamol-launch-pymol &` and `mcp__clamol__list_objects` returns without error.

---

## Loading structures

### `fetch_pdb(pdb_id, object_name?)`

Fetch from RCSB by 4-letter code. If `object_name` is omitted, the lowercase PDB id is used.

```python
fetch_pdb(pdb_id="1ubq")
# -> {"name": "1ubq", "n_atoms": 660, "chains": ["A"]}

fetch_pdb(pdb_id="4hhb", object_name="hb")
# -> {"name": "hb", "n_atoms": 4779, "chains": ["A", "B", "C", "D"]}
```

### `load_structure(path, object_name?)`

Load a local file (PDB, CIF, mmCIF, SDF, etc.).

```python
load_structure(path="/Users/me/predictions/af2_model_1.pdb", object_name="pred")
# -> {"name": "pred", "n_atoms": 1234, "chains": ["A"]}
```

---

## Inspecting state

### `list_objects()`

```python
list_objects()
# -> ["1ubq", "hb", "pred"]
```

### `get_chains(object)`

```python
get_chains(object="4hhb")
# -> ["A", "B", "C", "D"]
```

### `get_atom_coords(selection)`

Returns one `AtomCoord` record per atom. Backed by `cmd.get_pdbstr` + parsing — XML-RPC-safe but **narrow your selection** to keep returns tractable.

```python
get_atom_coords(selection="1ubq and name CA and resi 1-3")
# -> [
#   {"chain":"A","resi":"1","resn":"MET","name":"CA","element":"C","x":26.266,"y":25.413,"z":2.842},
#   {"chain":"A","resi":"2","resn":"GLN","name":"CA","element":"C","x":26.85,"y":29.021,"z":3.898},
#   {"chain":"A","resi":"3","resn":"ILE","name":"CA","element":"C","x":26.235,"y":30.058,"z":7.497}
# ]
```

---

## Selections and representation

### `select(name, selection)`

Create a named selection. The selection expression follows PyMOL syntax — see [selection_syntax.md](selection_syntax.md).

```python
select(name="active_site", selection="byres (resn HEM around 5)")
# -> {"name": "active_site", "n_atoms": 64}
```

### `show(representation, selection?)` / `hide(representation, selection?)`

Representations: `cartoon`, `sticks`, `spheres`, `surface`, `mesh`, `ribbon`, `lines`, `dots`, `nb_spheres`, `everything` (special — clears all when hidden).

```python
show(representation="cartoon", selection="polymer.protein")
hide(representation="everything", selection="resn HOH")
```

### `color(color, selection?)`

Named colors (`red`, `cyan`, `forest`, `salmon`, ...), hex (`0xff8800`), or `spectrum` for rainbow.

```python
color(color="spectrum", selection="ss h")     # rainbow on helices
color(color="grey50", selection="not 1ubq")
```

---

## Alignment

All three alignment tools return the same `AlignResult` shape `{rmsd, n_atoms, n_cycles, rmsd_initial, n_atoms_initial}`. They differ in algorithm:

| Tool | Algorithm | Best for |
| --- | --- | --- |
| `align` | Sequence then structure | ≥30% sequence identity |
| `super_align` | Structure only (rigid body) | Low-identity pairs, same fold |
| `cealign` | Combinatorial extension | Distant homologs, different folds |

### `align(mobile, target)`

```python
align(mobile="pred", target="1ubq")
# -> {"rmsd": 1.45, "n_atoms": 70, "n_cycles": 5, "rmsd_initial": 1.92, "n_atoms_initial": 76}
```

### `super_align(mobile, target)`

Same call shape as `align`. Lower RMSD typical for divergent pairs.

### `cealign(target, mobile)` ⚠️

**Argument order is swapped** vs. `align`/`super_align` — `target` first, then `mobile`. This matches PyMOL's own `cmd.cealign(target, mobile)` signature.

```python
cealign(target="1ubq", mobile="pred")
# -> {"rmsd": 1.42, "n_atoms": 68, ...}
```

`n_cycles`, `rmsd_initial`, `n_atoms_initial` are reported as the same value as `rmsd`/`n_atoms` because CE doesn't do outlier-rejection cycles.

---

## Rendering

### `render_png(width=1200, height=900, ray=True)`

Renders the current view and returns the PNG inline — **you see the image**. Use `ray=False` (OpenGL snapshot) while iterating on the view; use `ray=True` for the final image.

```python
render_png(width=1600, height=1200, ray=True)
# -> Image(image/png, ~200KB base64)
```

Typical render times on a Mac M-series:
- `ray=False`: <100 ms
- `ray=True, 1200x900`: 1-3 s
- `ray=True, 1920x1080`: 3-8 s

---

## Escape hatch

### `run_pml(script)`

Run arbitrary PyMOL command-language script. Use sparingly — typed tools return structured data; `run_pml` returns only a line-count confirmation (PyMOL's stdout is not captured over XML-RPC).

```python
run_pml(script="""
bg_color white
set ray_opaque_background, 0
set cartoon_transparency, 0.4, 1ubq
orient hb_A
""")
# -> "executed 4 PML line(s)"
```

When you'd reach for `run_pml`:

- Toggle settings (`set cartoon_fancy_helices, 1`)
- Camera (`orient`, `zoom`, `turn x, 90`)
- Mutagenesis wizard
- Loading PyMOL scripts via `@/path/to/script.pml`
- Anything else not yet wrapped as a typed tool

After `run_pml`, call `list_objects` / `get_atom_coords` / `render_png` to inspect effects.
