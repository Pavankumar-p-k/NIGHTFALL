# Build

Verified on this machine, 2026-10-06. Everything below marked **VERIFIED** was executed; anything else is marked `UNVERIFIED`.

## Toolchain (VERIFIED)

| Component | Detected value |
|---|---|
| Engine | UE 5.8.2 (CL 56702186, installed build) at `C:\UE_5.8` |
| UBT | bundled .NET SDK 10.0 win-x64, `UnrealBuildTool.dll` |
| MSVC | VS 18 Community - `v14.50.35717` (`Using Visual Studio 14.50.35726 toolchain`) |
| Windows SDK | `10.0.26100.0` |
| ISPC | 1.24.0 (LLVM 18.1.2) |
| Build executor | Unreal Build Accelerator local executor, 8 physical / 16 logical cores |
| Git | 2.53.0 + git-lfs 3.7.1 |

## Targets

| Target | Type | Result |
|---|---|---|
| `NightFallEditor` | Editor | **VERIFIED - SUCCEEDED** (96 s first build; `UnrealEditor-NightFall.dll`) |
| `NightFall` | Game | **VERIFIED - SUCCEEDED** (84 s; `Binaries\Win64\NightFall.exe`) |
| `NightFallServer` | Server | **VERIFIED - FAILED** (see below) |

Build commands (or use `Tools\Build.ps1 -Target <name>`):

```powershell
C:\UE_5.8\Engine\Build\BatchFiles\Build.bat NightFallEditor Win64 Development -Project=C:\Users\peter\Desktop\NightFall\NightFall.uproject -WaitMutex
```

## Dedicated server target is blocked on this engine install (VERIFIED)

Exact UBT output when building `NightFallServer` (exit code 6):

```
Creating makefile for NightFallServer (no existing makefile)
Server targets are not currently supported from this engine distribution.
Result: Failed (OtherCompilationError)
```

Cause: `C:\UE_5.8\Engine\Config\BaseEngine.ini` → `[InstalledPlatforms]` contains no `PlatformType="Server"` entry for Win64, and `UEBuildTarget.cs` throws exactly this message for `TargetType.Server` when the distribution has no server platform configured. This is a property of **launcher/installed builds**, not of our project. `Source\NightFallServer.Target.cs` is kept so the target works the moment a capable engine is available.

**Impact:** we cannot produce a standalone `NightFallServer.exe` with this engine install.

**Options (decision needed before Phase 2, no action taken yet):**

1. **PIE "Play as Dedicated Server"** - the editor hosts the server world in-process. Lets us develop and verify server-authoritative replication now. `UNVERIFIED` until tested (Phase 2).
2. **Listen server** game mode for the prototype - fully supported, no extra binary.
3. **Build UE 5.8 from source** to get server targets - needs roughly 250 GB free disk plus ~8 h of building. Current free space: C: ~85 GB, F: ~76 GB. Not feasible today; requires the user's decision.
4. **Linux dedicated server** from the installed build: `Loaded TargetPlatform 'WindowsServer'` appears in editor startup, but UBT still refuses `TargetType.Server`, so packaging a server executable is equally blocked. `UNVERIFIED`/likely blocked.

## Editor launch (VERIFIED)

```powershell
& 'C:\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' `
  'C:\Users\peter\Desktop\NightFall\NightFall.uproject' `
  -nullrhi -unattended -nop4 -nosplash -stdout -TestExit="Engine Initialization) Total time"
```

Result: exits 0 in 11 s warm (45 s on first run), engine initializes, project loads, 0 fatal errors, `Map check complete: 0 Error(s), 0 Warning(s)`.

Notes:

- `-ExecCmds=Quit` does **not** terminate the editor in this build: `Cmd: Quit` executes during init, but the process keeps running (observed: idle > 900 s until killed). Use `-TestExit="<phrase>"`, which `FEngineLoop::Tick` polls and turns into `FPlatformMisc::RequestExit` (`LaunchEngineLoop.cpp:5590`).
- First run of a new project does a full asset-registry scan (35 s) and Derived Data Cache maintenance (30 s). Budget 60 s for cold starts.
- The engine starts a background **Zen Storage** service (`zenserver.exe`, port 8558) and the Epic Online Services SDK pings its config endpoint on launch. These are part of the engine, free, and create no account. If unwanted, they can be disabled in `Engine/Plugins/Online/OnlineServices` - `UNVERIFIED`.
- `LogTemp: Error test: UE::UnifiedErrorTest::*` lines in the log are deliberate engine self-tests, not project errors.

## Packaging (cook + package)

Not attempted yet - no content to cook. `UNVERIFIED`.

## Validation script

```powershell
.\Tools\Validate-Environment.ps1                    # 14 checks, ~10 s
.\Tools\Validate-Environment.ps1 -EditorSmokeTest   # + headless editor boot/exit, ~30 s
```

Writes `Tools\validation-latest.txt`; exit code 0 = all passed.
