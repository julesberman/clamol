"""Thin wrapper around PyMOL's built-in XML-RPC server (`pymol -R`, port 9123).

PyMOL's RPC server exposes every `cmd.*` method via `register_instance(cmd)`,
so most calls work as `client.method_name(...)`. Use plain types — the wire
format is XML-RPC, which doesn't speak numpy. For coord-style data, prefer
`cmd.get_pdbstr()` (string) over `cmd.get_coords()` (numpy array).
"""

from __future__ import annotations

import time
import xmlrpc.client

PYMOL_RPC_URL = "http://localhost:9123"


class PyMOLConnectionError(RuntimeError):
    pass


class PyMOLClient:
    def __init__(self, url: str = PYMOL_RPC_URL) -> None:
        self.url = url
        self._proxy = xmlrpc.client.ServerProxy(url, allow_none=True)

    def connect(self, timeout: float = 5.0) -> None:
        deadline = time.monotonic() + timeout
        last_err: Exception | None = None
        while time.monotonic() < deadline:
            try:
                self._proxy.get_version()
                return
            except Exception as e:  # ConnectionRefused, ProtocolError, etc.
                last_err = e
                time.sleep(0.2)
        raise PyMOLConnectionError(
            f"Cannot reach PyMOL XML-RPC at {self.url}. "
            "Is PyMOL running with `pymol -R`? Try `clamol-launch-pymol`. "
            f"Last error: {last_err!r}"
        )

    def __getattr__(self, name: str):
        return getattr(self._proxy, name)


_client: PyMOLClient | None = None


def get_client() -> PyMOLClient:
    global _client
    if _client is None:
        c = PyMOLClient()
        c.connect()
        _client = c
    return _client
