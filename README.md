# clamol

MCP server that exposes PyMOL to Claude Code via PyMOL's built-in XML-RPC bridge. No PyMOL plugin needed — drives any PyMOL build (open-source, Schrödinger, conda) through stock `pymol -R`.

## Install (one-time, per machine)

```bash
brew install pymol
git clone https://github.com/julesberman/clamol && cd clamol
bash install.sh
```

`install.sh` is interactive and explains each step. It (1) creates a venv with clamol installed editable, (2) symlinks the `pymol` skill into `~/.claude/skills/`, and (3) registers clamol as a **user-scope** MCP server in Claude Code — so every `claude` session in every directory has the tools, no per-project `.mcp.json` needed.

Pass `-y` for non-interactive. Re-runs are idempotent.

## Each session

```bash
clamol-launch-pymol &       # GUI + RPC on :9123 (add --headless for batch)
claude                      # in any directory — skill + tools auto-load
```

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

## Sharing with a single project (team)

If you'd rather commit the MCP config alongside a project so teammates pick it up via `git pull`, copy `.mcp.json.example` into the project root instead of using `install.sh`'s user-scope registration. The user-scope path is recommended for personal use; the per-project `.mcp.json` is best for sharing within a team repo.

## License

MIT.
