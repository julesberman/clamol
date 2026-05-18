# Gotchas

Surprises and their fixes when driving PyMOL through the `clamol` MCP server.

---

## XML-RPC doesn't speak Python kwargs

`xmlrpc.client.ServerProxy.method(**kw)` raises `TypeError`. Inside clamol the tools route kwarg-heavy commands (e.g. `fetch`, `align` with options, `png`) through `cmd.do("fetch 1ubq, ubq, async=0")` — a string command. If you reach for `run_pml`, follow the same pattern: comma-separated args, `key=value` syntax inside the PML string.

## `cealign` argument order is reversed

`align(mobile, target)` and `super_align(mobile, target)` take **mobile first**.
`cealign(target, mobile)` takes **target first** — matching PyMOL's own `cmd.cealign` signature. Crossing them silently produces a wrong-direction alignment.

## Numpy arrays don't survive the wire

PyMOL's `cmd.get_coords` returns a numpy array. XML-RPC can't serialize it and you'll get a `Fault` or empty result. `get_atom_coords` works around this by routing through `cmd.get_pdbstr` (a plain string) and parsing PDB ATOM lines locally into typed records. For huge selections, narrow first.

## `render_png` returns the bytes inline

The PNG is base64-encoded into the MCP `ImageContent` block — the model literally sees the image. The temp file is left on disk under `$TMPDIR`; PyMOL is on the same host as the MCP server, so this just works locally. (If you ever run PyMOL on a different host, the file won't be reachable — fall back to `cmd.png` to disk and copy manually.)

## `run_pml` doesn't capture PyMOL's stdout

`cmd.do(...)` over XML-RPC executes the script but discards anything PyMOL printed to its console. `run_pml` returns only a line-count confirmation. To inspect side-effects, call other tools: `list_objects`, `get_atom_coords`, `render_png`.

## Headless PyMOL exits without `-K`

`pymol -c -R` starts the RPC server then *exits* because there's no input on stdin and no GUI to keep it alive. `clamol-launch-pymol --headless` uses `pymol -cqKR` — the `-K` flag keeps it alive. If you start PyMOL yourself, remember the `K`.

## Port 9123 is hard-coded

PyMOL's `-R` always binds to 9123. If something else holds the port (a stale pymol, another bridge), you'll get `ConnectionRefusedError` 60s into a CC session. Fix: `lsof -i :9123` and kill the squatter, then relaunch.

## `ray=True` is slow

Ray-traced renders take seconds. For an iterative workflow (try a view, render, adjust, render) use `ray=False` until you're happy, then `ray=True` for the final image.

## Selections without object scope hit everything

`select(name="foo", selection="resi 10")` selects residue 10 in *every* loaded object. Scope with `objname and ...`:

```
select(name="foo", selection="1ubq and resi 10")
```

## `show("everything")` is destructive — call `hide("everything")` first

Most workflows start with `hide(representation="everything")` to drop PyMOL's defaults; then call `show(...)` for what you want. Otherwise PyMOL's defaults (lines on everything) overlay your cartoon and the render looks busy.

## PyMOL state is sticky between requests

Each MCP tool call goes to the same long-running PyMOL process. Objects, selections, settings, and camera persist across tool calls — and across separate CC sessions until PyMOL itself is restarted. If a session looks weird, `run_pml(script="delete all; reinitialize")` resets to defaults.

## Schrödinger PyMOL vs open-source — same RPC

`-R` works identically on both builds. No code change needed; just whichever `pymol` is on `$PATH`.

---

## Reference

- PyMOL XML-RPC server: https://pymolwiki.org/index.php/RPC
- PyMOL Python API: https://pymol.org/dokuwiki/doku.php?id=api
- Selection algebra: https://pymolwiki.org/index.php/Selection_Algebra
