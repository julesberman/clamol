# Canonical clamol workflows

Worked end-to-end recipes. Tool names are MCP names (`fetch_pdb`, `align`, …).

---

## 1. Compare a folding prediction vs ground truth

Goal: load AlphaFold (or similar) prediction, superpose onto a crystal structure, color by per-atom alignment quality, render.

```python
# 1. Load both structures
load_structure(path="/Users/me/predictions/uniprot_X_af2.pdb", object_name="pred")
fetch_pdb(pdb_id="4hhb", object_name="truth")

# 2. For comparing same protein with high seq identity, super_align is the
#    cleanest. For low-identity / distant fold, prefer cealign.
result = super_align(mobile="pred", target="truth")
# AlignResult{rmsd=1.42, n_atoms=141, ...}

# 3. Style and color
hide(representation="everything")
show(representation="cartoon", selection="pred or truth")
color(color="cyan", selection="pred")
color(color="salmon", selection="truth")

# 4. Render at presentation size, ray-traced
render_png(width=1600, height=1200, ray=True)
```

Report to the user: the RMSD, the number of aligned atoms, and the inline rendering.

### Variant: color the prediction by deviation

After `super_align`, the per-atom distance to the target is in PyMOL's `b` (B-factor) column for the aligned set. To re-color by RMSD:

```python
run_pml(script="spectrum b, blue_white_red, pred")
render_png(width=1600, height=1200, ray=True)
```

---

## 2. Identify a binding-site shell

Goal: find protein residues within N Å of a ligand and render with cartoon + sticks.

```python
fetch_pdb(pdb_id="1stp")             # streptavidin–biotin
hide(representation="everything")
show(representation="cartoon", selection="polymer.protein")

# Show the ligand as sticks
show(representation="sticks", selection="resn BTN")
color(color="yellow", selection="resn BTN and element C")

# Residues within 5 Å — whole residues, not just touching atoms
select(name="shell", selection="byres (resn BTN around 5) and polymer.protein")
show(representation="sticks", selection="shell")
color(color="magenta", selection="shell and element C")

# Zoom and render
run_pml(script="orient shell")
render_png(width=1400, height=1000, ray=True)
```

To list the shell residues for downstream analysis:

```python
get_atom_coords(selection="shell and name CA")
# -> [{chain, resi, resn, ...}, ...]
```

---

## 3. Per-residue Cα analysis

Goal: pull Cα coordinates for downstream local analysis (PCA, distance matrix, plotting).

```python
fetch_pdb(pdb_id="1ubq")
coords = get_atom_coords(selection="1ubq and chain A and name CA")
# -> list of AtomCoord, one per residue
```

The model can now reason over coords directly (compute distances, find the most flexible loops, etc.) without round-tripping more tool calls.

---

## 4. Side-by-side multi-state alignment

Goal: load two predictions and the ground truth, align both onto truth, render all three.

```python
fetch_pdb(pdb_id="1ubq", object_name="truth")
load_structure(path="/tmp/af2_model1.pdb", object_name="m1")
load_structure(path="/tmp/af2_model2.pdb", object_name="m2")

r1 = super_align(mobile="m1", target="truth")
r2 = super_align(mobile="m2", target="truth")

hide(representation="everything")
show(representation="cartoon", selection="truth or m1 or m2")
color(color="grey80", selection="truth")
color(color="cyan",   selection="m1")
color(color="salmon", selection="m2")

render_png(width=1800, height=1200, ray=True)
# Report both RMSDs: m1 -> {r1.rmsd}, m2 -> {r2.rmsd}
```

---

## 5. Save the session

PyMOL session files (`.pse`) preserve everything — useful for the user to keep working interactively.

```python
run_pml(script="save /Users/me/Desktop/alignment.pse")
```

---

## Tips that apply to all workflows

- **Render small (`ray=False`) while iterating, big and ray-traced once at the end.** Ray-tracing a 1920×1080 image takes seconds; OpenGL snapshots are instant.
- **Hide before you show.** Start most workflows with `hide(representation="everything")` to clear PyMOL's defaults so subsequent `show` calls produce a predictable view.
- **`orient` before rendering** — auto-frames the camera on a selection (or all).
- **Confirm with `list_objects` / `render_png`** when you suspect state drift.
