"""Canary tests — negative controls that must FAIL if the code regresses or
the test harness itself is broken.

A passing test suite is only meaningful if it *can* fail for the right reasons.
These canaries guard against false positives: a green suite that is green by
accident (a stubbed dependency, a tail-then-filter bug, a misconfigured runner).
Each canary pairs an assertion about the fix with a proof that the trap it
guards is real.
"""

import os

import pytest

EXE = r"C:/Epic/UnrealEditorFortnite-Win64-Shipping.exe"


def _touch(path: str, mtime: float) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("x\n")
    os.utime(path, (mtime, mtime))


def _naive_newest_by_mtime(log_dir: str):
    """The ORIGINAL buggy selection: newest *.log by mtime, no filtering."""
    logs = [f for f in os.listdir(log_dir) if f.endswith(".log")]
    logs.sort(key=lambda f: os.path.getmtime(os.path.join(log_dir, f)), reverse=True)
    return logs[0] if logs else None


@pytest.mark.canary
def test_canary_the_trap_is_real(tmp_path):
    """Control: prove the bug exists. The naive picker DOES choose the wrong,
    newest revision-control log. If this stops being true the regression canary
    below loses meaning and must be revisited."""
    d = str(tmp_path)
    _touch(os.path.join(d, "UnrealEditorFortnite.log"), 1000)
    _touch(os.path.join(d, "UnrealRevisionControl.log"), 2000)  # newer => trap
    assert _naive_newest_by_mtime(d) == "UnrealRevisionControl.log"


@pytest.mark.canary
def test_canary_fix_avoids_the_revision_control_trap(tmp_path, listener_module):
    """Regression canary: the fix must NOT return the revision-control log even
    though it is the newest file — the exact false positive of the original bug.
    Reverting the fix to newest-by-mtime makes this fail."""
    d = str(tmp_path)
    _touch(os.path.join(d, "UnrealEditorFortnite.log"), 1000)
    _touch(os.path.join(d, "UnrealRevisionControl.log"), 2000)
    got = os.path.basename(listener_module._find_editor_log(log_dir=d, exe_path=EXE))
    assert got != "UnrealRevisionControl.log"
    assert got == "UnrealEditorFortnite.log"


@pytest.mark.canary
def test_canary_filter_then_tail_trap(tmp_path, listener_module):
    """A tail-then-filter implementation returns nothing when the only match is
    above the tail window. Prove the trap (naive approach yields []) and that
    the real handler avoids it."""
    p = tmp_path / "editor.log"
    lines = [f"line {i}\n" for i in range(100)]
    lines[2] = "the MATCH is here\n"
    p.write_text("".join(lines), encoding="utf-8")

    # Naive: tail first (last 5), then filter -> empty.
    naive = [l for l in p.read_text(encoding="utf-8").splitlines()[-5:] if "MATCH" in l]
    assert naive == []

    res = listener_module._cmd_get_editor_log(last_n=5, filter_str="MATCH", log_file=str(p))
    assert res["count"] == 1


@pytest.mark.canary
def test_canary_harness_can_actually_fail():
    """Sanity: the runner evaluates assertions. A suite that cannot fail gives
    false confidence — unacceptable for safety-critical software."""
    with pytest.raises(AssertionError):
        assert 1 == 2
