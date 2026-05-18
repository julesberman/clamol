# PyMOL selection syntax cheatsheet

Selections are space-separated keywords joined by boolean operators. Used as the `selection=` arg of nearly every clamol tool.

## Atom-property keywords

| Keyword | Matches |
| --- | --- |
| `chain A` | atoms in chain A |
| `resi 10` | residue index 10 |
| `resi 10-30` | residues 10 through 30 (inclusive) |
| `resi 10+15+20` | residues 10, 15, and 20 |
| `resn ALA` | all alanine residues |
| `resn HEM+NAD` | heme or NAD ligands |
| `name CA` | only Cα atoms |
| `name CA+C+N+O` | backbone heavy atoms |
| `element C` | all carbons |
| `b > 30` | b-factor greater than 30 |
| `q < 1` | partial occupancy |
| `ss h` / `ss s` / `ss l` | α-helix / β-strand / loop |

## Predefined classes

| Keyword | Meaning |
| --- | --- |
| `polymer` | protein + nucleic acid |
| `polymer.protein` | protein only |
| `polymer.nucleic` | DNA / RNA |
| `solvent` | waters |
| `organic` | small molecules (ligands), excluding ions |
| `inorganic` | ions, cofactors |
| `hetatm` | non-standard residues (HETATM lines) |
| `hydro` | hydrogen atoms |
| `backbone` | N, CA, C, O |
| `sidechain` | everything in a residue except backbone |

## Boolean operators

`and`, `or`, `not`, parentheses.

```
chain A and resi 1-50 and name CA
not (resn HOH or resn NAG)
polymer.protein and (b > 50)
```

## Distance / proximity

| Pattern | Meaning |
| --- | --- |
| `(X around 5)` | atoms within 5 Å of any atom in X |
| `byres (X around 5)` | whole residues with any atom within 5 Å of X |
| `X within 5 of Y` | atoms in X within 5 Å of Y |
| `X gap 2` | X plus all atoms within 2 Å of X's surface |

```python
# residues forming a 5 Å shell around the ligand:
select(name="pocket", selection="byres (resn LIG around 5) and polymer.protein")

# beta strand contacts:
select(name="strand_contacts", selection="byres (ss s around 4) and not ss s")
```

## Object scoping

Prefix a selection with `objname and ...` to scope to one object. Without scoping, selections apply to **all** loaded objects.

```python
select(name="ub_helix", selection="1ubq and resi 23-34")
```

## Wildcards

| Pattern | Meaning |
| --- | --- |
| `resn ALA+GLY+SER` | enumerate |
| `name C*` | starts with C (Cα, Cβ, Cγ, …) |
| `*` | all (rarely useful — use `all`) |

## Useful idioms

```
# Just CA atoms of a chain — perfect for downstream coord analysis:
chain A and name CA and polymer.protein

# Active site within 6 Å of a covalent ligand, residues only:
byres (resn LIG around 6) and polymer.protein

# Ignore alternate conformations (keep altloc A only):
not alt B+C+D

# Drop disorder, drop waters and ions:
polymer.protein and not hydro and not alt B+C+D
```

## Operator precedence

`not` > `and` > `or`. Parenthesize liberally when in doubt.

```
# WRONG: parses as (chain A and resi 10) or chain B
chain A and resi 10 or chain B

# Right:
chain A and (resi 10 or chain B)
```

## Reference

Full grammar: https://pymolwiki.org/index.php/Selection_Algebra
