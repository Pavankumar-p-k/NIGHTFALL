import importlib.util
import json
import os
import socket
import sys
import threading
import time
import traceback

SERVER_NAME = "unreal-connector"
SERVER_VERSION = "1.0.0"
MARKER = "@@UNREAL_CONNECTOR_JSON@@"
MAX_TOOL_CHARS = 40000
EXEC_MODES = ("ExecuteFile", "ExecuteStatement", "EvaluateStatement")
REMOTE_RELATIVE = os.path.join(
    "Engine", "Plugins", "Experimental", "PythonScriptPlugin", "Content", "Python", "remote_execution.py"
)

EDITOR_HINT = (
    "No Unreal Editor node discovered. Make sure the Unreal Editor is running and remote execution "
    "is enabled: set bRemoteExecution=True under [/Script/PythonScriptPlugin.PythonScriptPluginSettings] "
    "in Config/DefaultEngine.ini, then restart the editor."
)

INSTRUCTIONS = (
    "Drive the live Unreal Editor. Tools: editor_status (discovery + live state), "
    "run_python (execute editor Python), viewport_screenshot (capture the viewport as PNG). "
    "Requires an editor running with bRemoteExecution=True in Config/DefaultEngine.ini. "
    "Every run_python script must be self-contained (no persistent REPL state between calls)."
)


class BridgeError(Exception):
    pass


def log(message):
    try:
        sys.stderr.write("[{0}] {1}\n".format(SERVER_NAME, message))
        sys.stderr.flush()
    except Exception:
        pass


def registry_engine_roots():
    try:
        import winreg
    except ImportError:
        return []
    roots = []
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Epic Games\Unreal Engine\Builds") as key:
            index = 0
            while True:
                try:
                    name, value, _kind = winreg.EnumValue(key, index)
                except OSError:
                    break
                index += 1
                if isinstance(value, str):
                    order = 0 if name == "5.8" else 1
                    roots.append((order, name, value))
    except OSError:
        return []
    roots.sort(key=lambda item: (item[0], item[1]))
    return [root for _order, _name, root in roots]


def remote_execution_candidates():
    candidates = []
    override = os.environ.get("UNREAL_REMOTE_EXECUTION_PY")
    if override:
        candidates.append(override)
    for var in ("UNREAL_ENGINE_ROOT", "UE_ROOT", "UNREAL_ENGINE_PATH"):
        root = os.environ.get(var)
        if root:
            candidates.append(os.path.join(root, REMOTE_RELATIVE))
    for root in registry_engine_roots():
        candidates.append(os.path.join(root, REMOTE_RELATIVE))
    candidates.append(os.path.join(r"C:\UE_5.8", REMOTE_RELATIVE))
    seen = set()
    unique = []
    for path in candidates:
        key = os.path.normcase(os.path.abspath(path))
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def find_remote_execution_path():
    for path in remote_execution_candidates():
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(
        "remote_execution.py not found. Searched:\n  " + "\n  ".join(remote_execution_candidates())
    )


