"""FastMCP server entry points.

`main()` runs the MCP server over stdio (Claude Code's transport).
`launch_pymol_cli()` is the `clamol-launch-pymol` console script — a thin
wrapper that execs `pymol` with the right flags so the user doesn't have to
remember them.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("clamol")


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()


def launch_pymol_cli() -> None:
    """Console script: exec `pymol` with the XML-RPC server enabled.

    Default is GUI mode (so the user can watch alignments happen).
    Use `--headless` for batch/automation. Either way, `-K` keeps PyMOL
    alive in headless mode so the RPC server doesn't quit immediately.
    """
    parser = argparse.ArgumentParser(
        prog="clamol-launch-pymol",
        description="Launch PyMOL with the XML-RPC server on localhost:9123.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="run without GUI (still keeps RPC server alive)",
    )
    args = parser.parse_args()

    pymol = shutil.which("pymol")
    if pymol is None:
        print(
            "error: pymol not on PATH. Install via `brew install pymol` "
            "or `conda install -c conda-forge pymol-open-source`.",
            file=sys.stderr,
        )
        sys.exit(1)

    flags = ["-cqKR"] if args.headless else ["-qR"]
    print(f"launching: {pymol} {' '.join(flags)}", file=sys.stderr)
    print("PyMOL XML-RPC server will listen on http://localhost:9123", file=sys.stderr)
    os.execvp(pymol, [pymol, *flags])


# Register tools by importing the module — decorators in clamol.tools attach
# to `mcp`. Must come AFTER `mcp` is defined.
from clamol import tools  # noqa: E402,F401
