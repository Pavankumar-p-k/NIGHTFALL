# NIGHT FALL

Original full-3D multiplayer gothic vampire game. Unreal Engine 5.8, C++, server-authoritative.

## Current status

- **Phase:** Setup foundation (environment audit, engine migration, project scaffold, build verification).
- **No gameplay code yet.** The repository currently contains only the project skeleton required to compile and verify the toolchain.
- See `Docs/ROADMAP.md` for what comes next.

## Requirements

| Item | Location |
|---|---|
| Unreal Engine 5.8.2 (installed build) | `C:\UE_5.8` |
| Visual Studio 2026 (v18), NativeDesktop workload | MSVC 14.50, Windows SDK 10.0.26100 |
| Git + Git LFS | system `PATH` |
| Python 3.11 | system `PATH` (engine bundles its own 3.11.8 for editor scripting) |

## Quick start

```powershell
# 1. Validate the environment (fast checks, no build)
.\Tools\Validate-Environment.ps1

# 2. Build the editor target
.\Tools\Build.ps1 -Target NightFallEditor

# 3. Open the project
& 'C:\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' 'C:\Users\peter\Desktop\NightFall\NightFall.uproject'
```

## Documentation

| File | Purpose |
|---|---|
| `Docs/DEVELOPMENT.md` | Day-to-day commands, iteration loop, debugging |
| `Docs/ARCHITECTURE.md` | Code/module layout, networking rules, folder taxonomy |
| `Docs/BUILD.md` | Build targets, toolchain, packaging, known limitations |
| `Docs/ROADMAP.md` | Milestone plan (vertical slice → prototypes) |
| `Docs/TESTING.md` | How features are verified, what counts as done |
| `Docs/DEVELOPMENT_RULES.md` | Non-negotiable project rules |

## Source control

Git repository with Git LFS for binary assets (`.uasset`, `.umap`, art, audio). Commit working states incrementally; never commit `Saved/`, `Intermediate/`, `Binaries/`, `DerivedDataCache/`.
