"""Minimal MCP client for the local Unreal editor (http://127.0.0.1:8000/mcp).
Usage: python3 ue.py <python_file> [timeout_s]  -> runs the file's code via execute_python_code, prints output."""
import json
import os
import tempfile
import sys
import urllib.request

URL = "http://127.0.0.1:8000/mcp"
SESSION_FILE = os.path.join(tempfile.gettempdir(), "ue_mcp_session.txt")


def post(payload, session=None, timeout=60):
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if session:
        headers["Mcp-Session-Id"] = session
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")
        sid = r.headers.get("Mcp-Session-Id")
    if body.startswith("event:") or body.startswith("data:"):
        body = "\n".join(l[5:].strip() for l in body.splitlines() if l.startswith("data:"))
    return (json.loads(body) if body.strip() else None), sid


def session():
    try:
        return open(SESSION_FILE).read().strip()
    except OSError:
        pass
    res, sid = post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "local-client", "version": "1"}}})
    post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    open(SESSION_FILE, "w").write(sid or "")
    return sid


def call(code, timeout):
    sid = session()
    try:
        res, _ = post({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "execute_python_code", "arguments": {"code": code, "auto_save": "false"}}}, sid, timeout)
    except urllib.error.HTTPError:
        open(SESSION_FILE, "w").write("")
        import os
        os.remove(SESSION_FILE)
        sid = session()
        res, _ = post({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "execute_python_code", "arguments": {"code": code, "auto_save": "false"}}}, sid, timeout)
    if res and "error" in res and "Unknown session" in json.dumps(res["error"]):
        import os
        os.remove(SESSION_FILE)
        return call(code, timeout)
    for c in (res or {}).get("result", {}).get("content", []):
        if c.get("type") == "text":
            try:
                d = json.loads(c["text"])
                print(d.get("output", "") or "", d.get("error_message", "") or "")
            except ValueError:
                print(c["text"])
    if res and "error" in res:
        print("ERROR", res["error"])


if __name__ == "__main__":
    call(open(sys.argv[1]).read(), float(sys.argv[2]) if len(sys.argv) > 2 else 120)
