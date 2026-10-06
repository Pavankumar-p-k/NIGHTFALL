# Architecture

State: **scaffold only**. Nothing below the folder taxonomy is implemented yet; this document defines the target so code lands in the right place from the first commit.

## Principles

- Server-authoritative gameplay (combat, inventory, progression, world state).
- One runtime module, `NightFall`. Subsystems are separated by folder, not by module, until a subsystem genuinely needs its own compilation unit, dedicated server/client split, or third-party dependency. Premature module fragmentation creates circular dependency pressure for no benefit.
- Folder taxonomy is stable: new systems get a folder, not a rewrite.
- Data-driven wherever it reduces code: curves, data assets, DataTables for weapons, factions, crafting.

## Module layout

```
Source/
  NightFall.Target.cs            Game target (Win64)
  NightFallEditor.Target.cs      Editor target
  NightFallServer.Target.cs      Dedicated server target (see BUILD.md - see server limitations on installed build)
  NightFall/                     Single runtime module
    NightFall.Build.cs
    NightFall.cpp / NightFall.h  Primary game module
    Core/                        Base types, statics, logging, shared interfaces
    Game/                        Game mode, game state, match/world flow
    Characters/                  Character base classes shared by all factions
    Player/                      Player controller, camera, input binding (EnhancedInput)
    Multiplayer/                 Replication helpers, RPC contracts, replication graphs
    World/                       Persistent level streaming, world partition glue
    Villages/                    Village definitions, spawn/bounds, streaming cells
    NPC/                         Non-player characters (villagers, merchants, quest givers)
    AI/                          Behaviour trees / StateTree tasks, perception, navigation
    Combat/                      Damage system, hit validation, melee/ranged resolution
    Weapons/                     Weapon definitions, ammo, ballistics, weapon data assets
    Inventory/                   Containers, item definitions, add/remove/transfer rules
    Horses/                      Mount spawning, riding, sync
    Quests/                      Quest graph, triggers, rewards
    Factions/                    Rep, hostility, faction state
    Vampire/                     Vampire-specific abilities and rules
    Hunter/                      Hunter-specific abilities and rules
    Priest/                      Priest-specific abilities and rules
    Werewolf/                    Werewolf-specific abilities and rules
    Persistence/                 Save/load orchestration
    Save/                        Save game schemas
    UI/                          Widgets, HUD, menus
    Audio/                       Sound cue wiring
    Weather/                     Weather simulation (systemic, server-driven)
    Time/                        Day/night cycle (server-driven clock)
    Interaction/                 Interactables, doors, containers, shops
    Tools/                       Utility, editor-only helpers
    Tests/                       Automation tests
```

## Content layout

```
Content/
  Maps/           Levels (world partition, villages, test maps)
  Characters/     Characters, animation
  Environment/    Buildings, props, terrain, foliage
  Weapons/        Weapon meshes, data assets
  UI/             Widget blueprints, icons
  Audio/          Sound cues, ambience
  Placeholders/   Temporary test assets - must be replaced before feature sign-off
```

## Networking rules

- Ownership: server owns all authoritative state. Clients own at most input and local cosmetic state.
- Combat, loot, inventory, quest progression, economy: server validates every client request (range, cooldown, ownership, rate) before applying.
- Replication: replicated properties only where clients must read them; RPCs are requests from clients, commands from server.
- Anti-cheat posture for the prototype: reject invalid input early on the server; no trusted client.
- Day/night and weather: server clock is the only source of time; clients interpolate.

## Extension policy

A folder graduates to its own module only when one of these is true: (a) it must compile only for server or only for client, (b) it links a large third-party library, (c) it is reused by a second game target. Otherwise it stays a folder.
