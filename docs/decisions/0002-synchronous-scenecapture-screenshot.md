# ADR-0002: Synchronous `SceneCapture2D` for viewport capture

- **Status:** Accepted
- **Date:** 2026-06-11

## Context

`get_viewport_screenshot` must return an image to the model within a single
command — that is the whole point of the visual feedback loop.

The stock API, `AutomationLibrary.take_high_res_screenshot`, is **asynchronous**:
the file is written a frame or more after the call, and the write depends on the
editor viewport actually redrawing. With the editor window unfocused or idle the
redraw does not happen and the file never appears. This was reproduced during
development: the call "succeeds" and returns an automation-task object, but no
PNG is written.

The command model compounds this: the listener processes one command per tick
and returns its response synchronously, and the main thread cannot spin-wait for
an asynchronous editor render without deadlocking the very render it is waiting
for.

## Decision

Capture off-screen, synchronously, within the command:

1. Read the current viewport camera (`UnrealEditorSubsystem`).
2. Spawn a temporary `SceneCapture2D` there; target an `RTF_RGBA8`
   render target (`RenderingLibrary.create_render_target2d`).
3. `capture_scene()` (renders immediately) → `export_render_target()` writes a
   PNG.
4. Destroy the temporary actor in a `finally` block.

Verified live against UEFN: one call, valid PNG header, real scene content.

## Consequences

- **+** Deterministic and single-call; no dependency on the editor redrawing or
  the window being focused.
- **+** Fits the existing per-tick command dispatch with no async machinery.
- **−** The result is a `SceneCapture`, not a pixel-exact copy of the editor
  viewport: no editor gizmos/overlays, and its own show flags / FOV. For "what
  does the camera see" this is acceptable, and arguably cleaner (no UI chrome).
- **−** `RTF_RGBA8` is required: a float render target exports a file that is not
  a valid PNG. (Found the hard way; locked in by the format argument.)
- **−** Spawns and destroys a transient actor per call.

## Alternatives considered

- **`take_high_res_screenshot` + poll for the file** — rejected: the async write
  stalls without a redraw, and delivering the image in one call would require a
  deferred-response mechanism the simple per-tick dispatch does not have; the
  main thread cannot block on the render.
- **`HighResShot` console command** — rejected: same asynchronous,
  redraw-dependent write.
