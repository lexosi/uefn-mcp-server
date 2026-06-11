# Proposed Tools — Roadmap

Candidate tools for the UEFN MCP server, prioritized by **value × feasibility**.
Every entry is gated against UEFN's real Python limits (see [UEFN limitations](#uefn-limitations)
below) — UEFN Python is editor-only, runs on the render thread, and blocks or
crashes on a surprising set of operations. We do not ship tools UEFN can't run.

Legend: ✅ verified live · ⚠️ feasible with care · ❌ blocked/crashes in UEFN.

---

## Shipped

| Tool | Status | Notes |
|------|--------|-------|
| `get_viewport_screenshot` | ✅ shipped (v0.4.0) | Off-screen `SceneCapture2D` → PNG → returned to the model. Synchronous, single-call. |

---

## Tier S — highest ROI

| Tool | Purpose | API | Status |
|------|---------|-----|--------|
| `scatter_props` | Scatter an asset N times over an area (random / poisson-disk). Kills hand-placing 200 props. | `EditorActorSubsystem.spawn_actor_from_object` in a `ScopedSlowTask` | ✅ |
| `batch_transform_actors` | Align / distribute / snap-to-grid / mirror / randomize on the current selection. | `get_selected_level_actors` + `set_actor_transform` | ✅ |
| `align_actors_to_ground` | Raycast-drop selected actors onto the surface below (fix floaters after a scatter). | `SystemLibrary.line_trace_single` | ✅ |

## Tier A — asset & material pipeline

| Tool | Purpose | API | Status |
|------|---------|-----|--------|
| `import_asset` | Import FBX / glTF / PNG from disk into the project (batch). | `AssetImportTask` + `AssetTools.import_asset_tasks` | ✅ ⚠️ validation may reject non-whitelisted content |
| `create_material_instance` | Create a Material Instance from a master material. | `AssetTools.create_asset` + `MaterialInstanceConstantFactoryNew` | ✅ |
| `set_material_param` | Set scalar / vector / texture params on a Material Instance. | `MaterialEditingLibrary.set_material_instance_*_parameter_value` | ✅ |
| `assign_material` | Assign a material / MI to a mesh actor's slots. | `StaticMeshComponent.set_material` | ✅ |
| `duplicate_actors_grid` | Duplicate a selected actor in a grid / line / circle pattern. | `spawn_actor_from_object` + transform math | ✅ |
| `organize_outliner` | Move / rename actors into folders by class or prefix; enforce naming. | `Actor.set_folder_path`, `set_actor_label` | ✅ |
| `set_static_mesh_collision` | Add simple box / sphere / convex collision to a static mesh. | `StaticMeshEditorSubsystem.add_simple_collisions` | ✅ (collision only — **not** LOD) |

## Tier B — audit, data, Verse

| Tool | Purpose | API | Status |
|------|---------|-----|--------|
| `level_health_audit` | Report orphaned assets, redirectors, oversized textures, actor / poly counts. | Asset Registry **metadata only** | ⚠️ never call `get_asset()` in bulk (crashes) |
| `validate_assets` | Run naming / collision / material validation rules on demand. | `EditorValidatorSubsystem` | ✅ |
| `datatable_csv_json` | Import / export a DataTable to CSV or JSON. | `DataTableFunctionLibrary.export_data_table_to_*` | ✅ |
| `generate_verse_device_stub` | Scaffold a `creative_device` Verse class with `@editable` fields + `OnBegin`. The supported workaround for the V2-device wall. | text generation into the project `_Verse` folder | ✅ no editor API risk |
| `pcg_generate` | Trigger a PCG component to (re)generate. | `PCGComponent.generate` | ⚠️ project-dependent |

---

## Not building (UEFN blocks or crashes)

| Tool | Reason |
|------|--------|
| `generate_lods` | `StaticMeshEditorSubsystem.set_lods*` → `EXCEPTION_ACCESS_VIOLATION`; the reduction plugin is not loaded in UEFN. |
| `set_v2_device_property` | V2 Creative devices (Timer, Score, Capture Area…) store config as Verse `@editable`, not UPROPERTYs. Both `get/set_editor_property` and `getattr` fail. Use `generate_verse_device_stub` instead. |
| `create_niagara_system` | Niagara systems are a "disallowed object type" at UEFN validation. |
| `play_in_editor` | UEFN has no PIE; Python runs on the render thread. The methods exist but fail. |
| `edit_blueprint_graph` | UEFN uses Verse, not user Blueprints. |

---

## UEFN limitations

Hard constraints every tool is designed around (sources: Epic's *Python Tools in UEFN*
docs, and the community-maintained UEFN_QUIRKS map):

- **Editor-only, render thread.** No `time.sleep`, no long loops without `ScopedSlowTask`, no play-in-editor.
- **One heavy op per call.** Chaining heavy operations in a single exec block floods the asset registry and crashes.
- **No bulk `get_asset()`.** Audit tools must use Asset Registry metadata; loading each asset during a scan crashes.
- **`/Game/` mount is invisible.** Walk the project's `Content/` from disk instead.
- **Verse-driven properties** must be read via `getattr` / `dir()` before `get_editor_property`.
- **Mutations** should be wrapped in `ScopedEditorTransaction` (undo) and report a `status` dict.

---

## Build conventions

1. Register a handler in `uefn_listener.py` with `@_register("name")`; add a thin tool in `mcp_server.py`.
2. Fetch editor subsystems **inside** the handler (`_actor_sub()`, `_unreal_editor_sub()`, `_level_editor_sub()`); prefer subsystems over the deprecated `EditorLevelLibrary`.
3. Return a JSON-serializable dict; clean up any temporary actors in a `finally` block.
4. Bump `PROTOCOL_VERSION` on a new tool.