def load_remote_execution(path):
    spec = importlib.util.spec_from_file_location("ue_remote_execution_client", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clamp_number(value, low, high, default):
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = float(default)
    return max(low, min(high, number))


def limit_text(text, limit=MAX_TOOL_CHARS):
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    head = int(limit * 0.7)
    tail = limit - head
    omitted = len(text) - head - tail
    return text[:head] + "\n... [truncated {0} chars] ...\n".format(omitted) + text[-tail:]


def render(template, **replacements):
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace("__{0}__".format(key), str(value))
    return rendered


def extract_marker(data):
    chunks = []
    for entry in data.get("output") or []:
        chunks.append(str(entry.get("output", "")))
    text = "".join(chunks)
    index = text.rfind(MARKER)
    if index < 0:
        return None
    payload = text[index + len(MARKER):].lstrip()
    try:
        value, _end = json.JSONDecoder().raw_decode(payload)
        return value
    except ValueError:
        return None


def run_result_text(data):
    parts = ["success: {0}".format(bool(data.get("success")))]
    result = data.get("result")
    if result:
        parts.append("result:\n{0}".format(result))
    output = data.get("output") or []
    if output:
        rendered = []
        for entry in output:
            rendered.append("[{0}] {1}".format(entry.get("type", "?"), str(entry.get("output", "")).rstrip("\n")))
        parts.append("output:\n{0}".format("\n".join(rendered)))
    return "\n".join(parts)


EDITOR_INFO_SCRIPT = """import json
import unreal

info = {}

def world_path(world):
    if world is None:
        return None
    try:
        return world.get_path_name()
    except Exception:
        try:
            return world.get_name()
        except Exception as exc:
            return "ERROR: " + repr(exc)

def capture(key, fn):
    try:
        info[key] = fn()
    except Exception as exc:
        info[key] = "ERROR: " + repr(exc)

subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
capture("editor_world", lambda: world_path(subsystem.get_editor_world()))
capture("game_world_pie", lambda: world_path(subsystem.get_game_world()))
capture("playing_in_editor", lambda: subsystem.get_game_world() is not None)
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
capture("actor_count", lambda: len(actor_subsystem.get_all_level_actors()))
capture("selected_actors", lambda: sorted(actor.get_name() for actor in actor_subsystem.get_selected_level_actors()))
print("__MARKER__" + json.dumps(info, sort_keys=True))"""

SCREENSHOT_TRIGGER_SCRIPT = """import json
import unreal

outcome = {"step": "automation_library"}
try:
    task = unreal.AutomationLibrary.take_high_res_screenshot(__WIDTH__, __HEIGHT__, r"__PATH__")
    outcome["returned"] = repr(task)
    outcome["task_valid"] = bool(task.is_valid_task()) if task is not None else False
except Exception as exc:
    outcome["error"] = repr(exc)
print("__MARKER__" + json.dumps(outcome, sort_keys=True))"""

HIGHRESSHOT_SCRIPT = """import json
import unreal

outcome = {"step": "highresshot"}
try:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    command = "HighResShot __WIDTH__x__HEIGHT__ filename=__PATH__"
    unreal.SystemLibrary.execute_console_command(world, command)
    outcome["command"] = command
except Exception as exc:
    outcome["error"] = repr(exc)
print("__MARKER__" + json.dumps(outcome, sort_keys=True))"""


class Bridge:
    def __init__(self):
        self._lock = threading.RLock()
        self._module = None
        self._rx = None
        self._connected_node = None

    def _ensure_started(self):
        if self._rx is not None:
            return self._rx
        path = find_remote_execution_path()
        if self._module is None:
            self._module = load_remote_execution(path)
            log("loaded remote execution client: " + path)
        rx = self._module.RemoteExecution()
        try:
            rx.start()
        except OSError as exc:
            raise BridgeError("failed to start UDP discovery on 239.0.0.1:6766: {0}".format(exc))
        self._rx = rx
        log("remote execution discovery started")
        return rx

    def _discover(self, wait):
        rx = self._ensure_started()
        deadline = time.time() + max(0.0, wait)
        while True:
            nodes = list(rx.remote_nodes)
            if nodes or time.time() >= deadline:
                return nodes
            time.sleep(0.1)

    def discover(self, wait=3.0):
        with self._lock:
            try:
                return self._discover(wait)
            except FileNotFoundError as exc:
                raise BridgeError(str(exc))

    @staticmethod
    def _describe_nodes(nodes):
        if not nodes:
            return "none"
        summary = []
        for node in nodes:
            summary.append(
                "{0} (project={1}, engine={2})".format(
                    node.get("node_id", "?"), node.get("project_name", "?"), node.get("engine_version", "?")
                )
            )
        return "; ".join(summary)

    @staticmethod
    def _pick_node(nodes, node_id):
        if node_id:
            for node in nodes:
                if node.get("node_id") == node_id:
                    return node
            raise BridgeError(
                "Editor node '{0}' not found. Discovered: {1}".format(node_id, Bridge._describe_nodes(nodes))
            )
        if not nodes:
            raise BridgeError(EDITOR_HINT)
        nightfall = [node for node in nodes if str(node.get("project_name", "")).lower() == "nightfall"]
        if nightfall:
            return nightfall[0]
        return nodes[0]

    def _reset_connection(self):
        if self._rx is not None:
            try:
                self._rx.close_command_connection()
            except Exception as exc:
                log("error while closing command connection: " + repr(exc))
        self._connected_node = None

    def _ensure_connected(self, node, timeout):
        if self._rx.has_command_connection() and self._connected_node == node.get("node_id"):
            channel = self._rx._command_connection._command_channel_socket
            if channel is not None:
                channel.settimeout(timeout)
                return
        self._reset_connection()
        self._rx.open_command_connection(node["node_id"])
        channel = self._rx._command_connection._command_channel_socket
        if channel is not None:
            channel.settimeout(timeout)
        self._connected_node = node.get("node_id")
        log("connected to node " + str(node.get("node_id")))

    def _execute(self, code, exec_mode, timeout, node_id, wait, allow_retry):
        try:
            nodes = self._discover(wait)
            node = self._pick_node(nodes, node_id)
        except FileNotFoundError as exc:
            raise BridgeError(str(exc))
        try:
            self._ensure_connected(node, timeout)
            return self._rx.run_command(code, unattended=True, exec_mode=exec_mode)
        except socket.timeout:
            self._reset_connection()
            raise BridgeError(
                "The editor did not respond within {0:.0f}s (it may be busy or compiling); "
                "the command connection was reset.".format(timeout)
            )
        except (OSError, RuntimeError) as exc:
            self._reset_connection()
            if allow_retry:
                log("command channel failed ({0}); retrying once with a fresh connection".format(exc))
                return self._execute(code, exec_mode, timeout, node_id, 4.0, False)
            raise BridgeError("command connection failed: {0}".format(exc))

    def run(self, code, exec_mode="ExecuteFile", timeout=45.0, node_id=None):
        with self._lock:
            wait = 6.0 if self._connected_node is None else 1.5
            return self._execute(code, exec_mode, timeout, node_id, wait, True)

    def shutdown(self):
        with self._lock:
            if self._rx is not None:
                try:
                    self._rx.stop()
                except Exception as exc:
                    log("error while stopping remote execution: " + repr(exc))
                self._rx = None
                self._connected_node = None


BRIDGE = Bridge()


def project_root():
    here = os.path.abspath(__file__)
    candidate = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    if os.path.isfile(os.path.join(candidate, "NightFall.uproject")):
        return candidate
    return None


def default_screenshot_path():
    root = project_root()
    base = os.path.join(root, "Saved", "ConnectorScreenshots") if root else os.path.join(os.getcwd(), "Saved", "ConnectorScreenshots")
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(base, "shot_{0}.png".format(stamp))


def file_signature(path):
    try:
        stat = os.stat(path)
    except OSError:
        return None
    return (stat.st_mtime_ns, stat.st_size)


def wait_for_file(path, before, timeout):
    time.sleep(0.8)
    deadline = time.time() + timeout
    previous = None
    while time.time() < deadline:
        signature = file_signature(path)
        if signature is not None and signature != before:
            if signature == previous:
                return signature
            previous = signature
        time.sleep(0.25)
    return previous


def tool_editor_status(arguments):
    wait = clamp_number(arguments.get("discover_timeout_seconds", 3.0), 0.5, 20.0, 3.0)
    try:
        nodes = BRIDGE.discover(wait)
    except BridgeError as exc:
        return str(exc), True
    lines = ["discovered {0} node(s)".format(len(nodes))]
    preferred = ("node_id", "project_name", "project_root", "engine_version", "engine_root", "user", "machine")
    for index, node in enumerate(nodes, 1):
        lines.append("node {0}:".format(index))
        shown = set()
        for key in preferred:
            if key in node:
                lines.append("  {0}: {1}".format(key, node[key]))
                shown.add(key)
        for key in sorted(node):
            if key not in shown:
                lines.append("  {0}: {1}".format(key, node[key]))
    if not nodes:
        lines.append(EDITOR_HINT)
        return "\n".join(lines), False
    if not arguments.get("include_editor_info", True):
        return "\n".join(lines), False
    try:
        data = BRIDGE.run(render(EDITOR_INFO_SCRIPT, MARKER=MARKER), timeout=20.0)
    except BridgeError as exc:
        lines.append("editor info failed: {0}".format(exc))
        return "\n".join(lines), True
    info = extract_marker(data)
    if info is None:
        lines.append("editor info failed:\n{0}".format(run_result_text(data)))
        return "\n".join(lines), True
    lines.append("editor info:")
    lines.append(json.dumps(info, indent=2, sort_keys=True))
    return "\n".join(lines), False


def tool_run_python(arguments):
    code = arguments.get("code")
    if not isinstance(code, str) or not code.strip():
        return "'code' must be a non-empty Python script string.", True
    exec_mode = arguments.get("exec_mode", "ExecuteFile")
    if exec_mode not in EXEC_MODES:
        return "'exec_mode' must be one of: {0}".format(", ".join(EXEC_MODES)), True
    timeout = clamp_number(arguments.get("timeout_seconds", 45.0), 1.0, 55.0, 45.0)
    node_id = arguments.get("node_id")
    if node_id is not None and not isinstance(node_id, str):
        return "'node_id' must be a string.", True
    try:
        data = BRIDGE.run(code, exec_mode=exec_mode, timeout=timeout, node_id=node_id)
    except BridgeError as exc:
        return str(exc), True
    text = run_result_text(data)
    return text, not bool(data.get("success"))


def tool_viewport_screenshot(arguments):
    width = clamp_number(arguments.get("width", 1280), 16, 8192, 1280)
    height = clamp_number(arguments.get("height", 720), 16, 8192, 720)
    width = int(width)
    height = int(height)
    timeout = clamp_number(arguments.get("timeout_seconds", 20.0), 3.0, 50.0, 20.0)
    requested = arguments.get("path")
    if requested is not None and not isinstance(requested, str):
        return "'path' must be a string.", True
    path = os.path.abspath(requested) if requested else default_screenshot_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except OSError as exc:
        return "cannot create screenshot directory: {0}".format(exc), True
    before = file_signature(path)
    attempts = []
    trigger = render(SCREENSHOT_TRIGGER_SCRIPT, WIDTH=width, HEIGHT=height, PATH=path, MARKER=MARKER)
    try:
        data = BRIDGE.run(trigger, timeout=25.0)
    except BridgeError as exc:
        return "screenshot trigger failed: {0}".format(exc), True
    attempts.append("AutomationLibrary.take_high_res_screenshot: {0}".format(run_result_text(data)))
    signature = wait_for_file(path, before, timeout)
    method = "unreal.AutomationLibrary.take_high_res_screenshot"
    if signature is None:
        fallback_path = path.replace("\\", "/")
        fallback = render(HIGHRESSHOT_SCRIPT, WIDTH=width, HEIGHT=height, PATH='"' + fallback_path + '"', MARKER=MARKER)
        try:
            data = BRIDGE.run(fallback, timeout=25.0)
        except BridgeError as exc:
            return "HighResShot fallback failed: {0}".format(exc), True
        attempts.append("HighResShot console command: {0}".format(run_result_text(data)))
        signature = wait_for_file(path, before, timeout)
        method = "HighResShot console command"
    if signature is None:
        return (
            "Screenshot was not created: {0}\nAttempts:\n{1}\n"
            "On D3D12 the editor viewport cannot be read back (silent empty read); launch the editor "
            "with -d3d11 for screenshots, or the viewport may be closed / the editor may run with -nullrhi.".format(
                path, "\n".join(attempts)
            ),
            True,
        )
    return (
        "Screenshot saved\npath: {0}\nsize: {1} bytes\nmethod: {2}\n"
        "Open the file with a file-reading tool to view the image.".format(path, signature[1], method),
        False,
    )


TOOL_HANDLERS = {
    "editor_status": tool_editor_status,
    "run_python": tool_run_python,
    "viewport_screenshot": tool_viewport_screenshot,
}

TOOLS = [
    {
        "name": "editor_status",
        "description": (
            "Discover Unreal Editor instances running on this machine and report their connection info, "
            "plus (optionally) live editor state: open level, Play-In-Editor status, actor count, selection. "
            "Discovery alone works whenever the editor runs with remote execution enabled."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "discover_timeout_seconds": {
                    "type": "number",
                    "description": "How long to wait for discovery replies (default 3).",
                    "default": 3,
                },
                "include_editor_info": {
                    "type": "boolean",
                    "description": "Query the editor for live state after discovery (default true).",
                    "default": True,
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "run_python",
        "description": (
            "Run a Python script inside the live Unreal Editor. Scripts are isolated: no state persists "
            "between calls, so each script must be self-contained and start with 'import unreal'. "
            "'result' holds the traceback when the script fails; 'output' holds print/log lines. "
            "Use it to spawn or edit actors, manipulate assets, start or stop Play-In-Editor, run console "
            "commands via unreal.SystemLibrary.execute_console_command, and drive editor subsystems. "
            "Keep scripts short: split long work into several calls (MCP calls time out around 60s)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python source to execute in the editor."},
                "exec_mode": {
                    "type": "string",
                    "enum": list(EXEC_MODES),
                    "description": "Execution mode (default ExecuteFile allows multi-statement scripts).",
                    "default": "ExecuteFile",
                },
                "timeout_seconds": {
                    "type": "number",
                    "description": "Give up if the editor does not respond within this many seconds (default 45, max 55).",
                    "default": 45,
                },
                "node_id": {"type": "string", "description": "Optional specific editor node id from editor_status."},
            },
            "required": ["code"],
            "additionalProperties": False,
        },
    },
    {
        "name": "viewport_screenshot",
        "description": (
            "Capture the active level viewport of the Unreal Editor as a PNG (game view, works with or "
            "without Play-In-Editor) and return its absolute path - open it with a file-reading tool to "
            "view it. Falls back to the HighResShot console command when the primary automation API is "
            "unavailable. When 'path' is omitted a unique file under Saved/ConnectorScreenshots is used."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "width": {"type": "integer", "description": "Capture width in pixels (default 1280).", "default": 1280},
                "height": {"type": "integer", "description": "Capture height in pixels (default 720).", "default": 720},
                "path": {"type": "string", "description": "Optional absolute output path for the PNG."},
                "timeout_seconds": {"type": "number", "description": "Max seconds to wait for the file (default 20).", "default": 20},
            },
            "additionalProperties": False,
        },
    },
]


