# NightFall — Island World Build Plan

UE 5.8 Blueprint project. Goal: a big open-world island game with GTA5/RDR2-style
distance streaming (World Partition), built for low-end devices.

## Current world state
- **Island map:** `Content/Maps/Untitled.umap` — `Landscape_0` (4096 components,
  64x64, 63 quads each = 4032 quads/side) at user-set scale
  **396.83 / 396.83 / 429.69 = 16.0 x 16.0 km**, **centred on world origin**
  `(-800009, -800009, 0)` (was `-201600`). Terrain spans x/y `-800009 .. 800009`.
  Actor property `enable_nanite=False` (was True — caused OOM).
  **Do not change scale without asking.**
- **Sea level = Z 0** (verified: island edges/bed at -30..-127 m, centre peak +503 m).
  `WaterBodyOcean_0` at Z 0 with `affects_landscape=False` (carving disabled — was
  flattening the whole island; **never re-enable**).
- **62 `WaterBodyRiver` actors** placed from `rivers_splines.json`, aligned to the
  re-centred island (`DX=DY=-598409`), depths 200 cm, `affects_landscape=False`.
  **All 1189 spline points' Z re-set to *traced actual terrain* + 200 cm** (see
  `Saved/island_pack/terrain_actual.csv`) — the original heightmap fit had ±3 m
  error (worst +5.8 m) which buried water on steep slopes: 132/1189 points (11%)
  were underground, worst rivers 13/14/0. Now 0 buried by construction.
- **WaterZone** `WaterZone_1` centred on island **(0,0,0)** (was off-centre at the
  old 598409 centre = 6 km error), `zone_extent` 6048000 -> **1600000**
  (actor bounds ±48 km, verified covers the island).
- **Real water flow = Shallow Water (WaterAdvanced plugin, already enabled).**
  6 x `AShallowWaterRiver` actors (`ShallowWaterRiver_1..6`), each listing a
  geographically-close cluster of river water bodies in `SourceRiverWaterBodies`
  (k-means over river midpoints; a sim grid covers its sources' bounding box, so
  distant rivers must NOT share one). All set to `RenderState=LIVE_SIM`,
  `ResolutionMaxAxis=256`. Total 62/62 rivers covered; each spawns a Niagara
  component running `Grid2D_SW_River`. Editor memory 14.3 GB for all 6.
  - Component properties auto-fill on Rebuild when null (no need to assign):
    Niagara system -> `/WaterAdvanced/Niagara/Systems/Grid2D_SW_River`, materials
    -> `SW_Water_Material_River` / `_Spline` / `_To_Ocean_Transition`.
  - Python notes: `RenderState` must be set with the enum
    `unreal.ShallowWaterRenderState.LIVE_SIM` (an int is rejected); the actor's
    **label** != `get_name()` (internal name stays `ShallowWaterRiver_N`).
  - Harmless log line: `Rebuild() - no valid sinks, using the first source as a sink`.
  - For the **low-end target**, switch these to `BAKED_SIM` once happy — `Bake()`
    is not a UFUNCTION so it must be done in the editor UI per actor (Details panel).
- **Water mesh quality cvars** in `[SystemSettings]`:
  `r.Water.WaterMesh.MaxDimensionInTiles=4096` (256 -> 1024 -> **4096**), `LODCountBias=1`,
  `TessFactorBias=1`. The log warning quotes a **non-existent** cvar
  (`MaxWidthInTiles`); the real one is `MaxDimensionInTiles`. Without it the
  quadtree was downscaled 0.12x (~240 m tiles) so 14 m rivers could not render
  at all — that was why water was invisible almost everywhere.
  - **Square-water bug:** at `MaxDimensionInTiles=1024` a tile was ~15.6 m while
    rivers average 16.5 m wide, so every river rendered as a chain of river-width
    squares ("squares on points"). Raised to **4096** (tile ~4x finer) in both the
  live console and `DefaultEngine.ini`. WaterZone `get_actor_bounds` extent is
  **4,800,000 cm half-extent (±48 km, 96 km across)**, so tile size is
  `2 * extent / MaxDimensionInTiles`.
