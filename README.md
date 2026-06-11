# UEFN MCP Server

[![CI](https://github.com/lexosi/uefn-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/lexosi/uefn-mcp-server/actions/workflows/ci.yml)

> An MCP server that lets an AI agent drive the **Unreal Editor for Fortnite**
> from Claude Code (or any MCP client): inspect and edit actors and assets, run
> editor Python, and capture the viewport back to the model as an image.

<!-- Demo GIF — uncomment the line below once docs/media/loop.gif is recorded.
     Kept commented so the top of the README shows no broken image until the
     file exists. See the "Recording the demo GIF" section for what to capture.

![Visual feedback loop — the agent edits the scene and sees its own change](docs/media/loop.gif)
-->

## Highlights

- **Probe-first debugging.** The one real defect this fork fixes — `get_editor_log`
  returning auth-spam instead of the editor output — was root-caused by reading the
  actual UEFN log directory at runtime and confirming which file the heuristic
  picked, not by guessing. The fix is small and targeted; every assumption behind
  it was checked against a live editor first. ([before/after](CHANGELOG.md))
- **Negative-control testing.** The suite pairs each fix with a control that proves
  the bug was real, and guards "successful-but-wrong" outcomes (a screenshot that
  is a black frame; a log call that returns revision-control spam). A test that
  cannot fail is treated as no test. → **[docs/TESTING.md](docs/TESTING.md)**
- **Multimodal AI ↔ editor loop.** `get_viewport_screenshot` renders the editor
  camera off-screen and returns the image to the model, so an agent can *see* the
  scene it is editing and self-correct. It uses a synchronous `SceneCapture2D`
  path, engineered around the stock screenshot API whose write is deferred to a
  later frame and stalls when the editor window is not redrawing.

Everything above is **verified against a live editor**. Candidate tools that are
*not* built yet are kept separate, in a feasibility-gated roadmap
([docs/proposed_tools.md](docs/proposed_tools.md)) that documents what UEFN's
Python actually allows — and what it crashes on.

## Fork & credits

This is a fork of **[KirChuvakov/uefn-mcp-server](https://github.com/KirChuvakov/uefn-mcp-server)**.

**Upstream** built the foundation: the two-process architecture, the HTTP
listener with port discovery and a status window, and the initial 28 tools.

**This fork adds:**

| Area | Change |
|------|--------|
| Bug fix | Correct editor-log targeting (was returning the revision-control spam log) |
| Hardening | Migrated 8 deprecated `EditorLevelLibrary` calls to editor Subsystems; clean listener hot-reload |
| Feature | `get_viewport_screenshot` — synchronous viewport capture returned to the model |
| Tests | pytest suite (unit + live + canary negative controls) and CI |
| Docs | testing methodology, feasibility-gated roadmap, changelog |

See the [CHANGELOG](CHANGELOG.md) for the full, versioned history of this fork.

## What it is

```
Claude Code  <--stdio-->  MCP Server (mcp_server.py)  <--HTTP-->  Listener (uefn_listener.py, inside UEFN)
```

- **29 tools**: actors, assets, levels, viewport, **viewport screenshots**, project info, editor log, and arbitrary Python execution.
- **Zero C++ compilation** — pure Python, works across UEFN versions.
- **Main-thread safe** — all `unreal.*` calls dispatched via the editor tick callback.

UEFN's Python runs **editor-only** (not at game runtime); gameplay logic lives in
Verse. This server is for editor tooling: inspection, content pipelines, layout,
and debugging.

## Quick start

### 1. Enable Python in UEFN

**Project > Project Settings**, search **Python**, enable **Python Editor Script Plugin**.

### 2. Start the listener inside UEFN

**Tools > Execute Python Script** → select `uefn_listener.py`. A status window shows
listener/connection state, port, and live metrics. You can close it; the listener
keeps running.

### 3. Install and configure

```bash
pip install -r requirements.txt   # the `mcp` SDK
```

Create `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "uefn": {
      "command": "python",
      "args": ["C:/path/to/uefn-mcp-server/mcp_server.py"]
    }
  }
}
```

Restart Claude Code. You'll have 29 UEFN tools available.

### Try it

- *"List all actors in the level"*
- *"Spawn a cube at 100, 200, 300"*
- *"Take a screenshot of the viewport and tell me what's wrong with the layout"*

## Tools

| Category | Tools |
|----------|-------|
| **System** | `ping`, `execute_python`, `get_log`, `get_editor_log`, `shutdown` |
| **Actors** | `get_all_actors`, `get_selected_actors`, `spawn_actor`, `delete_actors`, `set_actor_transform`, `get_actor_properties`, `set_actor_properties`, `select_actors`, `focus_selected` |
| **Assets** | `list_assets`, `get_asset_info`, `get_selected_assets`, `rename_asset`, `delete_asset`, `duplicate_asset`, `does_asset_exist`, `save_asset`, `search_assets` |
| **Project / Level** | `get_project_info`, `save_current_level`, `get_level_info` |
| **Viewport** | `get_viewport_camera`, `set_viewport_camera`, `get_viewport_screenshot` |

The `execute_python` tool runs arbitrary Python inside the editor with full access
to the `unreal` module:

```python
# Pre-populated: unreal, actor_sub, asset_sub, level_sub, tk, get_tk_root
# Assign to `result` to return a value
actors = actor_sub.get_all_level_actors()
result = [a.get_actor_label() for a in actors]
```

> **Tkinter note:** create UI via `get_tk_root()` + `tk.Toplevel(root)`. Never call
> `tk.Tk()` — multiple instances crash the editor.

## Testing

```bash
pip install -r requirements.txt -r requirements-dev.txt

pytest -m "not live"   # unit + unit canaries (what CI runs)
pytest -m live         # live integration against a running UEFN listener
```

CI runs only the unit layer — the live layer needs the Fortnite editor, which a CI
runner does not have. That boundary is deliberate; the methodology and the list of
canary controls are in **[docs/TESTING.md](docs/TESTING.md)**.

## Architecture

Two independently running Python processes:

| Component | File | Runs in | Dependencies |
|-----------|------|---------|--------------|
| **Listener** | `uefn_listener.py` | UEFN editor process | stdlib only |
| **MCP Server** | `mcp_server.py` | External process | `mcp` SDK |

`unreal.*` calls must happen on the editor's main thread (tick callback); the MCP
SDK needs pip packages that can't be added to UEFN's embedded Python. Splitting the
two also lets each restart independently. See [docs/architecture.md](docs/architecture.md).

## Recording the demo GIF

`docs/media/loop.gif` is a screen recording (the viewport can't be captured
headless). Capture 3–5 seconds that show the *loop*, not just a screenshot:

1. The agent runs `get_viewport_screenshot` and the returned image appears in chat.
2. The agent makes one visible edit (e.g. moves or spawns an actor).
3. The agent screenshots again and the change is visible in the second image.

The point to convey: the model *sees its own change* and closes the loop.

## Documentation

| Document | Description |
|----------|-------------|
| [Testing](docs/TESTING.md) | Test layers and the canary / negative-control methodology |
| [Proposed tools (roadmap)](docs/proposed_tools.md) | Feasibility-gated candidates and UEFN's hard limits |
| [Architecture](docs/architecture.md) | How the two-component system works |
| [Tools reference](docs/tools_reference.md) | Per-tool parameters, examples, responses |
| [Troubleshooting](docs/troubleshooting.md) | Common issues |
| [UEFN Python capabilities](docs/uefn_python_capabilities.md) | Full API capability map |
| [Changelog](CHANGELOG.md) | Versioned history of this fork |

## Requirements

- UEFN with Python scripting enabled
- Python 3.10+ on the host
- `pip install -r requirements.txt`
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (or any MCP client)

## License

MIT (inherited from upstream). See [LICENSE](LICENSE).