def rpc_result(request_id, result):
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def rpc_error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def initialize_result(params):
    requested = params.get("protocolVersion")
    if not isinstance(requested, str) or not requested:
        requested = "2025-03-26"
    return {
        "protocolVersion": requested,
        "capabilities": {"tools": {"listChanged": False}},
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        "instructions": INSTRUCTIONS,
    }


def tools_call_response(request_id, params):
    name = params.get("name")
    arguments = params.get("arguments")
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        return rpc_error(request_id, -32602, "'arguments' must be an object")
    if name not in TOOL_HANDLERS:
        return rpc_error(request_id, -32602, "Unknown tool: {0}".format(name))
    try:
        text, is_error = TOOL_HANDLERS[name](arguments)
    except BridgeError as exc:
        text, is_error = str(exc), True
    except Exception as exc:
        log("tool '{0}' raised:\n{1}".format(name, traceback.format_exc()))
        text, is_error = "internal error: {0}".format(repr(exc)), True
    return rpc_result(
        request_id,
        {
            "content": [{"type": "text", "text": limit_text(text)}],
            "isError": bool(is_error),
        },
    )


def build_response(message):
    is_notification = "id" not in message
    request_id = message.get("id")
    method = message.get("method")
    if not isinstance(method, str):
        if is_notification:
            return None
        return rpc_error(request_id, -32600, "Invalid Request: missing method")
    if is_notification:
        return None
    if method == "initialize":
        params = message.get("params") or {}
        if not isinstance(params, dict):
            params = {}
        return rpc_result(request_id, initialize_result(params))
    if method == "ping":
        return rpc_result(request_id, {})
    if method == "tools/list":
        return rpc_result(request_id, {"tools": TOOLS})
    if method == "tools/call":
        params = message.get("params") or {}
        if not isinstance(params, dict):
            return rpc_error(request_id, -32602, "'params' must be an object")
        return tools_call_response(request_id, params)
    if method == "resources/list":
        return rpc_result(request_id, {"resources": []})
    if method == "resources/templates/list":
        return rpc_result(request_id, {"resourceTemplates": []})
    if method == "prompts/list":
        return rpc_result(request_id, {"prompts": []})
    return rpc_error(request_id, -32601, "Method not found: {0}".format(method))


