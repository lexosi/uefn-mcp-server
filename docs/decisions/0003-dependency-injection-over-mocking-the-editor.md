# ADR-0003: Dependency injection + stub `unreal` over mocking the editor

- **Status:** Accepted
- **Date:** 2026-06-11

## Context

The editor-side module imports `unreal`, which only exists inside the editor.
Unit tests must run on CI, where no editor exists. Yet the logic worth testing —
which log file is the editor log, how `last_n`/`filter_str` combine, the HTTP
transport's success/error paths — is editor-independent.

The tempting shortcut is to mock the editor: a fake `unreal` with a fake
`SceneCapture2D`, fake scene queries, etc. That path is a trap here: faking the
editor's rendering and scene API lets tests pass without proving anything about
the editor. The expensive, failure-prone behaviour is exactly the part a mock
would paper over.

## Decision

Make the editor-independent logic reachable without an editor, and verify the
editor-bound logic against a real editor instead of a fake one.

- **Dependency injection.** The selection logic takes its inputs as arguments:
  `_find_editor_log(log_dir=..., exe_path=...)`. A test builds a directory of
  real temporary log files and asserts which one is chosen — no editor, no
  filesystem mock.
- **Import without side effects.** `conftest.py` injects a stub `unreal` module
  and sets `UEFN_LISTENER_NO_AUTOSTART=1`, so importing the listener registers
  its handlers without binding a socket or starting a tick callback.
- **Honest split.** Editor-bound behaviour (ping, screenshot, the live log) lives
  in a `live` layer that talks to a real listener and **skips** when none is
  reachable. CI runs `pytest -m "not live"`.

## Consequences

- **+** Pure logic is tested deterministically on CI across Python versions, with
  no brittle simulation of Epic's API.
- **+** The unit/live boundary is explicit and documented
  ([../TESTING.md](../TESTING.md)); nothing pretends a CI runner has an editor.
- **+** Enables the negative-control ("canary") tests, which need the real
  selection function, not a mock of it.
- **−** The stub `unreal` must be import-complete. A module-level annotation
  (`def _serialize_actor(actor: unreal.Actor)`) is evaluated at import on Python
  3.11/3.12 and broke the stub; Python 3.14 defers annotations and masked it
  locally. The CI matrix caught it; fixed with `from __future__ import
  annotations`.
- **−** Editor-bound behaviour is not unit-tested; it is verified live and
  excluded from CI by design.

## Alternatives considered

- **Mock the editor** (fake `unreal`/`SceneCapture2D`/scene API) — rejected: a
  passing test against a fake editor proves the fake, not the editor. Editor
  behaviour is verified against a real editor and honestly left out of CI.
- **No unit tests, only live tests** — rejected: it would leave the selection and
  transport logic — the parts most likely to regress — untested in CI.
