"""MCP tools — registered on the FastMCP instance defined in clamol.server.

Each tool is a thin shim: validate inputs (Pydantic via type hints), call PyMOL
via the XML-RPC client, return a typed Pydantic model. Tools that need PyMOL
kwargs route through `cmd.do(...)` command strings (XML-RPC doesn't speak
Python kwargs).
"""

from __future__ import annotations

# Tools land in subsequent commits; this module exists so server.py can
# import it as the registration trigger.
