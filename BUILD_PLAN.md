# NightFall — Island World Build Plan

UE 5.8 Blueprint project. Goal: a big open-world island game with GTA5/RDR2-style
distance streaming (World Partition), built for low-end devices.

## Current world state
- **Island map:** `Content/Maps/Untitled.umap` — contains ONLY `Landscape_0`
  (island heightmap imported by user at scale **3287** = ~132 km, scale must NOT change)
  + material `MI_Island_Auto` (auto height/slope, no paint layers required).
- Lighting added: DirectionalLight (Sun), SkyAtmosphere, SkyLight, ExponentialHeightFog,
  VolumetricCloud.
- Water / PCG / PlayerStart were removed during a clean-slate rollback.
- 9 paint layers (sand, rock, ash, gravel, mud, dry, jungle, forest, grass) still exist
  on the landscape but are empty/unused (deletion is UI-only in UE 5.8).
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

## History (high level)
- 2 km map built and user-approved. Island pack imported (user) into Untitled.umap.
- Auto material authored + assigned. Ocean was spawned at computed sea level
  (Z ~ -1,529,037; terrain range Z -1,675,624 .. -479,970).
- Map rolled back to landscape-only per user; lighting re-added.