def send_message(payload_bytes, mode):
    stream = sys.stdout.buffer
    if mode == "header":
        stream.write(b"Content-Length: " + str(len(payload_bytes)).encode("ascii") + b"\r\n\r\n" + payload_bytes)
    else:
        stream.write(payload_bytes + b"\n")
    stream.flush()


def read_input_messages():
    stream = sys.stdin.buffer
    while True:
        first = stream.readline()
        if not first:
            return
        stripped = first.strip()
        if not stripped:
            continue
        if stripped.lower().startswith(b"content-length:"):
            try:
                length = int(stripped.split(b":", 1)[1].strip())
            except ValueError:
                send_message(
                    json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}).encode("utf-8"),
                    "line",
                )
                continue
            while True:
                header = stream.readline()
                if not header or header.strip() == b"":
                    break
            body = b""
            remaining = length
            while remaining > 0:
                chunk = stream.read(remaining)
                if not chunk:
                    return
                body += chunk
                remaining -= len(chunk)
            yield body, "header"
        else:
            yield stripped, "line"


def main():
    log("starting (python {0})".format(sys.version.split()[0]))
    try:
        log("remote execution client: " + find_remote_execution_path())
    except FileNotFoundError as exc:
        log(str(exc))
    try:
        for payload, mode in read_input_messages():
            try:
                message = json.loads(payload)
            except ValueError:
                response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
                send_message(json.dumps(response).encode("utf-8"), mode)
                continue
            try:
                response = build_response(message)
            except Exception as exc:
                log("unhandled error:\n" + traceback.format_exc())
                response = rpc_error(message.get("id"), -32603, "Internal error: {0}".format(repr(exc)))
            if response is not None:
                send_message(json.dumps(response, ensure_ascii=False).encode("utf-8"), mode)
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        pass
    finally:
        log("stdin closed; shutting down")
        BRIDGE.shutdown()


if __name__ == "__main__":
    main()
