# ADR-0001: Two-process architecture — in-editor listener + external MCP server

- **Status:** Accepted (inherited from upstream `KirChuvakov/uefn-mcp-server`; recorded here for completeness)
- **Date:** 2026-06-11 (record), original design predates this fork

## Context

Driving an MCP client (e.g. Claude Code) against UEFN has two hard constraints:

1. Every `unreal.*` call must run on the editor's main thread.
2. The MCP SDK (`mcp`) is a pip package, and UEFN's embedded Python cannot
   install third-party packages.

A single process cannot satisfy both: the process that holds the `unreal` API is
the editor's embedded Python, which can't have `mcp`; the process that can have
`mcp` is an ordinary host Python, which has no `unreal`.

## Decision

Split into two cooperating processes:

- **Listener** (`uefn_listener.py`) runs *inside* the editor. Standard library
  only. An HTTP server on a background thread receives commands and dispatches
  the `unreal.*` work to the main thread via a tick callback.
- **MCP server** (`mcp_server.py`) runs as an ordinary host process with the
  `mcp` SDK, and forwards tool calls to the listener over localhost HTTP.

## Consequences

- **+** The listener has zero third-party dependencies and can't break on a
  package install.
- **+** Main-thread safety is structural: HTTP runs off-thread, `unreal.*` runs
  on the tick.
- **+** Each side restarts independently; the MCP server survives an editor
  reload and vice versa.
- **−** Two moving parts to start, and a localhost HTTP hop per call.
- **−** Server/listener versions can skew. Mitigated: `ping` returns the
  protocol version and the live command list.

## Alternatives considered

- **Single in-editor process exposing MCP directly** — rejected: `mcp` can't be
  installed in the embedded interpreter, and it would couple the transport to
  the editor's lifecycle (no independent restart).
- **C++ plugin instead of Python** — rejected by the upstream project: requires
  compilation and a per-UEFN-version rebuild; the Python path works across
  versions with no build step.
