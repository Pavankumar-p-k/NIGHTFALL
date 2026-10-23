# NightFall — Island World Build Plan

UE 5.8 Blueprint project. Goal: a big open-world island game with GTA5/RDR2-style
distance streaming (World Partition), built for low-end devices.

## Current world state
- **Island map:** `Content/Maps/Untitled.umap` — `Landscape_1` (4096 components,
  64x64, 63 quads each = 4032 quads/side) at user-set scale
  **396.83 / 396.83 / 429.69 = 16.0 x 16.0 km**, origin `(-201600, -201600, 0)`.
  Terrain spans x/y `-201600 .. 1398418`. **Do not change scale without asking.**
- **Sea level = Z 0** (verified: island edges/bed at -30..-127 m, centre peak +503 m).
- Lighting (DirectionalLight, SkyAtmosphere, SkyLight, ExponentialHeightFog,
  VolumetricCloud) repositioned to island centre `(598409, 598409)`.
- PCG `BP_PCG_RuntimeGroundCover_C_4` + material `MI_Landscape_Grassland_ORM` present;
  PCG moved onto the island.
- Water: `WaterZone_1`, `Landscape_WaterBrushManager_0`, `WaterBodyRiver_8`
  (moved to lowland `(214405, 598409, 4619)`), and **`WaterBodyOcean_0` spawned at
  Z 0** covering the whole island (bigger than needed, ~66 km wide).
- `PlayerStart_0` at `(278405, 705077, 3498)` (33 m above ground, inland lowland).
- **Config temporarily changed** (backups: `DefaultEngine.ini.bak`, `.bak2`):
  - `EditorStartupMap` / `GameDefaultMap` = `/Game/Maps/Untitled` (was `realmap`).
  - `r.Nanite=False` — Nanite landscape baking needs ~1 GB x 64 blocks and pushes the
    editor past the machine's 32 GB commit limit (crashes). **Restore to True when
    edits settle.**
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
- **Headless remote-exec etiquette:** never run >~16 ray-traces against the landscape in
  one command (621 traces reset the connection and took the editor down); do edits in
  small commands and `save_current_level()` at the end of each.
- `LevelEditorSubsystem` has no `get_loaded_level()`; use `save_current_level()`.
- Trace enum must be `unreal.TraceTypeQuery.ECC_VISIBILITY` (old name deprecated).

## History (high level)
- 2 km map built and user-approved. Island pack imported (user) into Untitled.umap.
- Auto material authored + assigned. Ocean was spawned at computed sea level
  (Z ~ -1,529,037; terrain range Z -1,675,624 .. -479,970).
- Map rolled back to landscape-only per user; lighting re-added.
- Scale iterated with user (132 km -> 121 km) then finally reset to the pack's intended
  **16 km** (396.83/396.83/429.69) and saved.
- Because the old 121 km coordinates were left behind, ALL actors were re-aligned onto
  the 16 km island and `WaterBodyOcean_0` was added at sea level Z 0.
