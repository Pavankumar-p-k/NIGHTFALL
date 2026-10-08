# NightFall — Open World Design Plan (Style Guide)

## Vision
Full open-world 3D game in UE 5.8, **1800s-era gothic style**, player character
(vampire) explores a large land of five villages, monsters, NPCs, story and
cutscenes. All assets free/open-source only. No paid services.

## Map Layout — One Open World, Five Biomes
| Region | Theme | Key Features |
|---|---|---|
| Mountain Village | Rocky peaks, cliffs | Mining paths, cable bridges, mountain hut village |
| Forest Village | Dense woods | Logging camp, animal trails, hidden shrine |
| Desert Village | Arid dunes, canyon | Oasis, caravan route, ruins |
| Snow Village | Frozen highlands | Frozen lake, hot springs, trapper cabins |
| Riverside Village | River valley | Waterfall, mills, ferry crossing, farms |

- Terrain: heightmap-based, biome zones connected by roads/paths
- Water: rivers flowing between regions, waterfall(s), ponds, lakes
- Caves: entrance + interior tunnels linking regions (hidden shortcuts)
- Paths/roads: connect all 5 villages through mountain passes and valleys

## World Details (1800s Style)
- Buildings: timber/stone 1800s architecture — houses, church, town hall, barns, mills
- Checkpoints: fast-travel posts (coach stations) between villages
- Sign boards: wooden direction signs at every crossroads
- Props: carts, barrels, lanterns, fences, wells, market stalls

## Life in the World
- NPCs: villagers with daily schedules (work, eat, sleep, flee at night)
- Animals: horses, cows, chickens, deer, wolves, birds
- Creatures/monsters: appear at night and in caves/forest depths
- Trains/travel: railway or stagecoach line crossing the map + ferry

## Story & Presentation
- Story: quest chain tied to the 5 villages (each village = one chapter)
- Cutscenes: Sequencer-driven, fixed camera angles, letterboxed
- Camera: cinematic angles for cutscenes; over-shoulder gameplay camera
- Effects: fog, torchlight, weather (snow/rain), blood/moon VFX, Lumen lighting

## Tech Stack
- UE 5.8, Lumen + Nanite, World Partition, MCP connector for AI-driven editing
- Free assets: Fab free-month packs, Quixel Megascans, Kenney, Sketchfab CC,
  OpenGameArt (license-checked per asset)
- Server-authoritative multiplayer foundation (existing plan)

## Build Order
1. Fix level save-to-disk bug (open issue)
2. Terrain: full heightmap with 5 biome regions + rivers
3. Roads, paths, caves, checkpoints, sign boards
4. Village 1 (mountain) prototype + character movement/animals
5. Buildings pass for all 5 villages (1800s assets)
6. NPCs with schedules + monsters/creature AI
7. Trains/coach travel + ferry systems
8. Story quests, cutscenes, camera work, effects/polish
