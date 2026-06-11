"""Shared pytest fixtures.

Two test layers:

* **Unit** — import ``uefn_listener`` on a host with no editor. We inject a
  stub ``unreal`` module and set ``UEFN_LISTENER_NO_AUTOSTART`` so importing the
  module does not bind a socket. Pure logic (log selection, filtering) is tested
  via dependency-injected arguments.
* **Live** — talk to a real UEFN listener over HTTP. These tests use the
  ``live_listener`` fixture, which skips the test when no listener is reachable.
"""

import json
import os
import sys
import types
import urllib.error
import urllib.request

import pytest

# --- Make uefn_listener importable without the UEFN editor -------------------
# Must happen before any test imports uefn_listener.
os.environ.setdefault("UEFN_LISTENER_NO_AUTOSTART", "1")
if "unreal" not in sys.modules:
    sys.modules["unreal"] = types.ModuleType("unreal")

# test_feasibility.py is a standalone in-editor probe script (it runs on import
# and calls unreal.* APIs), not a pytest module. Don't collect it.
collect_ignore = ["test_feasibility.py"]

_PORT_RANGE = range(8765, 8771)


def _discover_listener_port():
    """Return the first port in 8765-8770 with a healthy listener, else None."""
    for port in _PORT_RANGE:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}", method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if json.loads(resp.read().decode()).get("status") == "ok":
                    return port
        except Exception:
            continue
    return None


class ListenerClient:
    """Minimal HTTP client for the UEFN listener command protocol."""

    def __init__(self, port: int):
        self.port = port

    def command(self, command: str, params: dict | None = None, timeout: float = 30.0) -> dict:
        payload = json.dumps({"command": command, "params": params or {}}).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())


@pytest.fixture
def listener_module():
    """The imported ``uefn_listener`` module (handlers registered, no server)."""
    import uefn_listener

    return uefn_listener


@pytest.fixture(scope="session")
def live_listener():
    """A client for a running UEFN listener, or skip if none is reachable."""
    port = _discover_listener_port()
    if port is None:
        pytest.skip("No UEFN listener reachable on ports 8765-8770")
    return ListenerClient(port)
