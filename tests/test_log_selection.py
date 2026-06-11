"""Unit tests for editor-log selection and filtering (no editor required)."""

import os

import pytest

# A representative UEFN executable path; the app prefix is the first '-' token.
EXE = r"C:/Epic/UnrealEditorFortnite-Win64-Shipping.exe"


def _touch(path: str, mtime: float, content: str = "x\n") -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    os.utime(path, (mtime, mtime))


def test_selects_editor_log_over_newer_noise(tmp_path, listener_module):
    d = str(tmp_path)
    _touch(os.path.join(d, "UnrealEditorFortnite.log"), 1000)
    _touch(os.path.join(d, "UnrealRevisionControl.log"), 2000)  # newer noise
    _touch(os.path.join(d, "cef3.log"), 3000)                   # newest noise
    got = listener_module._find_editor_log(log_dir=d, exe_path=EXE)
    assert os.path.basename(got) == "UnrealEditorFortnite.log"


def test_excludes_backup_rotations(tmp_path, listener_module):
    d = str(tmp_path)
    _touch(os.path.join(d, "UnrealEditorFortnite-backup-2026.06.10.log"), 9000)  # newer, excluded
    _touch(os.path.join(d, "UnrealEditorFortnite.log"), 1000)
    got = listener_module._find_editor_log(log_dir=d, exe_path=EXE)
    assert os.path.basename(got) == "UnrealEditorFortnite.log"


def test_fallback_to_newest_when_no_prefix_match(tmp_path, listener_module):
    d = str(tmp_path)
    _touch(os.path.join(d, "Older.log"), 1000)
    _touch(os.path.join(d, "Newer.log"), 2000)
    got = listener_module._find_editor_log(log_dir=d, exe_path=EXE)
    assert os.path.basename(got) == "Newer.log"


def test_missing_dir_returns_none(tmp_path, listener_module):
    got = listener_module._find_editor_log(log_dir=str(tmp_path / "does_not_exist"), exe_path=EXE)
    assert got is None


def test_empty_dir_returns_none(tmp_path, listener_module):
    got = listener_module._find_editor_log(log_dir=str(tmp_path), exe_path=EXE)
    assert got is None


def test_filter_is_applied_before_tail(tmp_path, listener_module):
    """last_n must count *matching* lines. The match is near the top of the
    file, so a tail-then-filter implementation would return nothing."""
    p = tmp_path / "editor.log"
    lines = [f"line {i}\n" for i in range(100)]
    lines[3] = "this is the NEEDLE line\n"
    p.write_text("".join(lines), encoding="utf-8")

    res = listener_module._cmd_get_editor_log(last_n=5, filter_str="NEEDLE", log_file=str(p))
    assert res["count"] == 1
    assert any("NEEDLE" in line for line in res["lines"])


def test_filter_is_case_insensitive(tmp_path, listener_module):
    p = tmp_path / "editor.log"
    p.write_text("LogVerse: Error something\nLogTemp: ok\n", encoding="utf-8")
    res = listener_module._cmd_get_editor_log(last_n=50, filter_str="error", log_file=str(p))
    assert res["count"] == 1
    assert "Error" in res["lines"][0]


def test_explicit_log_file_overrides_autodetection(tmp_path, listener_module):
    p = tmp_path / "custom.log"
    p.write_text("only line\n", encoding="utf-8")
    res = listener_module._cmd_get_editor_log(last_n=10, log_file=str(p))
    assert res["file"] == str(p)
    assert res["lines"] == ["only line"]
