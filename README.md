# clamol

MCP server that exposes PyMOL to Claude Code via PyMOL's built-in XML-RPC bridge. No PyMOL plugin needed — drives any PyMOL build (open-source, Schrödinger, conda) through stock `pymol -R`.

## Install (for coworkers)

```bash
brew install uv pymol
echo '{"mcpServers":{"clamol":{"command":"uvx","args":["--from","git+https://github.com/julesberman/clamol","clamol"]}}}' > .mcp.json
```

Each session, launch PyMOL with the RPC server on:

```bash
clamol-launch-pymol &
```

Then run `claude` in that directory. Claude Code picks up the MCP server, `uvx` fetches `clamol` from GitHub on first launch, caches it after.

## Tools

Typed MCP tools — model receives structured returns (RMSDs, atom coords, inline PNG images), not stringified blobs.

| Tool | Purpose |
| --- | --- |
| `load_structure`, `fetch_pdb` | load a local file or fetch from RCSB |
| `align`, `super_align`, `cealign` | structural superposition (returns RMSD + atom count) |
| `select`, `show`, `hide`, `color` | selections and representation |
| `list_objects`, `get_chains`, `get_atom_coords` | inspect loaded structures |
| `render_png` | render to PNG and return inline so Claude sees the image |
| `run_pml` | escape hatch — run arbitrary PyMOL script |

## Skill

Install the bundled `pymol` Claude skill so Claude knows when and how to drive the MCP tools:

```bash
bash skills/pymol/install.sh
```

This symlinks `skills/pymol/` into `~/.claude/skills/pymol/`, so edits in the repo are live for everyone who `git pull`s.

## Dev

```bash
git clone https://github.com/julesberman/clamol
cd clamol
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Point `.mcp.json` at `.venv/bin/clamol` for fast iteration. Test individual tools with `npx @modelcontextprotocol/inspector .venv/bin/clamol`.

## License

MIT.