- **Water surface raised +0.2 m:** all 1189 river spline points are now
  `traced terrain + 220 cm` (was +200). Verified: 1189/1189 points strictly above
  terrain, min clearance exactly 220 cm, 62/62 rivers, 0 errors, saved.
- **Landscape material — paint layers enabled** on `MI_Landscape_Grassland_ORM`
  (parent `M_LandscapeMaterial_HQ`, 778 expressions). Was rendering purely
  procedural slope/elevation masks — that is why underwater showed only sand/mud
  and the 9 weightmaps did nothing. Flipped ON and saved:
  `Use Landscape Paint Layers`, `Use Layer02`..`Use Layer06`, `Use Auto Beach Layer`.
  - **Original switch values:** `Saved\material_switches_before.json`.
  - **Full asset backup (made BEFORE the edit):**
    `Saved\backup_20261024_202755\` (202 files, 505 MB = whole `AzielArts_Material\`
    + `Untitled.umap`); latest path also in `Saved\LAST_BACKUP.txt`.
  - Weightmaps (ash, dry, forest, grass, gravel, jungle, mud, rock, sand) exist as
    assets under `/Game/island_layers/`; PNGs in `Saved\island_pack\weightmaps\`.
  - **Open:** the landscape must have those layers *allocated/painted* — enabling
    the switches alone will not populate them. Landscape paint-layer allocation is
    **UI-only** (`LandscapeInfo` is not exposed to Python in 5.8).
- Lighting (DirectionalLight, SkyAtmosphere, SkyLight, ExponentialHeightFog,
  VolumetricCloud) repositioned to island centre `(0, 0)`.
- PCG `BP_PCG_RuntimeGroundCover_C_4` + material `MI_Landscape_Grassland_ORM` moved
  to island centre `(0, 0, 50304)`.
- `PlayerStart_0` at `(-53835, 316387, 5668)` — on ground (terrain 5468).
- Water: `WaterZone_1` at (598409, 598409, 0) (oversized ~140 km, fine for open ocean).
- **Landscape edit layers:** `LandscapeEditLayer_0` (base — holds the original island
  heights), `LandscapeEditLayer_1` (water-brush carve layer that flattened the island).
  Layer 1 is **hidden**; **user should delete it in Landscape -> Edit Layers (UI-only)**.
- **Config temporarily changed** (backups: `DefaultEngine.ini.bak`, `.bak2`):
  - `EditorStartupMap` / `GameDefaultMap` = `/Game/Maps/Untitled` (was `realmap`).
  - `r.Nanite=True` (restored) + `[SystemSettings] landscape.RenderNanite=0`
    (landscape Nanite rebuilds need ~38 GB and crash the editor).
- Completed & untouched: `Content/Maps/nightfallisland.umap` (old 2 km map, user-approved).
- Intended final map name: `Content/Maps/island_16km.umap` (not created yet).

## Source assets
- Island pack: `Saved/island_pack/` — `island_heightmap_4033.r16` / `.png`,
  9 weightmaps `weightmaps/layer_*.png`, `rivers_splines.json` (62 rivers),
  `island_info.json` (waterfalls, volcano, sea stacks, ring island, islets).
- Second heightmap (archipelago, for later): `Downloads/showat_archipelago_16km_heightmap_2049.png`
  (2049x2049, 16-bit, full 0-65535 range).

## Build order (STRICT)
Finish Island #1 completely before moving to the sea, then Island #2.

1. [in progress] Island #1: complete coast + landscape look (material/weights, ocean/coast)
2. Island #1: creatures (wildlife, fish, birds) via proximity spawners
3. Island #1: buildings / structures / points of interest
4. Island #1: gameplay systems (story triggers, quests, fishing base)
5. Island #1: World Partition + performance pass for low-end devices
6. Sea: sculpt seabed between islands (ocean gameplay zone)
7. Sea: ocean creatures, monsters, fishing, story
8. Island #2 (archipelago): import + build out fully
9. Merge into final world + full validation + README

## Design notes
- The sea between islands is a **gameplay zone** (creatures, monsters, fishing, fights,
  story), not empty filler.
- Low-end strategy: one landscape if merged, World Partition distance streaming,
  pooled/distance-culled creatures, quality-scalable water.

## Engine / tooling facts (UE 5.8)
- Engine: `C:\UE_5.8`; project: `C:\Users\peter\Desktop\NightFall\NightFall.uproject`.
- Remote execution works (see `Config/DefaultEngine.ini`): connect with engine
  `remote_execution.py`, `RemoteExecutionConfig` (127.0.0.1, cmd endpoint 6776).
  `print` does not return — store JSON in a global `_DIAG` and read with MODE_EVAL_STATEMENT.
- `landscape_import_weightmap_from_render_target` only writes into ALREADY-ALLOCATED
  weightmaps; newly added layers must be painted once in-editor to allocate.
- **Do NOT call `render_weightmap` / `render_weightmaps` headless** — it hangs the editor.
- Adding/removing landscape paint layers is UI-only (AddTargetLayer is not a UFUNCTION).
- **Machine limit:** 16 GB RAM + 16 GB pagefile = 32 GB commit. A full GUI load of the
  island peaks ~8-9 GB and regularly dies with *"Ran out of memory ... paging file is too
  small"* on a background worker. Mitigations used: `r.Nanite=False`, startup map switched
  to Untitled (skip `realmap`), heavy edits run with `-nullrhi -nosplash -unattended`.
- **Headless remote-exec etiquette:** batching line traces at **50 per command works
  reliably** (a full 1189-point terrain trace finished in 93 s); the earlier failure
  was ~621 traces in ONE command, which reset the connection. Do edits in small
  commands and `save_current_level()` at the end of each.
- `run_command` results come back **single-quoted** (Python repr), so `json.loads`
  on the raw string throws — strip quotes via `ast.literal_eval` first.
- `LevelEditorSubsystem` has no `get_loaded_level()`; use `save_current_level()`.
- Trace enum must be `unreal.TraceTypeQuery.ECC_VISIBILITY` (old name deprecated).
- **Water bodies placed via Python must have `affects_landscape=False`** on the water
  body component, else the water brush flattens the terrain on the next update.
  Property is `affects_landscape` (`b_affects_landscape` fails). Recover by hiding
  the water-carve edit layer: `Landscape.get_edit_layers_bp()` /
  `ly.set_editor_property("visible", False)` + `Landscape.force_layers_full_update()`.
- Landscape edit layers and paint layers are UI-only to delete; Python can only
  list/hide edit layers (`get_edit_layers_bp`, `get_edit_layer_by_name_bp`) and
  import heightmaps from a render target (`landscape_import_heightmap_from_render_target`).
- Remote-exec Python clients leak ~0.6 GB each; `Stop-Process -Name python` between
  batches. Editor holds ~17 GB after the full island is loaded.

## History (high level)
- 2 km map built and user-approved. Island pack imported (user) into Untitled.umap.
- Auto material authored + assigned. Ocean was spawned at computed sea level
  (Z ~ -1,529,037; terrain range Z -1,675,624 .. -479,970).
- Map rolled back to landscape-only per user; lighting re-added.
- Scale iterated with user (132 km -> 121 km) then finally reset to the pack's intended
  **16 km** (396.83/396.83/429.69) and saved.
- Landscape re-imported/recreated by user as `Landscape_0` centred on origin.
  Water brush carved the terrain flat (all traces hit z = -2907); recovered by
  disabling ocean carving, hiding the water-carve edit layer (mountains restored,
  centre +503 m), and re-aligning all 62 rivers to the re-centred island.
- **Lesson:** always set `affects_landscape=False` on Python-spawned water bodies.
