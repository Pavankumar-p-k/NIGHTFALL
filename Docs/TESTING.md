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
| Character movement | yes | - | yes | yes | - |
| Combat | yes | - | yes | yes | yes |
| Inventory | yes | - | yes | yes | yes |
| World streaming | yes | - | yes | yes | - |

## How to run

```powershell
# Toolchain + project integrity
.\Tools\Validate-Environment.ps1

# Build
.\Tools\Build.ps1 -Target NightFallEditor

# Headless smoke test: boots the editor, loads the project, quits. Exit code 0 = pass.
.\Tools\Validate-Environment.ps1 -EditorSmokeTest

# Automation tests (once Tests/ contains any)
& 'C:\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' `
  'C:\Users\peter\Desktop\NightFall\NightFall.uproject' `
  -ExecCmds="Automation RunTests NightFall; Quit" -unattended -nop4 -nullrhi -log
```

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
