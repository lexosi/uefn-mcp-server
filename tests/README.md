# Tests

Two layers, runnable independently.

```bash
pip install -r requirements-dev.txt

pytest                # unit + canary tests (live tests auto-skip if no listener)
pytest -m live        # live integration tests (needs the UEFN listener running)
pytest -m canary      # only the negative-control / false-positive guards
pytest -m "not live"  # everything that runs without an editor
```

## Layers

| File | Layer | Needs editor? |
|------|-------|---------------|
| `test_log_selection.py` | unit — editor-log selection + filtering | no |
| `test_transport.py` | unit — MCP server HTTP transport (mocked) | no |
| `test_canaries.py` | canaries — negative controls | no |
| `test_integration_live.py` | live — real listener: ping, log, screenshot | yes |

Unit tests import `uefn_listener` on a host with no editor: `conftest.py` injects
a stub `unreal` module and sets `UEFN_LISTENER_NO_AUTOSTART=1` so importing does
not bind a socket. Pure logic is exercised through dependency-injected arguments
(`_find_editor_log(log_dir=..., exe_path=...)`).

## Canaries — why

A green test suite is only trustworthy if it *can* go red for the right reason.
Canaries are negative controls that guard against false positives:

- **The trap is real** — proves the original bug (newest-`.log`-by-mtime picks
  `UnrealRevisionControl.log`) and that the fix avoids it. Reverting the fix
  turns the canary red.
- **Filter-then-tail trap** — proves a tail-then-filter implementation drops
  matches above the tail window.
- **Not-blank screenshot** — a capture can report success yet be a black frame;
  the canary asserts the image has real content.
- **Auth-spam log** — the log tool can succeed yet return revision-control spam.
- **Unknown command is rejected** — a harness that "passes everything" would
  miss a bogus command silently succeeding.
- **Harness can fail** — asserts the runner actually evaluates assertions.
