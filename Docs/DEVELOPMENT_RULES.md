# Development Rules

These rules are binding for all work on this project.

## Originality and legality

1. **No copying from copyrighted games.** Do not reproduce PUBG, Van Helsing, Dracula, Diablo, Castlevania or any other game's code, assets, characters, names, UI, levels or story. Build original systems from first principles.
2. **Free/open-source tools only.** Free tiers of tools are acceptable; paid assets/services require an explicit question and user approval first.
3. **Never introduce a paid service, subscription or cloud account without asking.** No paid services have been approved.
4. **Never sign up for cloud services or create accounts on the user's behalf.**
5. **Do not replace Unreal Engine.** UE 5.8 is the fixed technology choice.

## Engineering quality

6. **No placeholder architecture.** Every structure must be the real one that ships. If a decision risks creating a throw-away or badly-factored architecture, stop and report before proceeding.
7. **No fake implementations.** No stubs, `TODO` markers, dead buttons or features that "look" complete but are not. Honest state at all times.
8. **Server-authoritative** for combat, inventory, progression and world state. Clients send input and intent; the server validates, resolves and broadcasts.
9. **Single source of truth per system.** Shared data (resources, crafting, markets) is never duplicated across systems.
10. **Build future systems only when needed.** Do not write subsystems, abstractions or interfaces ahead of a demonstrated requirement.

## Process

11. **Inspect → explain → smallest correct version → build → test → fix → report.** Never skip verification.
12. **Never claim success without verification.** Unverified claims must be explicitly marked `UNVERIFIED`.
13. **Backups before destructive changes.** (Applied to the engine move: `F:\UE_5.8` retained as backup until verified.)
14. **Report exactly what works and what remains.** Include file paths and commands.
15. **Prefer incremental commits** over large unrelated commits.
