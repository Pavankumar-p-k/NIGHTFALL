# Roadmap

Ordered milestones. A milestone is done only when its verification step in `TESTING.md` passes.

## Phase 0 - Setup foundation (done)

- Environment audit (hardware, toolchain, engine, disk).
- Engine moved from USB `F:\UE_5.8` to internal NVMe `C:\UE_5.8`, byte-verified, re-registered, backup retained.
- Project scaffold: `.uproject`, targets, module, config, git, LFS, docs, validation scripts.
- **Gate:** editor target compiles, validation script passes, project opens in UnrealEditor.

## Phase 1 - Vertical slice: movement and local world (verified, one gate item open)

- Third-person character: locomotion, sprint, jump, crouch, camera (EnhancedInput).
- Player controller + game mode + game state skeleton.
- One test level: flat ground, lighting, a few collision props, spawn point (`/Game/Maps/TestArena`, editor startup and game default map).
- Day/night cycle (server clock) with visual sun/moon only.
- **Verified:** all 5 automation tests pass headless (`NightFall.Character.*`, `NightFall.GameMode.DefaultClasses`, `NightFall.Time.DayPhaseDrivesSun`); game smoke run loads TestArena and possesses the player pawn (exit 0); validation script 15/15.
- **UNVERIFIED:** interactive solo run at 60 fps on the RTX 4050 (needs a manual in-editor session).

## Phase 2 - Networked foundation (current)

- Listen server + client connection, join/leave, late join.
- Replicated movement and transform for player characters (2-4 clients).
- Server-authoritative spawn flow, PlayerState basics.
- Dedicated server target status resolved (see `BUILD.md`) - if the installed build cannot package a server, PIE "Dedicated Server" net mode is the interim verification path.
- **Gate:** two clients on one machine move and see each other with server-side authority.

## Phase 3 - Combat core

- Damage system (server validated), health, death/respawn.
- One melee weapon: swing, hit detection on server, cooldown, damage data asset.
- Hit feedback (audio + UI), kill feed.
- **Gate:** attacker damage is applied only through server validation; a modified client cannot apply damage.

## Phase 4 - Inventory and items

- Server-side inventory container, add/remove/transfer with validation.
- Item data table (id, name, icon, stack, category).
- Pick up / drop interactables, basic loot spawn.
- **Gate:** inventory state is identical on all clients after every operation.

## Phase 5 - World and travel

- World partition setup, streaming, first two villages as streamed cells.
- Travel between regions, persistence of player position.
- Horses: spawn, mount, ride, network sync.
- **Gate:** streaming works without hitching > 100 ms; horse stays in sync for a remote observer.

## Phase 6 - Factions and roles

- Four playable roles (Vampire, Hunter, Priest, Werewolf) with distinct starter kits.
- Faction hostility rules, reputation basics.
- **Gate:** role selection persists, roles cannot access each other's abilities.

## Later

- Quests, economy, second-hand market, crafting with one source of truth.
- Weather as a systemic world effect.
- AI NPCs, advanced AI behaviours.
- Open-world scale test with 20-30 players.

Each milestone is committed incrementally; nothing is marked done without the stated gate.
