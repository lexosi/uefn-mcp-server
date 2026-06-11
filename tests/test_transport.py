"""Unit tests for the MCP server HTTP transport (mocked, no editor required)."""

import json

import pytest


@pytest.fixture
def server(monkeypatch):
    import mcp_server as m

    m._discovered_port = None  # reset module-level cache between tests
    return m


class _FakeResp:
    def __init__(self, body: dict):
        self._b = json.dumps(body).encode()

    def read(self) -> bytes:
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_discover_port_returns_first_healthy(server, monkeypatch):
    probed = []

    def fake_ping(port):
        probed.append(port)
        return port == 8767

    monkeypatch.setattr(server, "_ping_port", fake_ping)
    assert server._discover_port() == 8767
    assert probed[0] == 8765  # scans from the default port up


def test_discover_port_raises_when_none(server, monkeypatch):
    monkeypatch.setattr(server, "_ping_port", lambda port: False)
    with pytest.raises(ConnectionError):
        server._discover_port()


def test_send_command_returns_result(server, monkeypatch):
    monkeypatch.setattr(server, "_discover_port", lambda: 8765)
    monkeypatch.setattr(
        server.urllib.request, "urlopen",
        lambda req, timeout=0: _FakeResp({"success": True, "result": {"pong": 1}}),
    )
    assert server._send_command("ping") == {"pong": 1}


def test_send_command_raises_on_uefn_error(server, monkeypatch):
    monkeypatch.setattr(server, "_discover_port", lambda: 8765)
    monkeypatch.setattr(
        server.urllib.request, "urlopen",
        lambda req, timeout=0: _FakeResp({"success": False, "error": "boom"}),
    )
    with pytest.raises(RuntimeError, match="boom"):
        server._send_command("ping")
