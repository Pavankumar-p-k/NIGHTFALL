# Testing

Nothing is "done" until it is verified by running it. Unverified claims must be marked `UNVERIFIED`.

## Levels of verification

1. **Compile** - target builds with zero errors (warnings triaged, not ignored).
2. **Launch** - UnrealEditor opens the project without fatal errors (check `Saved/Logs/`).
3. **Run** - feature exercised in PIE (Play In Editor), expected behaviour observed.
4. **Network** - exercised with 2+ instances (PIE multi-player, or dedicated server + client), authority confirmed.
5. **Adversarial** - negative case: invalid input, bad timing, or a client attempting an illegal action is rejected by the server.

## Standard verification matrix

| Feature | Compile | Launch | Run | Network | Adversarial |
|---|---|---|---|---|---|
| Engine/project setup | yes | yes | yes | - | - |
| Character movement | yes | yes | yes (automation) | - | - |
| Day/night cycle | yes | yes | yes (automation) | - | - |
| Game mode / defaults | yes | yes | yes (automation) | - | - |
| Combat | yes | - | yes | yes | yes |
| Inventory | yes | - | yes | yes | yes |
| World streaming | yes | - | yes | yes | - |

## How to run

```powershell
# Toolchain + project integrity
.\Tools\Validate-Environment.ps1

# Build
.\Tools\Build.ps1 -Target NightFallEditor
.\Tools\Build.ps1 -Target NightFall

# Headless smoke test: boots the editor, loads the project, quits. Exit code 0 = pass.
.\Tools\Validate-Environment.ps1 -EditorSmokeTest

# Automation tests (see the list below); exits when the queue drains.
& 'C:\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' `
  'C:\Users\peter\Desktop\NightFall\NightFall.uproject' `
  -ExecCmds='Automation RunTests NightFall' -TestExit='Automation Test Queue Empty' `
  -ReportExportPath='C:\Users\peter\Desktop\NightFall\Saved\Automation\NightFallTestReport' `
  -unattended -nop4 -nullrhi -stdout -log

# Game smoke: boots the game headless, loads the default map, possesses the pawn, exits.
& 'C:\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' `
  'C:\Users\peter\Desktop\NightFall\NightFall.uproject' `
  -game -nullrhi -TestExit='NightFall: player pawn possessed' -unattended -nop4 -stdout -log
```

## Test inventory (all passing as of Phase 1)

| Test | What it proves |
|---|---|
| `NightFall.Character.SprintChangesWalkSpeed` | sprint input changes `MaxWalkSpeed`, character settles on the floor |
| `NightFall.Character.ForwardInputMovesCharacter` | possessed character walks forward with velocity > 0 |
| `NightFall.Character.CrouchAppliesOnAuthority` | crouch input sets/clears `IsCrouched`, crouch speed < walk speed |
| `NightFall.GameMode.DefaultClasses` | game mode CDO points at `ANightFallCharacter` / `ANightFallGameState` |
| `NightFall.Time.DayPhaseDrivesSun` | world time advances phase; sun rotation/intensity track phase |

Test world notes (regression traps): the manual test world must call `NotifyBeginPlay()`, sub-tick with `GFrameCounter++` after each `World->Tick`, and possess spawned pawns with an `AAIController` — unpossessed characters never run movement physics.

## Network testing

- Prototype: PIE with **2 players** (editor toolbar Net Mode = Play As Client with 1 dedicated server, or Listen).
- Two-process test: run server target and client target simultaneously on this machine.
- Never report a networking feature as working based on single-instance PIE.

## Log locations

- Editor/game log: `Saved\Logs\NightFall.log`
- Validation script output: console + `Tools\validation-latest.txt` (written by the script)
- Build output: console (captured by `Tools\Build.ps1` into `Saved\BuildLogs\`)

## Regression rule

Any bug fixed must leave behind either an automation test under `Source/NightFall/Tests/` or a documented manual check in this file.
