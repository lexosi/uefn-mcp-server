"""Live integration tests — require a running UEFN listener.

Run with the listener up:  pytest -m live
These auto-skip when no listener is reachable (see the ``live_listener`` fixture).
"""

import os

import pytest

pytestmark = pytest.mark.live


def test_ping_reports_commands(live_listener):
    res = live_listener.command("ping")
    assert res["success"] is True
    assert "take_screenshot" in res["result"]["commands"]


def test_get_editor_log_targets_the_real_output_log(live_listener):
    res = live_listener.command("get_editor_log", {"last_n": 50})
    assert res["success"] is True
    log_file = res["result"].get("file", "")
    assert "UnrealRevisionControl" not in log_file
    assert "UnrealEditorFortnite" in log_file


@pytest.mark.canary
def test_canary_editor_log_is_not_auth_spam(live_listener):
    """Log equivalent of a black frame: the tool can 'succeed' yet return the
    revision-control auth spam. Assert the output is not dominated by it."""
    res = live_listener.command("get_editor_log", {"last_n": 100})
    lines = res["result"]["lines"]
    if not lines:
        pytest.skip("editor log empty")
    auth = sum(1 for l in lines if "lore_transport::auth" in l)
    assert auth < len(lines) * 0.5


@pytest.mark.canary
def test_canary_unknown_command_is_rejected(live_listener):
    """A harness that 'passes everything' would miss this: a bogus command must
    fail loudly, not silently succeed."""
    res = live_listener.command("definitely_not_a_real_command")
    assert res["success"] is False


def test_screenshot_writes_a_valid_png(live_listener):
    res = live_listener.command("take_screenshot", {"width": 320, "height": 180})
    assert res["success"] is True
    path = res["result"]["path"]
    assert os.path.exists(path)
    assert res["result"]["width"] == 320 and res["result"]["height"] == 180
    with open(path, "rb") as f:
        assert f.read(8) == b"\x89PNG\r\n\x1a\n"  # PNG magic


@pytest.mark.canary
def test_canary_screenshot_is_not_blank(live_listener):
    """Black-frame canary: a capture can 'succeed' yet be uniformly black/blank
    if nothing rendered. Assert the image has real content."""
    Image = pytest.importorskip("PIL.Image")
    res = live_listener.command("take_screenshot", {"width": 320, "height": 180})
    path = res["result"]["path"]

    img = Image.open(path).convert("RGB")
    # getcolors returns None when there are more distinct colors than maxcolors
    # (the healthy case); a blank frame collapses to 1-2 colors.
    colors = img.getcolors(maxcolors=320 * 180)
    assert colors is None or len(colors) > 16
    # And it must not be all-black.
    assert max(hi for _, hi in img.getextrema()) > 10
