# clamol

MCP server that exposes PyMOL to Claude Code via PyMOL's built-in XML-RPC bridge. No PyMOL plugin needed — drives any PyMOL build (open-source, Schrödinger, conda) through stock `pymol -R`.

---

## Install

### Step 0 — prerequisites

Check what you already have. **Skip whichever rows pass.**

| Need | Check it | Install if missing |
| --- | --- | --- |
| **Homebrew** (Mac) | `which brew` | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` |
| **git** | `which git` | `brew install git` (macOS ships one; usually fine) |
| **Python 3.11+** | `python3 --version` | `brew install python` |
| **PyMOL** | `which pymol` | `brew install pymol` |
| **Claude Code** | `which claude` | See [Claude Code install docs](https://docs.claude.com/en/docs/claude-code) |

> **TL;DR for a clean Mac:**
> ```bash
> brew install pymol git python
> # then install Claude Code per the link above
> ```

### Step 1 — clone and run the installer

```bash
git clone https://github.com/julesberman/clamol
cd clamol
bash install.sh
```

`install.sh` is interactive — it explains each step and asks before doing anything. Three things happen:

1. Creates `.venv/`, installs clamol editable, and symlinks the `clamol` / `clamol-launch-pymol` console scripts into `~/.local/bin/` so they're on `$PATH`.
2. Copies the `pymol` skill into `~/.claude/skills/pymol/`. **Optional** — the MCP tools work without it; the skill just teaches Claude when to use them. Re-run `install.sh` after `git pull` to refresh.
3. Registers clamol as a **user-scope** MCP server in Claude Code via `claude mcp add -s user`.

> If `~/.local/bin` isn't on your `$PATH`, the installer prints a one-line snippet to add to your shell rc.

After this, every `claude` session in every directory has the `mcp__clamol__*` tools and the pymol skill loaded automatically — no per-project `.mcp.json` needed.

Pass `-y` for unattended install. Re-runs are idempotent (safe to repeat after `git pull`).

### Step 2 — verify

```bash
claude mcp list
# expect: clamol: /path/to/.venv/bin/clamol  - ✓ Connected
```

If you see `✓ Connected`, you're done. (Claude Code can talk to clamol; PyMOL doesn't need to be running yet — the tools will start it when first called, or you can pre-launch it as below.)

---

## Each session

```bash
clamol-launch-pymol &       # GUI + RPC on :9123 (add --headless for batch)
claude                      # in any directory — skill + tools auto-load
```

Ask Claude something like:

> *"fetch 1ubq and 1ubi, super-align them, color cyan vs salmon, render a 1200×900 image"*

Claude will pick up the `pymol` skill, call `fetch_pdb` / `super_align` / `color` / `render_png` in order, and show you the inline PNG of the aligned structures.

---

## Tools

Typed MCP tools — the model receives structured returns (RMSDs, atom coords, inline PNG images), not stringified blobs.

| Tool | Purpose |
| --- | --- |
| `load_structure`, `fetch_pdb` | load a local file or fetch from RCSB |
| `align`, `super_align`, `cealign` | structural superposition (returns RMSD + atom count) |
| `select`, `show`, `hide`, `color` | selections and representation |
| `list_objects`, `get_chains`, `get_atom_coords` | inspect loaded structures |
| `render_png` | render to PNG and return inline so Claude sees the image |
| `run_pml` | escape hatch — run arbitrary PyMOL script |

Full per-tool reference: [`skills/pymol/references/tools.md`](skills/pymol/references/tools.md).
Selection-syntax cheatsheet: [`skills/pymol/references/selection_syntax.md`](skills/pymol/references/selection_syntax.md).
Canonical workflows: [`skills/pymol/references/workflows.md`](skills/pymol/references/workflows.md).
Gotchas: [`skills/pymol/references/gotchas.md`](skills/pymol/references/gotchas.md).

---

## Updating

```bash
cd clamol && git pull
```

The editable install means new code is picked up on the next `claude` session. No re-install needed. The skill symlink also picks up doc edits automatically.

## Uninstalling

```bash
claude mcp remove clamol -s user
rm -rf ~/.claude/skills/pymol
rm ~/.local/bin/clamol ~/.local/bin/clamol-launch-pymol
rm -rf /path/to/clamol  # optional — delete the clone
```

## Sharing with a single project (team)

The default install above puts clamol in *user* scope — available everywhere on your machine. If instead you want to commit MCP config alongside a specific project so teammates pick it up via `git pull`, copy `.mcp.json.example` into the project root.

## License

MIT.
