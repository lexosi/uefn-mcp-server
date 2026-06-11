# Testing

This project is editor automation: most behaviour ultimately depends on a
running Unreal/Fortnite editor. That makes naive "it passed" signals cheap and
misleading. The test strategy is therefore built around a single question —
*can this test actually fail for the reason it claims?* — and separates what is
verifiable without the editor from what is not.

## Layers

| Layer | Location | Needs the editor? | Run in CI? |
|-------|----------|-------------------|------------|
| Unit | `tests/test_log_selection.py`, `tests/test_transport.py` | No | Yes |
| Canaries (unit) | `tests/test_canaries.py` | No | Yes |
| Live integration (incl. live canaries) | `tests/test_integration_live.py` | Yes | No |

```bash
pip install -r requirements.txt -r requirements-dev.txt

pytest -m "not live"   # unit + unit canaries — what CI runs
pytest -m live         # live integration — requires a running UEFN listener
pytest                 # everything (live tests auto-skip if no listener)
```

### Unit layer — no editor required

The editor-side module (`uefn_listener.py`) imports `unreal`, a module that only
exists inside the editor's embedded Python. To test its logic on an ordinary
machine, `tests/conftest.py`:

1. Injects a stub `unreal` module into `sys.modules`, and
2. Sets `UEFN_LISTENER_NO_AUTOSTART=1`, so importing the module registers its
   command handlers **without** binding a socket or registering a tick callback.

The logic under test is reached by **dependency injection** rather than by
patching globals. For example, the log-selection function takes its inputs as
arguments:

```python
_find_editor_log(log_dir=tmp_path, exe_path="…/UnrealEditorFortnite-Win64-Shipping.exe")
```

so a test can construct a directory of fake log files and assert which one is
chosen, with no editor and no mocking of the filesystem.

The MCP transport (`mcp_server.py`) is tested the same way: `urllib`'s
`urlopen` is replaced with a small fake, and the success / UEFN-error / port-
discovery paths are asserted directly.

### Live integration — editor required

`tests/test_integration_live.py` talks to the real listener over HTTP. The
`live_listener` fixture probes ports 8765–8770 and **skips** the whole layer if
no listener answers, so the suite never reports a false failure on a machine
without the editor. These tests are excluded from CI (`-m "not live"`) because a
CI runner has no Fortnite editor. That exclusion is a property of the system
under test, not a missing piece of the suite.

## Canaries — negative controls against false positives

A test that cannot fail is worthless: it manufactures confidence without
evidence. Borrowing the control discipline from the lab, every non-trivial claim
in this suite is paired with a control that establishes the claim is real:

- **Positive control ("the trap is real").** Before asserting that a fix avoids
  a bug, a test demonstrates that the bug genuinely occurs under the naive
  implementation. If the trap stops reproducing, the downstream regression test
  has quietly lost its meaning and is flagged for review.
- **Negative control.** A known-bad input that *must* be rejected. If the suite
  stays green when fed something that should be caught, the detector — not the
  input — is broken.

These are deliberately separated from the assertions they protect, so a single
code change cannot turn both green by accident.

### Canaries currently in the suite

| Canary | Layer | What it proves | What turns it red |
|--------|-------|----------------|-------------------|
| `test_canary_the_trap_is_real` | unit | Positive control: the original log selector (newest `.log` by mtime) really does pick `UnrealRevisionControl.log`, the auth-spam file. | The failure mode stops reproducing — signal to revisit the regression test. |
| `test_canary_fix_avoids_the_revision_control_trap` | unit | The fix does **not** return the revision-control log even though it is the newest file. | Reverting the fix to newest-by-mtime. |
| `test_canary_filter_then_tail_trap` | unit | A tail-then-filter implementation drops a match that sits above the tail window (the original secondary bug); the real handler keeps it. | Re-introducing tail-before-filter ordering. |
| `test_canary_harness_can_actually_fail` | unit | Sanity: the runner evaluates assertions at all (`assert 1 == 2` must raise). | A misconfigured runner that does not execute assertions. |
| `test_canary_editor_log_is_not_auth_spam` | live | The log tool returns real editor output, not lines dominated (>50%) by `lore_transport::auth` revision-control spam. | The selector regressing to the wrong file at runtime. |
| `test_canary_unknown_command_is_rejected` | live | A bogus command returns `success: false` — it is not silently accepted. | An error path that swallows unknown commands. |
| `test_canary_screenshot_is_not_blank` | live | The viewport capture has real content: decoded with Pillow, it has >16 distinct colours and a non-trivial max channel value. | A "successful" capture that is actually a black/blank frame. |

The blank-frame canary is the clearest example of why this matters: a screenshot
tool can return a valid PNG, a 200 status, and a plausible file size while the
image is entirely black — the call "succeeded" but produced nothing. Asserting
image *content*, not just a return code, is the difference between a test and a
rubber stamp.

## What is deliberately not tested here

- **No mocked editor.** There is no fake `SceneCapture2D` or fake `unreal.*`
  scene API. Faking the editor's rendering would let the live tests pass without
  proving anything about the editor. Editor-bound behaviour is verified against
  a real editor and is honestly excluded from CI instead of simulated.
- **Coverage of the `unreal` surface is out of scope.** The value is in the
  selection/filtering/transport logic and in the controls above, not in
  exercising Epic's API.
