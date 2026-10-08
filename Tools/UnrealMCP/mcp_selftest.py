import json
import os
import queue
import subprocess
import sys
import threading
import time

SERVER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unreal_mcp_server.py")


def read_message(stream):
    first = stream.readline()
    if not first:
        return None
    stripped = first.strip()
    if not stripped:
        return read_message(stream)
    if stripped.lower().startswith(b"content-length:"):
        length = int(stripped.split(b":", 1)[1].strip())
        while True:
            header = stream.readline()
            if not header or header.strip() == b"":
                break
        body = stream.read(length)
        if not body:
            return None
        return json.loads(body)
    return json.loads(stripped)


class Client:
    def __init__(self):
        self.proc = subprocess.Popen(
            [sys.executable, SERVER],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.responses = queue.Queue()
        self.reader = threading.Thread(target=self._read_loop, daemon=True)
        self.reader.start()

    def _read_loop(self):
        while True:
            try:
                message = read_message(self.proc.stdout)
            except Exception:
                message = None
            if message is None:
                break
            self.responses.put(message)

    def send_line(self, obj):
        self.proc.stdin.write((json.dumps(obj) + "\n").encode("utf-8"))
        self.proc.stdin.flush()

    def send_header(self, obj):
        body = json.dumps(obj).encode("utf-8")
        self.proc.stdin.write(b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n\r\n" + body)
        self.proc.stdin.flush()

    def wait(self, request_id, timeout=30.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                message = self.responses.get(timeout=max(0.1, deadline - time.time()))
            except queue.Empty:
                return None
            if message.get("id") == request_id:
                return message
        return None

    def request(self, obj, timeout=30.0):
        self.send_line(obj)
        return self.wait(obj.get("id"), timeout)

    def stderr_text(self):
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        try:
            out, err = self.proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            out, err = self.proc.communicate()
        return err.decode("utf-8", "replace") if err else ""


FAILURES = []
CHECKS = [0]


def check(label, condition, detail=""):
    CHECKS[0] += 1
    if condition:
        print("PASS  {0}".format(label))
    else:
        print("FAIL  {0}  {1}".format(label, detail))
        FAILURES.append(label)


def main():
    client = Client()
    try:
        init = client.request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "selftest", "version": "0"}}})
        check("initialize returns a result", isinstance(init, dict) and "result" in init, repr(init))
        if init and "result" in init:
            check("initialize echoes protocolVersion", init["result"].get("protocolVersion") == "2025-06-18", repr(init))
            check("initialize advertises tools capability", init["result"].get("capabilities", {}).get("tools") is not None, repr(init))
            check("initialize serverInfo", init["result"].get("serverInfo", {}).get("name") == "unreal-connector", repr(init))

        client.send_line({"jsonrpc": "2.0", "method": "notifications/initialized"})
        pong = client.request({"jsonrpc": "2.0", "id": 2, "method": "ping"})
        check("ping returns empty result", isinstance(pong, dict) and pong.get("result") == {}, repr(pong))

        listed = client.request({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
        tools = listed.get("result", {}).get("tools", []) if isinstance(listed, dict) else []
        names = sorted(tool.get("name") for tool in tools)
        check("tools/list has 3 tools", names == ["editor_status", "run_python", "viewport_screenshot"], repr(names))
        schemas_ok = all(isinstance(tool.get("inputSchema"), dict) and tool["inputSchema"].get("type") == "object" for tool in tools)
        check("every tool has an object inputSchema", schemas_ok, repr(tools))

        status = client.request({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "editor_status", "arguments": {"discover_timeout_seconds": 1, "include_editor_info": False}}})
        status_result = status.get("result", {}) if isinstance(status, dict) else {}
        status_text = "".join(c.get("text", "") for c in status_result.get("content", []))
        check("editor_status returns text", "discovered" in status_text, repr(status_text)[:400])
        check("editor_status is not an error when no editor runs", status_result.get("isError") is False, repr(status_result)[:400])

        run = client.request({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "run_python", "arguments": {"code": "print(1)"}}})
        run_result = run.get("result", {}) if isinstance(run, dict) else {}
        run_text = "".join(c.get("text", "") for c in run_result.get("content", []))
        check(
            "run_python reports editor absence or succeeds",
            run_result.get("isError") is True and "No Unreal Editor node discovered" in run_text or "success: True" in run_text,
            repr(run_text)[:400],
        )

        missing = client.request({"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "run_python", "arguments": {}}})
        missing_result = missing.get("result", {}) if isinstance(missing, dict) else {}
        check("run_python without code is an error result", missing_result.get("isError") is True, repr(missing_result)[:300])

        unknown_tool = client.request({"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "nope", "arguments": {}}})
        check("unknown tool returns -32602", isinstance(unknown_tool, dict) and unknown_tool.get("error", {}).get("code") == -32602, repr(unknown_tool))

        unknown_method = client.request({"jsonrpc": "2.0", "id": 8, "method": "bogus/method"})
        check("unknown method returns -32601", isinstance(unknown_method, dict) and unknown_method.get("error", {}).get("code") == -32601, repr(unknown_method))

        resources = client.request({"jsonrpc": "2.0", "id": 9, "method": "resources/list"})
        check("resources/list returns empty list", isinstance(resources, dict) and resources.get("result", {}).get("resources") == [], repr(resources))

        client.send_header({"jsonrpc": "2.0", "id": 10, "method": "ping"})
        framed = client.wait(10)
        check("Content-Length framed request answered", isinstance(framed, dict) and framed.get("result") == {}, repr(framed))

        run_stderr = client.stderr_text()
        check("server stayed alive for the whole session", client.proc.returncode is not None and client.proc.returncode == 0, "exit={0}".format(client.proc.returncode))
    except Exception as exc:
        print("FAIL  selftest crashed: {0}".format(repr(exc)))
        FAILURES.append("crash")
        run_stderr = ""
        try:
            client.proc.kill()
        except Exception:
            pass
    print("")
    if FAILURES:
        print("{0}/{1} checks passed; FAILED: {2}".format(CHECKS[0] - len(FAILURES), CHECKS[0], ", ".join(FAILURES)))
        try:
            if run_stderr:
                print("--- server stderr ---\n" + run_stderr[-4000:])
        except Exception:
            pass
        sys.exit(1)
    print("{0}/{0} checks passed".format(CHECKS[0]))


if __name__ == "__main__":
    main()
