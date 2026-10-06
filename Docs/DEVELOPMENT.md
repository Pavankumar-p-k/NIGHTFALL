# Development

## Toolchain locations

| Tool | Path |
|---|---|
| Engine | `C:\UE_5.8` |
| Editor | `C:\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe` |
| Commandlet | `C:\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe` |
| Build script | `C:\UE_5.8\Engine\Build\BatchFiles\Build.bat` |
| Automation (UAT) | `C:\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat` |
| Project | `C:\Users\peter\Desktop\NightFall\NightFall.uproject` |
| MSVC | `C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.50.35717\bin\Hostx64\x64\cl.exe` |
| Windows SDK | `10.0.26100.0` |

## Day-to-day loop

```powershell
# 1. Make the change in Source/ or Content/
# 2. Build (incremental)
.\Tools\Build.ps1 -Target NightFallEditor

# 3. Open editor and exercise the feature
& 'C:\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' 'C:\Users\peter\Desktop\NightFall\NightFall.uproject'

# 4. Commit the verified state
git add -A; git commit -m "<what changed and how it was verified>"
```

## Compiling from the command line directly

```powershell
& 'C:\UE_5.8\Engine\Build\BatchFiles\Build.bat' NightFallEditor Win64 Development `
  -Project='C:\Users\peter\Desktop\NightFall\NightFall.uproject' -WaitMutex -FromMsBuild
```

Live coding (`Ctrl+Alt+F11` in editor) is fine for iterating, but always run a full build before committing.

## Debugging

- Attach VS to `UnrealEditor.exe` (Debug → Attach to Process), or launch from VS with the `.uproject` as command argument with `UnrealEditor` as target.
- `UE_LOG(LogTemp, Warning, TEXT("..."))` for temporary traces; introduce a project log category in `Core/` once logging becomes systematic (not yet needed).
- Crashes write callstacks to `Saved\Logs\`.

## Python (editor scripting)

Engine-bundled Python is at `C:\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin`. System Python 3.11.9 is available for tooling scripts. Do not add paid/cloud tooling.

Remote execution is enabled in `Config\DefaultEngine.ini` (`[/Script/PythonScriptPlugin.PythonScriptPluginSettings] bRemoteExecution=True`), which the MCP connector in `Tools\UnrealMCP\` uses to drive a live editor (takes effect on editor launch).

## Performance notes for this machine

- RTX 4050 laptop GPU, 16 GB RAM, NVMe SSD. Keep DerivedDataCache on `C:` (default, already on SSD).
- Prefer PIE testing at `Scalability` defaults; capture `stat unit` / `stat gpu` when optimising.

## Current known gaps

- Interactive solo run at 60 fps on the test map: `UNVERIFIED` (Phase 1 gate item).
- Server target packaging status: see `BUILD.md` (installed-build limitation).
