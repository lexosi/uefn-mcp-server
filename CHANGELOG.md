# Changelog

All notable changes to this fork are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [0.4.0]

### Added
- **`get_viewport_screenshot`** — captures the editor viewport off-screen via a
  temporary `SceneCapture2D` (RTF_RGBA8 render target → PNG) and returns the
  image to the model. Synchronous and single-call; gives an AI agent a visual
  feedback loop for editing the scene.
- `docs/proposed_tools.md` — feasibility-gated roadmap of candidate tools and
  the UEFN Python limits they are designed around.

## [0.3.0]

### Fixed
- **`get_editor_log` returned the wrong file.** It selected the newest `.log`
  by mtime, which in UEFN is `UnrealRevisionControl.log` (rewritten every few
  seconds with auth/transport spam) rather than the real Output Log
  (`UnrealEditorFortnite.log`). It now derives the app prefix from
  `sys.executable`, keeps only matching non-backup logs, and returns the newest.
- `get_editor_log` now filters **before** tailing, so `last_n` counts matching
  lines; added an optional `log_file` override.
- Listener hot-reload no longer spams `OSError [WinError 10038]`: the previous
  HTTP server is now `shutdown()` and joined before `server_close()`.

### Changed
- Migrated all deprecated `EditorLevelLibrary` calls to editor subsystems
  (`EditorActorSubsystem` / `UnrealEditorSubsystem` / `LevelEditorSubsystem`):
  `spawn_actor`, `focus_selected`, `get_project_info`, `get_level_info`,
  `save_current_level`, `get_viewport_camera`, `set_viewport_camera`.
  Prevents breakage when Epic removes the Editor Scripting Utilities Plugin.

## [0.2.0]

- Upstream baseline ([KirChuvakov/uefn-mcp-server](https://github.com/KirChuvakov/uefn-mcp-server)):
  status window, port discovery, metrics, and the initial 28 tools.
