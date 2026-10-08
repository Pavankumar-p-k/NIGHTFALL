# MCP Bridges (Unreal Editor <-> AI Agents)

NightFall exposes the running editor to AI agents through two independent MCP bridges.

## 1. Official Epic MCP server (primary)

- Plugin: `ModelContextProtocol` + `AllToolsets` (enabled in `NightFall.uproject`).
- Endpoint after start: `http://127.0.0.1:8000/mcp` (HTTP, streamable JSON-RPC).
- Client config file: `.mcp.json` at the project root (generated with console
  `ModelContextProtocol.GenerateClientConfig ClaudeCode`).
- Start: console command `ModelContextProtocol.StartServer`
  (auto-start setting `bAutoStartServer=True` is present in
  `Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini`).
- Toolsets: 52 discoverable (`list_toolsets`), including programmatic Python
  execution and automation-test toolsets.
- Claude Code: `claude plugin install unreal-engine-skills-for-claude-code@claude-plugins-official`,
  then approve `unreal-mcp` in the project (`claude mcp list` must show `Connected`).

## 2. Custom minimal connector (`Tools/UnrealMCP`)

Small stdio MCP server for agents that only need three capabilities.

- Server: `Tools/UnrealMCP/unreal_mcp_server.py`
  (talks to the editor via UE Remote Execution; requires
  `bRemoteExecution=True`, already set in `Config/DefaultEngine.ini`).
- Tools:
  - `editor_status` - project, engine version, editor readiness
  - `run_python` - execute Python inside the editor, returns stdout
  - `viewport_screenshot` - capture the active viewport
- Self-test: `python Tools/UnrealMCP/mcp_selftest.py` (16 checks, no editor required).

## Verification status

- Official MCP: server start + JSON-RPC initialize + client config verified live;
  Claude Code connection verified (`claude mcp list` -> Connected).
- Custom connector: self-test 16/16 green; live `editor_status` / `run_python`
  verified against the running editor. `viewport_screenshot` output UNVERIFIED
  for the active session (viewport rendering issue, see debugging history).
